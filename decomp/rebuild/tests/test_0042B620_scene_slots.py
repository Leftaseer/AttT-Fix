"""The CArmyScreenScene slot setters/getters (0x42B620..0x42B670), its release routine (0x42B680), the pair table
lookup (0x42B720), the 0x00608848 vtable installers (0x42B7B0/0x42B7C0/0x42B7D0) and the constructor (0x42B7F0)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

SET_SLOT_C = 0x0042B620
SET_OBJ = 0x0042B630
SET_SLOT_14 = 0x0042B640
SET_SLOT_50 = 0x0042B650
GET_SLOT_50 = 0x0042B660
GET_INDEX = 0x0042B670
RELEASE = 0x0042B680
PAIR_LOOKUP = 0x0042B720
SET_VT_THIS = 0x0042B7B0
SET_VT = 0x0042B7C0
DELETING_DTOR = 0x0042B7D0
CTOR = 0x0042B7F0

BASE_CTOR = 0x004B20D0
OP_DELETE = 0x005E3E9C

VT_42B7F0 = 0x00608848
PAIR_KEYS = 0x006C8858
PAIR_VALUES = 0x006C885C
PAIR_COUNT = 0x006BF630

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


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


def _callee_stub(h, log, value, pop, args):
    """logs ECX and the stack arguments into `log`, returns `value` and pops `pop` bytes"""
    code = b'\x89\x0D' + _dword(log)
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _log(h, size=0x20):
    return h.alloc(size, bytes(size))


def test_slot_setters(h):
    """+0xC, +0x14 and +0x50 take the value; +0x10 takes and returns the pointer"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x60, bytes(0x60))
        diffs = h.compare(SET_SLOT_C, args=[0x11223344], regs={UC_X86_REG_ECX: s})
        if diffs:
            return diffs
        diffs = h.compare(SET_OBJ, args=[0x55667788], regs={UC_X86_REG_ECX: s}, ret='eax')
        if diffs:
            return diffs
        diffs = h.compare(SET_SLOT_14, args=[0x99aabbcc], regs={UC_X86_REG_ECX: s})
        if diffs:
            return diffs
        diffs = h.compare(SET_SLOT_50, args=[0xddeeff00], regs={UC_X86_REG_ECX: s})
        if diffs:
            return diffs
        h.call(SET_SLOT_C, args=[0x11223344], regs={UC_X86_REG_ECX: s})
        h.call(SET_SLOT_14, args=[0x99aabbcc], regs={UC_X86_REG_ECX: s})
        h.call(SET_SLOT_50, args=[0xddeeff00], regs={UC_X86_REG_ECX: s})
        res = h.call(SET_OBJ, args=[0x55667788], regs={UC_X86_REG_ECX: s})
        problems = []
        if _u32(h, s + 0xc) != 0x11223344:
            problems.append('+0xC is %#x' % _u32(h, s + 0xc))
        if _u32(h, s + 0x10) != 0x55667788:
            problems.append('+0x10 is %#x' % _u32(h, s + 0x10))
        if res['eax'] != 0x55667788:
            problems.append('the stored pointer result is %#x' % res['eax'])
        if _u32(h, s + 0x14) != 0x99aabbcc:
            problems.append('+0x14 is %#x' % _u32(h, s + 0x14))
        if _u32(h, s + 0x50) != 0xddeeff00:
            problems.append('+0x50 is %#x' % _u32(h, s + 0x50))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_getters(h):
    """+0x50 and +0x1D8 are read back"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x240, bytes(0x240))
        h.uc.mem_write(s + 0x50, _dword(0xcafebabe))
        h.uc.mem_write(s + 0x1d8, _dword(0x0badf00d))
        diffs = h.compare(GET_SLOT_50, regs={UC_X86_REG_ECX: s})
        if diffs:
            return diffs
        diffs = h.compare(GET_INDEX, regs={UC_X86_REG_ECX: s})
        if diffs:
            return diffs
        problems = []
        if h.call(GET_SLOT_50, regs={UC_X86_REG_ECX: s})['eax'] != 0xcafebabe:
            problems.append('+0x50 getter')
        if h.call(GET_INDEX, regs={UC_X86_REG_ECX: s})['eax'] != 0x0badf00d:
            problems.append('+0x1D8 getter')
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_release(h):
    """each of the six slots is released through vtable entry 0 with 1 and then cleared; +0x3C is returned"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(s + 0x3c, _dword(0x12345678))
        offsets = (0xc4, 0xc0, 0xbc, 0xb8, 0xcc, 0xc8)
        logs = []
        for k, o in enumerate(offsets):
            obj = h.alloc(0x20, bytes(0x20))
            vt = h.alloc(0x40, bytes(0x40))
            log = _log(h, 8)
            h.uc.mem_write(vt, _dword(_callee_stub(h, log, 0, 4, 1)))
            h.uc.mem_write(obj, _dword(vt))
            h.uc.mem_write(s + o, _dword(obj))
            logs.append((o, obj, log))
        diffs = h.compare(RELEASE, regs={UC_X86_REG_ECX: s}, ret='eax')
        if diffs:
            return diffs
        res = h.call(RELEASE, regs={UC_X86_REG_ECX: s})
        problems = []
        if res['eax'] != 0x12345678:
            problems.append('the result is %#x' % res['eax'])
        for o, obj, log in logs:
            if _u32(h, log) != obj:
                problems.append('slot %#x was not released' % o)
            elif _u32(h, log + 4) != 1:
                problems.append('slot %#x was released with %d' % (o, _u32(h, log + 4)))
            if _u32(h, s + o) != 0:
                problems.append('slot %#x is not cleared' % o)
        return problems or None
    finally:
        h.heap_ptr = heap0


PAIRS = ((5, 7), (0, 0), (9, 11))


def _write_pairs(h):
    _patch(h, PAIR_COUNT, _dword(len(PAIRS)))
    for i, (a, b) in enumerate(PAIRS):
        _patch(h, PAIR_KEYS + 8 * i, _dword(a))
        _patch(h, PAIR_VALUES + 8 * i, _dword(b))


def test_pair_lookup(h):
    """a pair matches on the first key when it is 0, otherwise on both values"""
    heap0 = h.heap_ptr
    try:
        _write_pairs(h)
        cases = [((5, 7), 0), ((5, 8), -1), ((0, 123), 1), ((9, 11), 2), ((4, 4), -1)]
        problems = []
        for (pair, want) in cases:
            diffs = h.compare(PAIR_LOOKUP, args=list(pair), ret='eax')
            if diffs:
                problems.extend(diffs)
                continue
            res = h.call(PAIR_LOOKUP, args=list(pair))
            got = struct.unpack('<i', struct.pack('<I', res['eax']))[0]
            if got != want:
                problems.append('%r is at %d' % (pair, got))
        _patch(h, PAIR_COUNT, _dword(0))
        diffs = h.compare(PAIR_LOOKUP, args=[5, 7], ret='eax')
        if diffs:
            problems.extend(diffs)
        res = h.call(PAIR_LOOKUP, args=[5, 7])
        if res['eax'] != 0xFFFFFFFF:
            problems.append('an empty table gives %#x' % res['eax'])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_vtable_installers(h):
    """0x42B7B0 returns this, 0x42B7C0 does not touch the registers; both store 0x00608848 at +0"""
    heap0 = h.heap_ptr
    try:
        a = h.alloc(0x20, bytes(0x20))
        b = h.alloc(0x20, bytes(0x20))
        diffs = h.compare(SET_VT_THIS, regs={UC_X86_REG_ECX: a}, ret='eax')
        if diffs:
            return diffs
        diffs = h.compare(SET_VT, regs={UC_X86_REG_ECX: b}, ret=None)
        if diffs:
            return diffs
        problems = []
        res = h.call(SET_VT_THIS, regs={UC_X86_REG_ECX: a})
        if _u32(h, a) != VT_42B7F0:
            problems.append('the first vtable is %#x' % _u32(h, a))
        if res['eax'] != a:
            problems.append('the first installer returned %#x' % res['eax'])
        h.call(SET_VT, regs={UC_X86_REG_ECX: b})
        if _u32(h, b) != VT_42B7F0:
            problems.append('the second vtable is %#x' % _u32(h, b))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_deleting_destructor(h):
    """the low flag bit calls operator delete; the vtable is stored either way and this is returned"""
    heap0 = h.heap_ptr
    try:
        for freeing in (0, 1):
            s = h.alloc(0x20, bytes(0x20))
            log = _log(h, 8)
            _hook(h, OP_DELETE, _callee_stub(h, log, 0x0DE1E7E9, 4, 1))
            diffs = h.compare(DELETING_DTOR, args=[freeing], regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                return diffs
            h.uc.mem_write(s, bytes(4))
            h.uc.mem_write(log, bytes(8))
            res = h.call(DELETING_DTOR, args=[freeing], regs={UC_X86_REG_ECX: s})
            problems = []
            if _u32(h, s) != VT_42B7F0:
                problems.append('the vtable is %#x' % _u32(h, s))
            if res['eax'] != s:
                problems.append('the result is %#x' % res['eax'])
            if freeing and _u32(h, log) != s:
                problems.append('operator delete did not get the object')
            if not freeing and _u32(h, log) != 0:
                problems.append('operator delete ran without the flag')
            _restore(h)
            if problems:
                return problems
        return None
    finally:
        h.heap_ptr = heap0


def test_constructor(h):
    """the base constructor, the zeroed slots, the three vtables, the halved screen extents and the zero byte"""
    heap0 = h.heap_ptr
    try:
        base_log = _log(h, 8)
        _hook(h, BASE_CTOR, _callee_stub(h, base_log, 0, 4, 1))
        s = h.alloc(0x200, bytes(0x200))
        diffs = h.compare(CTOR, regs={UC_X86_REG_ECX: s}, ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(s, bytes(0x200))
        res = h.call(CTOR, regs={UC_X86_REG_ECX: s})
        problems = []
        if res['eax'] != s:
            problems.append('the result is %#x' % res['eax'])
        if _u32(h, base_log) != s or _u32(h, base_log + 4) != 0:
            problems.append('the base constructor got %#x, %d' % (_u32(h, base_log), _u32(h, base_log + 4)))
        if _u32(h, s) != 0x0060888C or _u32(h, s + 4) != 0x0060886C or _u32(h, s + 0x74) != 0x00608864:
            problems.append('the vtables are %#x %#x %#x' % (_u32(h, s), _u32(h, s + 4), _u32(h, s + 0x74)))
        for o in list(range(0x84, 0xB0, 4)) + list(range(0xB8, 0xD0, 4)):
            if _u32(h, s + o) != 0:
                problems.append('+%#x is %#x' % (o, _u32(h, s + o)))
        if abs(_f32(h, s + 0xB0) + 400.0) > 1e-3:
            problems.append('+0xB0 is %r' % _f32(h, s + 0xB0))
        if abs(_f32(h, s + 0xB4) + 300.0) > 1e-3:
            problems.append('+0xB4 is %r' % _f32(h, s + 0xB4))
        if h.uc.mem_read(s + 0x158, 1)[0] != 0:
            problems.append('+0x158 is not zero')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
