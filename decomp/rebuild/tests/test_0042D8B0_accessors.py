"""0x42D8B0..0x42D990 (member accessors and flags), 0x42D8D0 / 0x42D9E0 (trajectory points), 0x42D940, 0x42DA40 and
0x42DC00 (record and vector element, handler forwarding)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

MEMBER_168 = 0x0042D8B0
TRAJECTORY = 0x0042D8D0
CLEAR_STARTED = 0x0042D910
MEMBER_2D0 = 0x0042D920
MEMBER_220 = 0x0042D930
RECORD = 0x0042D940
SET_ALIVE = 0x0042D960
CLEAR_ALIVE = 0x0042D970
MEMBER_4 = 0x0042D980
MEMBER_1DC = 0x0042D990
TRAJECTORY_OBJECT = 0x0042D9E0
VECTOR_ELEMENT = 0x0042DA40
FORWARD = 0x0042DC00

CLAMP = 0x005B8026
HALF = 0x00607CE0
GRAVITY = 0x00608B40

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _float(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


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
    """logs ECX and the stack arguments, returns `value` and pops `pop` bytes"""
    code = b'\x89\x0D' + _dword(log)
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _args_stub(h, log, value, pop, args):
    """stdcall-style variant: logs the stack arguments only"""
    code = b''
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def test_pointer_getters(h):
    """the member pointers are this plus the fixed offsets"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x200, bytes(0x200))
        wants = ((MEMBER_168, 0x168), (MEMBER_4, 4), (MEMBER_1DC, 0x1dc))
        problems = []
        for addr, off in wants:
            diffs = h.compare(addr, regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                return ['%08X: %s' % (addr, d) for d in diffs]
            got = h.call(addr, regs={UC_X86_REG_ECX: s})['eax']
            if got != s + off:
                problems.append('%08X gives %#x' % (addr, got))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_number_getters(h):
    """the +0x2D0 and +0x220 dwords"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x300, bytes(0x300))
        h.uc.mem_write(s + 0x2d0, _dword(0x11223344))
        h.uc.mem_write(s + 0x220, _dword(0x55667788))
        problems = []
        for addr, off, want in ((MEMBER_2D0, 0x2d0, 0x11223344), (MEMBER_220, 0x220, 0x55667788)):
            diffs = h.compare(addr, regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                return ['%08X: %s' % (addr, d) for d in diffs]
            got = h.call(addr, regs={UC_X86_REG_ECX: s})['eax']
            if got != want:
                problems.append('%08X gives %#x' % (addr, got))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_flag_setters(h):
    """+0x24 is set and cleared, +0x24C is cleared"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x260, b'\xAA' * 0x260)
        problems = []
        for addr, off, want in ((SET_ALIVE, 0x24, 1), (CLEAR_ALIVE, 0x24, 0), (CLEAR_STARTED, 0x24c, 0)):
            h.uc.mem_write(s + off, b'\xAA')
            diffs = h.compare(addr, regs={UC_X86_REG_ECX: s}, ret=None)
            if diffs:
                return ['%08X: %s' % (addr, d) for d in diffs]
            h.call(addr, regs={UC_X86_REG_ECX: s})
            if h.uc.mem_read(s + off, 1)[0] != want:
                problems.append('%08X leaves %d' % (addr, h.uc.mem_read(s + off, 1)[0]))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_record_lookup(h):
    """record index of the frame array: base + stride * index * 0x18; an out-of-range index reads record 0"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x20, bytes(0x20))
        records = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(s, _dword(records))
        h.uc.mem_write(s + 8, _dword(5))
        h.uc.mem_write(s + 0xc, _dword(2))
        for i in range(4):
            h.uc.mem_write(records + i * 0x30, _dword(0xA0 + i))
        problems = []
        for index, want in ((0, records), (2, records + 0x60), (7, records)):
            diffs = h.compare(RECORD, args=[index], regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                return ['index %d: %s' % (index, d) for d in diffs]
            got = h.call(RECORD, args=[index], regs={UC_X86_REG_ECX: s})['eax']
            if got != want:
                problems.append('index %d gives %#x' % (index, got))
        return problems or None
    finally:
        h.heap_ptr = heap0


def _trajectory_setup(h):
    s = h.alloc(0x40, bytes(0x40))
    out = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(s + 0x1c, struct.pack('<f', 3.0))
    h.uc.mem_write(s + 0x20, struct.pack('<f', 1.5))
    h.uc.mem_write(s, struct.pack('<f', 2.0))
    return s, out


def _trajectory_want(h, t):
    gravity = struct.unpack('<d', h.uc.mem_read(GRAVITY, 8))[0]
    x = 3.0 * t - 1.5 * 0.5
    return x, x * x / gravity * 2.0


def test_trajectory(h):
    """x = v.x * t - v.y / 2, y = x^2 / gravity * scale, z = 0"""
    heap0 = h.heap_ptr
    try:
        s, out = _trajectory_setup(h)
        problems = []
        for t in (0.0, 4.0, -1.25):
            h.uc.mem_write(out, b'\xCC' * 0x10)
            diffs = h.compare(TRAJECTORY, args=[out, _bits(t)], regs={UC_X86_REG_ECX: s}, ret=None)
            if diffs:
                return ['t %r: %s' % (t, d) for d in diffs]
            h.call(TRAJECTORY, args=[out, _bits(t)], regs={UC_X86_REG_ECX: s})
            wx, wy = _trajectory_want(h, t)
            if abs(_float(h, out) - wx) > 1e-4:
                problems.append('t %r: x is %r' % (t, _float(h, out)))
            if abs(_float(h, out + 4) - wy) > 1e-3:
                problems.append('t %r: y is %r' % (t, _float(h, out + 4)))
            if _u32(h, out + 8):
                problems.append('t %r: z is %r' % (t, _float(h, out + 8)))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_trajectory_object(h):
    """the same point, then 0x005B8026(out, out, this + 0x24); out is returned"""
    heap0 = h.heap_ptr
    try:
        s, out = _trajectory_setup(h)
        log = h.alloc(0x10, bytes(0x10))
        _hook(h, CLAMP, _args_stub(h, log, 0x5A5A, 12, 3))
        diffs = h.compare(TRAJECTORY_OBJECT, args=[out, _bits(4.0)], regs={UC_X86_REG_ECX: s}, ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(out, b'\xCC' * 0x10)
        res = h.call(TRAJECTORY_OBJECT, args=[out, _bits(4.0)], regs={UC_X86_REG_ECX: s})
        problems = []
        if res['eax'] != out:
            problems.append('the result is %#x' % res['eax'])
        if _u32(h, log) != out or _u32(h, log + 4) != out or _u32(h, log + 8) != s + 0x24:
            problems.append('the clamp got %#x, %#x, %#x' % (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8)))
        wx, wy = _trajectory_want(h, 4.0)
        if abs(_float(h, out) - wx) > 1e-4 or abs(_float(h, out + 4) - wy) > 1e-3:
            problems.append('the point is %r, %r' % (_float(h, out), _float(h, out + 4)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_vector_element(h):
    """element index of the +4 pointer vector; a null vector or a bad index gives 0"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x10, bytes(0x10))
        items = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(items, b''.join(_dword(0xB0 + i) for i in range(3)))
        h.uc.mem_write(s + 4, _dword(items))
        h.uc.mem_write(s + 8, _dword(items + 12))
        problems = []
        for index, want in ((0, 0xB0), (2, 0xB2), (3, 0)):
            diffs = h.compare(VECTOR_ELEMENT, args=[index], regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                return ['index %d: %s' % (index, d) for d in diffs]
            got = h.call(VECTOR_ELEMENT, args=[index], regs={UC_X86_REG_ECX: s})['eax']
            if got != want:
                problems.append('index %d gives %#x' % (index, got))
        h.uc.mem_write(s + 4, bytes(4))
        diffs = h.compare(VECTOR_ELEMENT, args=[0], regs={UC_X86_REG_ECX: s}, ret='eax')
        if diffs:
            return diffs
        if h.call(VECTOR_ELEMENT, args=[0], regs={UC_X86_REG_ECX: s})['eax']:
            problems.append('a null vector gives an element')
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_forwarder(h):
    """the handler at +0x10 is called with the object at +0x14 as its this, (this, arg) on the stack; this returns"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x20, bytes(0x20))
        target = h.alloc(0x10, bytes(0x10))
        log = h.alloc(0x10, bytes(0x10))
        handler = _callee_stub(h, log, 0x99, 8, 2)
        h.uc.mem_write(s + 0x10, _dword(handler))
        h.uc.mem_write(s + 0x14, _dword(target))
        diffs = h.compare(FORWARD, args=[0x1234], regs={UC_X86_REG_ECX: s}, ret='eax')
        if diffs:
            return diffs
        res = h.call(FORWARD, args=[0x1234], regs={UC_X86_REG_ECX: s})
        problems = []
        if res['eax'] != s:
            problems.append('the result is %#x' % res['eax'])
        if _u32(h, log) != target or _u32(h, log + 4) != s or _u32(h, log + 8) != 0x1234:
            problems.append('the handler got %#x, %#x, %#x' % (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8)))
        return problems or None
    finally:
        h.heap_ptr = heap0
