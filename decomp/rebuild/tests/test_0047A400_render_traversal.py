"""Transform traversal 0x47A400 and pass traversal 0x47ABA0; device and scene virtual calls are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

TRANSFORM = 0x0047A400
PASSES = 0x0047ABA0
DRAW = 0x004773F0
DEVICE_SLOT = 0x006C8C10
MATRIX_SLOT = 0x006CA0A4
saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _inc(log):
    return b'\xFF\x05' + _dword(log)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _transform_fixture(h):
    log = h.alloc(0x80, bytes(0x80))
    set_transform = (_arg(4, log) + _arg(8, log + 4) + _inc(log + 8) +
                     b'\x56\x57\x8B\x74\x24\x14' + b'\xBF' + _dword(log + 0x40) +
                     b'\xB9\x10\x00\x00\x00\xF3\xA5\x5F\x5E\xC2\x0C\x00')
    set_stub = _stub(h, set_transform)
    vtable = h.alloc(0xb4, bytes(0xb4))
    h.uc.mem_write(vtable + 0xb0, _dword(set_stub))
    device = h.alloc(4, _dword(vtable))
    _patch(h, DEVICE_SLOT, _dword(device))
    draw = (b'\x89\x0D' + _dword(log + 0x1c) + _arg(4, log + 0x20) +
            _arg(8, log + 0x24) + _inc(log + 0x28) +
            b'\xA1' + _dword(MATRIX_SLOT) + b'\x8B\x40\x34' +
            b'\xA3' + _dword(log + 0x2c) + b'\xC2\x08\x00')
    _hook(h, DRAW, draw)
    obj = h.alloc(0x218 + 2 * 0x21c, bytes(0x218 + 2 * 0x21c))
    return log, device, obj


def _set_object(h, obj, count, salt):
    for i in range(16):
        h.uc.mem_write(obj + 0x1d0 + 4 * i, _dword(salt + i))
    h.uc.mem_write(obj + 0x210, _dword(salt ^ 0x55550000))
    h.uc.mem_write(obj + 0x214, _dword(count))


def _check_transform(h, fixture, child_count, first, second):
    log, device, obj = fixture
    _set_object(h, obj, child_count, 0x1000)
    children = obj + 0x218
    h.uc.mem_write(obj + 0x218, _dword(children))
    for i in range(child_count):
        _set_object(h, children + i * 0x21c, 0, 0x2000 + i * 0x100)
    diffs = h.compare(TRANSFORM, args=(first, second), regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
    if diffs:
        return diffs
    h.uc.mem_write(log, bytes(0x80))
    result = h.call(TRANSFORM, args=(first, second), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return [result['fault']]
    last = obj + 0x218 + (child_count - 1) * 0x21c if child_count else obj
    salt = 0x2000 + (child_count - 1) * 0x100 if child_count else 0x1000
    calls = child_count + 1
    expected = (
        (0, device, 'device'), (4, 0x100, 'transform state'), (8, calls, 'transform calls'),
        (0x1c, salt ^ 0x55550000, 'draw object'), (0x20, first, 'first draw argument'),
        (0x24, second, 'second draw argument'), (0x28, calls, 'draw calls'),
        (0x2c, 0, 'current matrix component'),
    )
    problems = []
    for offset, want, label in expected:
        got = _u32(h, log + offset)
        if got != want:
            problems.append('%s is %#x, want %#x' % (label, got, want))
    for i in range(16):
        want = 0 if i == 13 else salt + i
        got = _u32(h, log + 0x40 + 4 * i)
        if got != want:
            problems.append('matrix[%d] is %#x, want %#x' % (i, got, want))
    return problems


def test_transform_traversal(h):
    heap0 = h.heap_ptr
    try:
        fixture = _transform_fixture(h)
        return _check_transform(h, fixture, 0, 0x12345678, 0x23456789) or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_transform_traversal_recurses(h):
    heap0 = h.heap_ptr
    try:
        fixture = _transform_fixture(h)
        return _check_transform(h, fixture, 2, 0x3456789A, 0x456789AB) or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _pass_fixture(h):
    log = h.alloc(0x50, bytes(0x50))
    scene = h.alloc(4)
    vtable = h.alloc(0x28, bytes(0x28))
    h.uc.mem_write(scene, _dword(vtable))
    count = (b'\x89\x0D' + _dword(log) + _arg(8, log + 4) + _inc(log + 8) +
             b'\x8B\x4C\x24\x04\xA1' + _dword(log + 0x40) + b'\x89\x01\xC2\x08\x00')
    begin = _arg(4, log + 0x0c) + _inc(log + 0x10) + b'\xC2\x04\x00'
    h.uc.mem_write(vtable + 0x18, _dword(_stub(h, count)))
    h.uc.mem_write(vtable + 0x20, _dword(_stub(h, begin)))
    h.uc.mem_write(vtable + 0x24, _dword(_stub(h, _inc(log + 0x14) + b'\xC3')))
    h.uc.mem_write(vtable + 0x1c, _dword(_stub(h, _inc(log + 0x18) + b'\xC3')))
    draw = (b'\x89\x0D' + _dword(log + 0x1c) + _arg(4, log + 0x20) +
            _arg(8, log + 0x24) + _inc(log + 0x28) + b'\xC2\x08\x00')
    _hook(h, TRANSFORM, draw)
    obj = h.alloc(0x200, bytes(0x200))
    children = h.alloc(2 * 0x21c, bytes(2 * 0x21c))
    h.uc.mem_write(obj + 0x1d0, _dword(0x11112222))
    h.uc.mem_write(obj + 0x1d8, _dword(0x33334444))
    h.uc.mem_write(obj + 0x1e0, _dword(2))
    h.uc.mem_write(obj + 0x1e4, _dword(children))
    return log, scene, obj, children


def test_pass_traversal(h):
    heap0 = h.heap_ptr
    try:
        log, scene, obj, children = _pass_fixture(h)
        problems = []
        for count in (0, 2):
            h.uc.mem_write(log + 0x40, _dword(count))
            diffs = h.compare(PASSES, args=(scene,), regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
            if diffs:
                problems += ['count %d: %s' % (count, d) for d in diffs]
                continue
            h.uc.mem_write(log, bytes(0x40))
            result = h.call(PASSES, args=(scene,), regs={UC_X86_REG_ECX: obj})
            if result['fault']:
                problems.append(result['fault'])
                continue
            calls = count * 2
            expected = (
                (0, scene, 'scene'), (4, 0, 'unused count argument'), (8, 1, 'count calls'),
                (0x0c, count - 1 if count else 0, 'last pass'), (0x10, count, 'begin calls'),
                (0x14, count, 'end calls'), (0x18, 1, 'finish calls'),
                (0x1c, children + 0x21c if calls else 0, 'last child'),
                (0x20, 0x33334444 if calls else 0, 'first child argument'),
                (0x24, 0x11112222 if calls else 0, 'second child argument'),
                (0x28, calls, 'child calls'),
            )
            for offset, want, label in expected:
                got = _u32(h, log + offset)
                if got != want:
                    problems.append('count %d: %s is %#x, want %#x' % (count, label, got, want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
