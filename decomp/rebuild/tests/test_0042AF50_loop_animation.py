"""CLoopAnimation's constructor (0x42AF50): the descriptor name becomes the source object (through the string copy
constructor and 0x0042A010), the CSimpleAnimation base (0x0042A530) is built around it and the loop range, and the
three height differences are computed.  The base render object's constructor (0x4AD180) and the driven object's key
slots (0xE0 / 0xE4) are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x0042AF50
SOURCE_CTOR = 0x0042A010
BASE_ANIM_CTOR = 0x0042A530
RENDER_CTOR = 0x004AD180
VT_LOOP = 0x00608744

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, stub):
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def _put_string(h, p, text):
    data = text.encode()
    if len(data) < 16:
        h.uc.mem_write(p + 4, data + b'\0' * (16 - len(data)))
        capacity = 15
    else:
        q = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(p + 4, _dword(q))
        capacity = len(data)
    h.uc.mem_write(p + 0x14, struct.pack('<II', len(data), capacity))


def _callee_stub(h, log, value, pop, args):
    code = b'\x89\x0D' + _dword(log)
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _key_object(h, count, keys):
    obj = h.alloc(0x200, bytes(0x200))
    vt = h.alloc(0x100 * 4, bytes(0x100 * 4))
    log = h.alloc(0x100, bytes(0x100))
    for off, value in ((0xe0, count), (0xe4, keys)):
        stub = _callee_stub(h, log + off // 4, value, 0, 0)
        h.uc.mem_write(vt + off, _dword(stub))
    h.uc.mem_write(obj, _dword(vt))
    return obj


def _keys(h, rows):
    return h.alloc(12 * len(rows), b''.join(struct.pack('<3f', *r) for r in rows))


def _descriptor(h, name, a, start, end, raw_end):
    d = h.alloc(0x40, bytes(0x40))
    _put_string(h, d, name)
    h.uc.mem_write(d + 0x1c, _dword(a))
    h.uc.mem_write(d + 0x20, _dword(start))
    h.uc.mem_write(d + 0x24, _dword(end))
    h.uc.mem_write(d + 0x28, _dword(raw_end))
    return d


def _floats(h, addr, n):
    return struct.unpack('<%df' % n, h.uc.mem_read(addr, 4 * n))


ROWS = ((0.0, 0.0, 1.0), (2.0, 0.0, 2.0), (5.0, 0.0, 4.0), (9.0, 0.0, 8.0))


def _case(h, name, a, start, end, raw_end, count=4):
    log = h.alloc(0x20, bytes(0x20))
    _hook(h, RENDER_CTOR, _callee_stub(h, log, 0x0AD18000, 12, 0))      # the source object's stack address is
                                                                         # deliberately not logged
    driven = _key_object(h, count, _keys(h, ROWS))
    desc = _descriptor(h, name, a, start, end, raw_end)
    anim = h.alloc(0x240, bytes(0x240))
    return anim, desc, driven, log


def _check(h, anim, desc, driven, log, start, end):
    problems = []
    if _u32(h, anim) != VT_LOOP:
        problems.append('the vtable is %#x' % _u32(h, anim))
    last = _u32(h, anim + 0x1d4)
    got = _u32(h, anim + 0x204)
    if got != start:
        problems.append('+0x204 is %d, not %d' % (got, start))
    want_end = min(end, last)
    got = _u32(h, anim + 0x208)
    if got != want_end:
        problems.append('+0x208 is %d, not %d' % (got, want_end))
    if h.uc.mem_read(anim + 0x20c, 1)[0] != 0:
        problems.append('the +0x20C byte is set')
    first = _u32(h, anim + 0x1d0)
    count = _u32(h, anim + 0x1c8)
    keys = _u32(h, anim + 0x1d8)
    if first != _u32(h, desc + 0x1c):
        problems.append('the first key is %d' % first)
    if last != min(_u32(h, desc + 0x28), count - 1):
        problems.append('the last key is %d' % last)
    z = lambda i: struct.unpack('<f', h.uc.mem_read(keys + 12 * i + 8, 4))[0]
    want = (z(first) - z(start - 1), z(want_end) - z(last), z(start - 1) - z(want_end))
    got_f = _floats(h, anim + 0x210, 3)
    if any(abs(g - w) > 1e-6 for g, w in zip(got_f, want)):
        problems.append('the height differences are %r, not %r' % (got_f, want))
    if _u32(h, log) != anim:
        problems.append('the base constructor got %#x' % _u32(h, log))
    return problems


def test_loop_constructor(h):
    """0x42AF50 builds the base animation and the loop range and height differences from the descriptor"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for name, a, start, end, raw_end in (('walk', 1, 3, 1, 3), ('walk', 1, 3, 9, 3),
                                             ('idle', 2, 1, 2, 2), ('a-long-animation-name', 1, 2, 3, 3)):
            anim, desc, driven, log = _case(h, name, a, start, end, raw_end)
            diffs = h.compare(CTOR, args=[desc, driven, 0], regs={UC_X86_REG_ECX: anim})
            if diffs:
                problems.extend('%r: %s' % (name, d) for d in diffs)
                continue
            _restore(h)                                                    # the hooks are re-installed per case
            anim, desc, driven, log = _case(h, name, a, start, end, raw_end)
            res = h.call(CTOR, args=[desc, driven, 0], regs={UC_X86_REG_ECX: anim})
            if res['fault']:
                problems.append('%r: the replacement faulted: %s' % (name, res['fault']))
                continue
            if res['eax'] != anim:
                problems.append('%r: the constructor returned %#x' % (name, res['eax']))
            problems.extend('%r: %s' % (name, p) for p in _check(h, anim, desc, driven, log, start, end))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_loop_constructor_owning(h):
    """0x42AF50 passes the owning flag on to the base construction"""
    heap0 = h.heap_ptr
    try:
        anim, desc, driven, log = _case(h, 'walk', 1, 3, 1, 3)
        diffs = h.compare(CTOR, args=[desc, driven, 1], regs={UC_X86_REG_ECX: anim})
        if diffs:
            return diffs
        _restore(h)
        anim, desc, driven, log = _case(h, 'walk', 1, 3, 1, 3)
        h.call(CTOR, args=[desc, driven, 1], regs={UC_X86_REG_ECX: anim})
        problems = []
        if h.uc.mem_read(anim + 0x1e5, 1)[0] != 1:
            problems.append('the owning flag is %d' % h.uc.mem_read(anim + 0x1e5, 1)[0])
        if h.uc.mem_read(driven + 0x1d4, 1)[0] != 0:
            problems.append('the driven object was not marked as not animating')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
