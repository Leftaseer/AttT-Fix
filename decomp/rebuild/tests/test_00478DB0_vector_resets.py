"""The seven array-reset routines at 0x478DB0, 0x4FBC60, 0x4FEE60, 0x507830, 0x51FDE0,
0x557260 and 0x557F50; allocation, element construction and both deletion paths are stubbed."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

NEW_ARRAY = 0x005E3B10
DELETE_ARRAY = 0x005E3EBA
EH_CTOR = 0x005E4197
SPECS = [
    (0x00478DB0, 0x0c, 0x00476070, 0x00478860),
    (0x004FBC60, 0x1ac, 0x004EC000, 0x00461CC0),
    (0x004FEE60, 0x78, 0x005203D0, 0x00520460),
    (0x00507830, 0xc8, 0x0051F040, 0x0051E940),
    (0x0051FDE0, 0x0c, 0x004FEC90, 0x004FECB0),
    (0x00557260, 0x0c, 0x00555E60, 0x00556D10),
    (0x00557F50, 0x4c, 0x00557A00, 0x00557E40),
]
saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, stub):
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    h.uc.ctl_remove_cache(target, target + 5)


def _load_arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _new_stub(h, log, result):
    return _stub(h, _load_arg(4, log) + b'\xB8' + _dword(result) + b'\xC3')


def _delete_stub(h, log):
    return _stub(h, _load_arg(4, log + 0x18) + b'\xC3')


def _ctor_stub(h, log):
    code = b''
    for i, offset in enumerate(range(4, 0x18, 4)):
        code += _load_arg(offset, log + 4 + 4 * i)
    return _stub(h, code + b'\xC2\x14\x00')


def _vector_dtor_stub(h, log):
    code = (b'\x89\x0D' + _dword(log + 0x1c) +
            _load_arg(4, log + 0x20) + b'\x8B\xC1\xC2\x04\x00')
    return _stub(h, code)


def _exercise(h, spec, state, raw, old, log, count, cookie, allocation_succeeds=True, expected_bytes=None):
    fn, element_size, ctor, dtor = spec

    def prepare():
        h.uc.mem_write(log, bytes(0x40))
        h.uc.mem_write(raw, _dword(0xA5A5A5A5))
        h.uc.mem_write(old, _dword(cookie))
        h.uc.mem_write(state, _dword(0) + _dword(old + 4) + _dword(9))

    prepare()
    diffs = h.compare(fn, args=[count], regs={UC_X86_REG_ECX: state}, ret=None)
    if diffs:
        return ['%08X: %s' % (fn, '; '.join(diffs))]
    prepare()
    result = h.call(fn, args=[count], regs={UC_X86_REG_ECX: state})
    if result['fault']:
        return ['%08X: %s' % (fn, result['fault'])]

    problems = []
    expected_new = count != 0 and allocation_succeeds
    expected_data = raw + 4 if expected_new else 0
    if _u32(h, state + 4) != expected_data or _u32(h, state + 8) != 0:
        problems.append('%08X: state is (%#x, %#x)' % (fn, _u32(h, state + 4), _u32(h, state + 8)))
    expected_delete = 0 if cookie else old
    if _u32(h, log + 0x18) != expected_delete:
        problems.append('%08X: delete[] got %#x' % (fn, _u32(h, log + 0x18)))
    expected_vector = old + 4 if cookie else 0
    if (_u32(h, log + 0x1c), _u32(h, log + 0x20)) != (expected_vector, 3 if cookie else 0):
        problems.append('%08X: vector dtor got (%#x, %#x)' %
                        (fn, _u32(h, log + 0x1c), _u32(h, log + 0x20)))
    if count:
        if expected_bytes is None:
            expected_bytes = count * element_size + 4
        if _u32(h, log) != expected_bytes:
            problems.append('%08X: new[] size is %#x' % (fn, _u32(h, log)))
    elif _u32(h, log):
        problems.append('%08X: new[] was called for zero elements' % fn)
    if expected_new:
        expected = (raw + 4, element_size, count, ctor, dtor)
        if tuple(_u32(h, log + 4 + 4 * i) for i in range(5)) != expected:
            problems.append('%08X: constructor log is %s' %
                            (fn, tuple(_u32(h, log + 4 + 4 * i) for i in range(5))))
        if _u32(h, raw) != count:
            problems.append('%08X: array cookie is %#x' % (fn, _u32(h, raw)))
    elif any(_u32(h, log + 4 + 4 * i) for i in range(5)):
        problems.append('%08X: element constructor was called' % fn)
    return problems


def _fixture(h, allocation_succeeds=True):
    log = h.alloc(0x40, bytes(0x40))
    state = h.alloc(0x10, bytes(0x10))
    raw = h.alloc(0x20, bytes(0x20))
    old = h.alloc(0x20, bytes(0x20))
    vector_dtor = _vector_dtor_stub(h, log)
    vtable = h.alloc(4, _dword(vector_dtor))
    h.uc.mem_write(old + 4, _dword(vtable))
    _hook(h, NEW_ARRAY, _new_stub(h, log, raw if allocation_succeeds else 0))
    _hook(h, DELETE_ARRAY, _delete_stub(h, log))
    _hook(h, EH_CTOR, _ctor_stub(h, log))
    return state, raw, old, log


def test_vector_resets_allocate_and_construct(h):
    heap0 = h.heap_ptr
    state, raw, old, log = _fixture(h)
    try:
        problems = []
        for spec in SPECS:
            problems += _exercise(h, spec, state, raw, old, log, 3, 1)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_vector_resets_plain_delete_and_zero_count(h):
    heap0 = h.heap_ptr
    state, raw, old, log = _fixture(h)
    try:
        problems = []
        for spec in SPECS:
            problems += _exercise(h, spec, state, raw, old, log, 0, 0)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_vector_resets_null_allocation(h):
    heap0 = h.heap_ptr
    state, raw, old, log = _fixture(h, allocation_succeeds=False)
    try:
        problems = []
        for spec in SPECS:
            problems += _exercise(h, spec, state, raw, old, log, 2, 1, allocation_succeeds=False)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_vector_resets_saturate_size_overflow(h):
    heap0 = h.heap_ptr
    state, raw, old, log = _fixture(h)
    try:
        problems = []
        for spec in SPECS:
            count = 0xFFFFFFFF // spec[1] + 1
            problems += _exercise(h, spec, state, raw, old, log, count, 0, expected_bytes=0xFFFFFFFF)
        problems += _exercise(h, SPECS[0], state, raw, old, log, 0x15555555, 0,
                              expected_bytes=0xFFFFFFFF)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
