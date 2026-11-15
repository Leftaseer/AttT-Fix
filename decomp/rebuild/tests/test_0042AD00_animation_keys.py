"""CSimpleAnimation's key helpers (0x42AD00..0x42ADB0) and the CCritKeyAnimation / CInvSimpleAnimation pieces
(0x42AE80..0x42AF30).

0x42AD00 returns the key's height step as a double (st0); 0x42AD30 / 0x42ADB0 turn the segment step by an angle and
write two floats to the out vector.  The subclass constructors/destructors call the base 0x42A530 / 0x42A720, which
are stubbed here so the tests see the vtable and the forwarded arguments without the base's own work."""
import math
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

HEIGHT = 0x0042AD00
DIR_ZY = 0x0042AD30
DIR_MOTION = 0x0042ADB0
EMPTY_CTOR = 0x0042AE80
CRIT_CTOR = 0x0042AE90
CRIT_DTOR = 0x0042AEC0
INV_CALL = 0x0042AED0
OTHER_DTOR = 0x0042AF20
REACHED = 0x0042AF30

BASE_CTOR = 0x0042A530
BASE_DTOR = 0x0042A720

VT_CRIT = 0x00608534
VT_OTHER = 0x0060863C

RADIAN = 0.017453299835324287

L_THIS = 0
LOG_SIZE = 0x20

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


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


def _log(h):
    return h.alloc(LOG_SIZE, bytes(LOG_SIZE))


def _callee_stub(h, log, value, pop, args):
    """ECX this, `args` stack dwords: logs (this, arg0..) and returns `value`; the callee pops `pop` bytes"""
    code = b'\x89\x0D' + _dword(log)
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _arg(h, log, i):
    return _u32(h, log + 4 + 4 * i)


def _keys(h, rows):
    return h.alloc(12 * len(rows), b''.join(struct.pack('<3f', *r) for r in rows))


def _animation(h, rows, first):
    a = h.alloc(0x220, bytes(0x220))
    vec = _keys(h, rows)
    h.uc.mem_write(a + 0x1d0, _dword(first))
    h.uc.mem_write(a + 0x1d8, _dword(vec))
    return a


def _out(h):
    return h.alloc(8, bytes(8))


def _floats(h, addr):
    return struct.unpack('<2f', h.uc.mem_read(addr, 8))


ROWS = ((0.0, 1.0, 1.5), (2.0, 2.0, 2.5), (5.0, 4.0, 3.5))


def test_key_height(h):
    """0x42AD00 returns the key's z minus the previous key's z (0 for the first key) through st0"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for index in (2, 1):
            a = _animation(h, ROWS, 0)
            diffs = h.compare(HEIGHT, args=[index], regs={UC_X86_REG_ECX: a}, ret='st0')
            if diffs:
                problems.extend('index %d: %s' % (index, d) for d in diffs)
                continue
            res = h.call(HEIGHT, args=[index], regs={UC_X86_REG_ECX: a})
            want = ROWS[index][2] - ROWS[index - 1][2]
            if res['st0'] is None or abs(res['st0'] - want) > 1e-6:
                problems.append('index %d: the result is %r, not %r' % (index, res['st0'], want))
        a = _animation(h, ROWS, 0)
        diffs = h.compare(HEIGHT, args=[0], regs={UC_X86_REG_ECX: a}, ret='st0')
        if diffs:
            problems.extend('first key: %s' % d for d in diffs)
        else:
            res = h.call(HEIGHT, args=[0], regs={UC_X86_REG_ECX: a})
            if res['st0'] not in (None, 0.0):
                problems.append('the first key is %r' % res['st0'])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_vertical_direction(h):
    """0x42AD30 writes (sin * step, cos * step) of the key's z step, (0, 0) for the first key"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for index, first in ((2, 0), (1, 0), (0, 0)):
            for degrees in (0.0, 30.0, 90.0, 200.0):
                a = _animation(h, ROWS, first)
                out = _out(h)
                bits = struct.unpack('<I', struct.pack('<f', degrees))[0]
                diffs = h.compare(DIR_ZY, args=[out, bits, index], regs={UC_X86_REG_ECX: a})
                if diffs:
                    problems.extend('index %d %r deg: %s' % (index, degrees, d) for d in diffs)
                    continue
                res = h.call(DIR_ZY, args=[out, bits, index], regs={UC_X86_REG_ECX: a})
                if res['eax'] != out:
                    problems.append('index %d %r deg: the result is %#x' % (index, degrees, res['eax']))
                step = 0.0 if index == first else _f32(ROWS[index][2] - ROWS[index - 1][2])
                angle = _f32(degrees * RADIAN)
                want = (step * math.sin(angle), step * math.cos(angle))
                got = _floats(h, out)
                if any(abs(g - w) > 1e-5 for g, w in zip(got, want)):
                    problems.append('index %d %r deg: %r, not %r' % (index, degrees, got, want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_motion_direction(h):
    """0x42ADB0 writes (z*sin + x*cos, cos*z - sin*x) of the key's xz step, (0, 0) for the first key"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for index, first in ((2, 0), (1, 0), (0, 0)):
            for degrees in (0.0, 30.0, 90.0, 200.0):
                a = _animation(h, ROWS, first)
                out = _out(h)
                bits = struct.unpack('<I', struct.pack('<f', degrees))[0]
                diffs = h.compare(DIR_MOTION, args=[out, bits, index], regs={UC_X86_REG_ECX: a}, ret=None)
                if diffs:
                    problems.extend('index %d %r deg: %s' % (index, degrees, d) for d in diffs)
                    continue
                res = h.call(DIR_MOTION, args=[out, bits, index], regs={UC_X86_REG_ECX: a})
                if res['fault']:
                    problems.append('index %d %r deg: %s' % (index, degrees, res['fault']))
                    continue
                if index == first:
                    dx = dz = 0.0
                else:
                    dx = _f32(ROWS[index][0] - ROWS[index - 1][0])
                    dz = _f32(ROWS[index][2] - ROWS[index - 1][2])
                angle = _f32(degrees * RADIAN)
                sine, cosine = math.sin(angle), math.cos(angle)
                want = (dz * sine + dx * cosine, cosine * dz - sine * dx)
                got = _floats(h, out)
                if any(abs(g - w) > 1e-5 for g, w in zip(got, want)):
                    problems.append('index %d %r deg: %r, not %r' % (index, degrees, got, want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_empty_constructor(h):
    """0x42AE80 returns EAX and only pops its three stack arguments"""
    heap0 = h.heap_ptr
    try:
        sentinel = 0x0BB0BB0B
        diffs = h.compare(EMPTY_CTOR, args=[1, 2, 3], regs={UC_X86_REG_EAX: sentinel})
        if diffs:
            return diffs
        res = h.call(EMPTY_CTOR, args=[1, 2, 3], regs={UC_X86_REG_EAX: sentinel})
        return None if res['eax'] == sentinel else ['the result is %#x' % res['eax']]
    finally:
        _restore(h)
        h.heap_ptr = heap0


class Subclass:
    """an object buffer plus a log of the base constructor/destructor stubs"""

    def __init__(self, h):
        self.obj = h.alloc(0x220, bytes(0x220))
        self.ctor_log = _log(h)
        self.dtor_log = _log(h)
        _hook(h, BASE_CTOR, _callee_stub(h, self.ctor_log, 0x0BEE0006, 12, 3))
        _hook(h, BASE_DTOR, _callee_stub(h, self.dtor_log, 0x0BEE0007, 0, 0))


def test_crit_constructor(h):
    """0x42AE90 passes the three arguments to 0x42A530 and then installs vtable 0x608534"""
    heap0 = h.heap_ptr
    try:
        s = Subclass(h)
        name, driven = 0x11110000, 0x22220000
        diffs = h.compare(CRIT_CTOR, args=[name, driven, 1], regs={UC_X86_REG_ECX: s.obj})
        if diffs:
            return diffs
        res = h.call(CRIT_CTOR, args=[name, driven, 1], regs={UC_X86_REG_ECX: s.obj})
        problems = []
        if res['eax'] != s.obj:
            problems.append('the constructor returned %#x' % res['eax'])
        if _u32(h, s.obj) != VT_CRIT:
            problems.append('the vtable is %#x' % _u32(h, s.obj))
        log = s.ctor_log
        got = (_u32(h, log), _arg(h, log, 0), _arg(h, log, 1), _arg(h, log, 2))
        if got != (s.obj, name, driven, 1):
            problems.append('the base constructor got %r' % (got,))
        if _u32(h, s.dtor_log):
            problems.append('the base destructor ran')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_crit_destructor(h):
    """0x42AEC0 installs vtable 0x608534 and runs the base destructor 0x42A720"""
    heap0 = h.heap_ptr
    try:
        s = Subclass(h)
        diffs = h.compare(CRIT_DTOR, regs={UC_X86_REG_ECX: s.obj}, ret=None)
        if diffs:
            return diffs
        h.call(CRIT_DTOR, regs={UC_X86_REG_ECX: s.obj})
        problems = []
        if _u32(h, s.obj) != VT_CRIT:
            problems.append('the vtable is %#x' % _u32(h, s.obj))
        if _u32(h, s.dtor_log) != s.obj:
            problems.append('the base destructor got %#x' % _u32(h, s.dtor_log))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_other_destructor(h):
    """0x42AF20 installs vtable 0x60863C and runs the base destructor 0x42A720"""
    heap0 = h.heap_ptr
    try:
        s = Subclass(h)
        diffs = h.compare(OTHER_DTOR, regs={UC_X86_REG_ECX: s.obj}, ret=None)
        if diffs:
            return diffs
        h.call(OTHER_DTOR, regs={UC_X86_REG_ECX: s.obj})
        problems = []
        if _u32(h, s.obj) != VT_OTHER:
            problems.append('the vtable is %#x' % _u32(h, s.obj))
        if _u32(h, s.dtor_log) != s.obj:
            problems.append('the base destructor got %#x' % _u32(h, s.dtor_log))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_inv_call(h):
    """0x42AED0 calls slot 0x30 with a zero argument and returns its result"""
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x40, bytes(0x40))
        vt = h.alloc(0x100 * 4, bytes(0x100 * 4))
        log = _log(h)
        stub = _callee_stub(h, log, 0x0BEE0008, 4, 1)
        h.uc.mem_write(vt + 0xc0, _dword(stub))
        h.uc.mem_write(obj, _dword(vt))
        diffs = h.compare(INV_CALL, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        res = h.call(INV_CALL, regs={UC_X86_REG_ECX: obj})
        problems = []
        if res['eax'] != 0x0BEE0008:
            problems.append('the result is %#x' % res['eax'])
        if (_u32(h, log), _arg(h, log, 0)) != (obj, 0):
            problems.append('slot 0x30 got (%#x, %#x)' % (_u32(h, log), _arg(h, log, 0)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_reached(h):
    """0x42AF30 reports whether the driven object's index equals the animation's +0x204"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for index, reached, want in ((2, 2, 1), (2, 3, 0), (0, 0, 1)):
            a = h.alloc(0x220, bytes(0x220))
            driven = h.alloc(0x200, bytes(0x200))
            h.uc.mem_write(a + 0x1c4, _dword(driven))
            h.uc.mem_write(a + 0x204, _dword(reached))
            h.uc.mem_write(driven + 0x1d8, _dword(index))
            diffs = h.compare(REACHED, regs={UC_X86_REG_ECX: a})
            if diffs:
                problems.extend('%d vs %d: %s' % (index, reached, d) for d in diffs)
                continue
            res = h.call(REACHED, regs={UC_X86_REG_ECX: a})
            if res['eax'] != want:
                problems.append('%d vs %d: the result is %d' % (index, reached, res['eax']))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
