"""CSimpleAnimation (0x42A530..0x42AB70): the constructor (0x42A530), the accessors and playback helpers
(0x42A6A0..0x42A720), the frame step (0x42A7A0), the update and draw forwarders (0x42A7F0..0x42A940) and the four
segment direction helpers (0x42A980..0x42AB70).

The CRenderObject3D base constructor/destructor/update (0x4AD180, 0x4AD020, 0x4AD110) and the release helper
(0x4AC890) are stubs that log their arguments; the driven object's vftable is filled with stubs that log (this, args)
and return a distinct value, so the comparison covers both the memory the body writes and the calls it makes.
(std::string calls are the MSVCP80 imports the harness emulates.)"""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

CTOR = 0x0042A530
RESET = 0x0042A6A0
INC = 0x0042A6C0
AT_END = 0x0042A6D0
FIRST = 0x0042A700
LAST = 0x0042A710
DTOR = 0x0042A720
STEP = 0x0042A7A0
UPDATE = 0x0042A7F0
DRAW_A = 0x0042A820
DRAW_B = 0x0042A880
FWD_2C = 0x0042A8E0
FWD_28 = 0x0042A900
FWD_30 = 0x0042A910
FWD_38 = 0x0042A920
FWD_34 = 0x0042A930
FWD_3C = 0x0042A940
DIR_XZ = 0x0042A980
DIR_ZY = 0x0042AA30
DIR_MOTION = 0x0042AAB0
DIR_MOTION_IF = 0x0042AB70

BASE_CTOR = 0x004AD180
BASE_DTOR = 0x004AD020
BASE_UPDATE = 0x004AD110
RELEASE = 0x004AC890

VT_SKIP = 0x00608424

L_THIS = 0
LOG_SIZE = 0x20

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


def _string_text(h, p):
    size, capacity = struct.unpack('<II', h.uc.mem_read(p + 0x14, 8))
    ptr = p + 4 if capacity < 16 else _u32(h, p + 4)
    return bytes(h.uc.mem_read(ptr, size)).decode()


def _log(h):
    return h.alloc(LOG_SIZE, bytes(LOG_SIZE))


def _callee_stub(h, log, value, pop, args):
    """ECX this, `args` stack dwords: logs (this, arg0..) and returns `value`; the callee pops `pop` bytes"""
    code = b'\x89\x0D' + _dword(log)                                  # mov [log], ecx
    for i in range(args):
        code += (b'\x8B\x54\x24' + bytes([4 + 4 * i])                  # mov edx, [esp + 4 + 4*i]
                 + b'\x89\x15' + _dword(log + 4 + 4 * i))              # mov [log + ..], edx
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _arg(h, log, i):
    return _u32(h, log + 4 + 4 * i)


class Driven:
    def __init__(self, h, slots, size=0x200):
        self.obj = h.alloc(size, bytes(size))
        vt = h.alloc(0x100 * 4, bytes(0x100 * 4))
        self.logs = {}
        for off, (value, pop, args) in slots.items():
            log = _log(h)
            stub = _callee_stub(h, log, value, pop, args)
            h.uc.mem_write(vt + off, _dword(stub))
            self.logs[off] = log
        h.uc.mem_write(self.obj, _dword(vt))


def _callee_logs(value=0x0BEE0000, pop=0, args=0):
    return {BASE_CTOR: (value, pop, args)}


def _stub_callees(h):
    """base ctor/dtor/update and the release helper; returns their logs"""
    logs = {}
    for target, value, pop, args in ((BASE_CTOR, 0x0AD18000, 12, 3), (BASE_DTOR, 0x0AD02000, 0, 0),
                                     (BASE_UPDATE, 0x0AD11000, 4, 1), (RELEASE, 0x0AC89000, 0, 0)):
        logs[target] = _log(h)
        _hook(h, target, _callee_stub(h, logs[target], value, pop, args))
    return logs


def _animation(h):
    a = h.alloc(0x200, bytes(0x200))
    _put_string(h, a + 0x1e8, 'idle')
    return a


def _keys(h, rows):
    v = h.alloc(12 * len(rows), b''.join(struct.pack('<3f', *r) for r in rows))
    return v


def test_reset(h):
    """0x42A6A0 restarts the playback: the current index and the driven object follow the first key"""
    heap0 = h.heap_ptr
    try:
        a = _animation(h)
        driven = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(a + 0x1c4, _dword(driven))
        h.uc.mem_write(a + 0x1cc, _dword(9))
        h.uc.mem_write(a + 0x1d0, _dword(3))
        h.uc.mem_write(a + 0x1d8, _dword(0x0BEE0000))
        h.uc.mem_write(a + 0x1dc, b'\x01')
        diffs = h.compare(RESET, regs={UC_X86_REG_ECX: a})
        if diffs:
            return diffs
        res = h.call(RESET, regs={UC_X86_REG_ECX: a})
        problems = []
        if res['eax'] != 3:
            problems.append('the result is %#x' % res['eax'])
        if _u32(h, a + 0x1cc) != 3:
            problems.append('the index is %d' % _u32(h, a + 0x1cc))
        if _u32(h, driven + 0x1d8) != 3:
            problems.append("the driven object's index is %d" % _u32(h, driven + 0x1d8))
        if h.uc.mem_read(a + 0x1dc, 1)[0] != 0:
            problems.append('the stop flag was not cleared')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_increment(h):
    """0x42A6C0 adds one to the index"""
    heap0 = h.heap_ptr
    try:
        res = h.call(INC, args=[5])
        if res['fault']:
            return ['the replacement faulted: %s' % res['fault']]
        if res['eax'] != 6:
            return ['the result is %d' % res['eax']]
        diffs = h.compare(INC, args=[5])
        return diffs or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_at_end(h):
    """0x42A6D0 compares the driven object's index with the last key"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for driven_index, last, want in ((2, 2, 1), (2, 3, 0)):
            a = _animation(h)
            driven = h.alloc(0x200, bytes(0x200))
            h.uc.mem_write(a + 0x1c4, _dword(driven))
            h.uc.mem_write(a + 0x1d4, _dword(last))
            h.uc.mem_write(driven + 0x1d8, _dword(driven_index))
            diffs = h.compare(AT_END, regs={UC_X86_REG_ECX: a})
            if diffs:
                problems.extend(diffs)
                continue
            res = h.call(AT_END, regs={UC_X86_REG_ECX: a})
            if res['eax'] != want:
                problems.append('%d vs %d: the result is %d' % (driven_index, last, res['eax']))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_first_and_last(h):
    """0x42A700 / 0x42A710 read the first and the last key index"""
    heap0 = h.heap_ptr
    try:
        a = _animation(h)
        h.uc.mem_write(a + 0x1d0, _dword(4))
        h.uc.mem_write(a + 0x1d4, _dword(11))
        problems = []
        for entry, want in ((FIRST, 4), (LAST, 11)):
            diffs = h.compare(entry, regs={UC_X86_REG_ECX: a})
            if diffs:
                problems.extend(diffs)
                continue
            res = h.call(entry, regs={UC_X86_REG_ECX: a})
            if res['eax'] != want:
                problems.append('%08X returns %d' % (entry, res['eax']))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_destructor_releases(h):
    """0x42A720 with the owning flag set releases the driven object through slot 0 and drops it"""
    heap0 = h.heap_ptr
    try:
        call_logs = _stub_callees(h)
        driven = Driven(h, {0: (0x0BEE0001, 4, 1)})
        a = _animation(h)
        h.uc.mem_write(a + 0x1c4, _dword(driven.obj))
        h.uc.mem_write(a + 0x1e5, b'\x01')
        diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: a}, ret=None)
        if diffs:
            return diffs
        h.call(DTOR, regs={UC_X86_REG_ECX: a})
        problems = []
        if _u32(h, a) != VT_SKIP:
            problems.append('the vtable is %#x' % _u32(h, a))
        if _u32(h, a + 0x1c4) != 0:
            problems.append('the driven object was not dropped')
        log = driven.logs[0]
        if _u32(h, log) != driven.obj or _arg(h, log, 0) != 1:
            problems.append('the release got (%#x, %#x)' % (_u32(h, log), _arg(h, log, 0)))
        if _u32(h, call_logs[BASE_DTOR]) != a:
            problems.append('the base destructor got %#x' % _u32(h, call_logs[BASE_DTOR]))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_destructor_keeps(h):
    """0x42A720 without the owning flag leaves the driven object alone"""
    heap0 = h.heap_ptr
    try:
        call_logs = _stub_callees(h)
        driven = Driven(h, {0: (0x0BEE0001, 4, 1)})
        a = _animation(h)
        h.uc.mem_write(a + 0x1c4, _dword(driven.obj))
        diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: a}, ret=None)
        if diffs:
            return diffs
        h.call(DTOR, regs={UC_X86_REG_ECX: a})
        problems = []
        if _u32(h, a + 0x1c4) != driven.obj:
            problems.append('the driven object was dropped')
        if _u32(h, driven.logs[0]) != 0:
            problems.append('the release was called')
        if _u32(h, call_logs[BASE_DTOR]) != a:
            problems.append('the base destructor did not run')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _step_case(h, stopped, hidden, index, last):
    a = _animation(h)
    driven = Driven(h, {})
    h.uc.mem_write(a + 0x1c4, _dword(driven.obj))
    h.uc.mem_write(a + 0x1cc, _dword(index))
    h.uc.mem_write(a + 0x1d4, _dword(last))
    h.uc.mem_write(a + 0x1dc, bytes([stopped]))
    h.uc.mem_write(a + 0x49, bytes([0 if hidden else 1]))
    return a, driven.obj


def test_step(h):
    """0x42A7A0 advances the index, clamps it at the last key and passes the object pointer back"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for stopped, hidden, index, last in ((1, False, 1, 3), (0, True, 1, 3), (0, False, 1, 3), (0, False, 3, 3)):
            a, driven = _step_case(h, stopped, hidden, index, last)
            sentinel = 0x0BB0BB0B
            diffs = h.compare(STEP, regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
            if diffs:
                problems.extend('stopped %d hidden %d: %s' % (stopped, hidden, d) for d in diffs)
                continue
            res = h.call(STEP, regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
            want = sentinel if (stopped or hidden) else driven
            if res['eax'] != want:
                problems.append('stopped %d hidden %d: the result is %#x, not %#x'
                                % (stopped, hidden, res['eax'], want))
            if not (stopped or hidden):
                want_index = min(index + 1, last)
                if _u32(h, a + 0x1cc) != want_index:
                    problems.append('stopped %d hidden %d: the index is %d, not %d'
                                    % (stopped, hidden, _u32(h, a + 0x1cc), want_index))
                if _u32(h, driven + 0x1d8) != want_index:
                    problems.append('the driven object\'s index is %d' % _u32(h, driven + 0x1d8))
                if h.uc.mem_read(a + 0x1dc, 1)[0] != int(index >= last):
                    problems.append('stopped %d hidden %d: the stop flag is %d'
                                    % (stopped, hidden, h.uc.mem_read(a + 0x1dc, 1)[0]))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_update(h):
    """0x42A7F0 runs the base update and passes dt on to slot 4"""
    heap0 = h.heap_ptr
    try:
        call_logs = _stub_callees(h)
        driven = Driven(h, {4: (0x0BEE0002, 4, 1)})
        a = _animation(h)
        h.uc.mem_write(a + 0x1c4, _dword(driven.obj))
        dt = 0x3F400000                                                    # 0.75
        sentinel = 0x0BB0BB0B
        diffs = h.compare(UPDATE, args=[dt], regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
        if diffs:
            return diffs
        res = h.call(UPDATE, args=[dt], regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
        problems = []
        if res['eax'] != 0x0BEE0002:
            problems.append('the result is %#x' % res['eax'])
        log = call_logs[BASE_UPDATE]
        if (_u32(h, log), _arg(h, log, 0)) != (a, dt):
            problems.append('the base update got (%#x, %#x)' % (_u32(h, log), _arg(h, log, 0)))
        if (_u32(h, driven.logs[4]), _arg(h, driven.logs[4], 0)) != (driven.obj, dt):
            problems.append('slot 4 got (%#x, %#x)' % (_u32(h, driven.logs[4]), _arg(h, driven.logs[4], 0)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _draw_case(h, entry, slot):
    call_logs = _stub_callees(h)
    driven = Driven(h, {slot: (0x0BEE0003, 0, 0)})
    a = _animation(h)
    h.uc.mem_write(a + 0x1c4, _dword(driven.obj))
    return call_logs, driven, a


def test_draw_forwarders(h):
    """0x42A820 / 0x42A880 release first (when +0x1E4 is set) and forward to slots 0xD0 / 0xC8"""
    heap0 = h.heap_ptr
    try:
        problems = []
        sentinel = 0x0BB0BB0B
        for entry, slot in ((DRAW_A, 0xd0), (DRAW_B, 0xc8)):
            for hidden, owned, want in ((True, False, sentinel), (False, False, 0x0BEE0003),
                                        (False, True, 0x0BEE0003)):
                call_logs, driven, a = _draw_case(h, entry, slot)
                h.uc.mem_write(a + 0x49, bytes([0 if hidden else 1]))
                h.uc.mem_write(a + 0x1e4, bytes([int(owned)]))
                diffs = h.compare(entry, regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
                if diffs:
                    problems.extend('%08X hidden %d: %s' % (entry, hidden, d) for d in diffs)
                    continue
                res = h.call(entry, regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
                if res['eax'] != want:
                    problems.append('%08X hidden %d: the result is %#x, not %#x'
                                    % (entry, hidden, res['eax'], want))
                if hidden and _u32(h, call_logs[RELEASE]):
                    problems.append('%08X hidden: the release ran' % entry)
                if not hidden and owned and _u32(h, call_logs[RELEASE]) != a:
                    problems.append('%08X: the release got %#x' % (entry, _u32(h, call_logs[RELEASE])))
                if not hidden and _u32(h, driven.logs[slot]) != driven.obj:
                    problems.append('%08X: slot %#x got %#x' % (entry, slot, _u32(h, driven.logs[slot])))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_virtual_forwarders(h):
    """0x42A8E0..0x42A940 forward their arguments to the driven object's slots"""
    heap0 = h.heap_ptr
    try:
        problems = []
        cases = ((FWD_2C, 0x2c, (0x11, 0), (0x11, None)), (FWD_28, 0x28, (0x22,), (0x22,)),
                 (FWD_30, 0x30, (), ()), (FWD_38, 0x38, (0x33, 0x44), (0x33, 0x44)),
                 (FWD_34, 0x34, (0x55,), (0x55,)), (FWD_3C, 0x3c, (), ()))
        for entry, slot, args, want_args in cases:
            driven = Driven(h, {slot: (0x0BEE0004, 4 * len(args), len(args))})
            a = _animation(h)
            h.uc.mem_write(a + 0x1c4, _dword(driven.obj))
            diffs = h.compare(entry, args=list(args), regs={UC_X86_REG_ECX: a})
            if diffs:
                problems.extend('%08X: %s' % (entry, d) for d in diffs)
                continue
            res = h.call(entry, args=list(args), regs={UC_X86_REG_ECX: a})
            if res['eax'] != 0x0BEE0004:
                problems.append('%08X: the result is %#x' % (entry, res['eax']))
            log = driven.logs[slot]
            if _u32(h, log) != driven.obj:
                problems.append('%08X: slot %#x got this %#x' % (entry, slot, _u32(h, log)))
            for i, want in enumerate(want_args):
                if want is not None and _arg(h, log, i) != want:
                    problems.append('%08X: slot %#x arg %d is %#x' % (entry, slot, i, _arg(h, log, i)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_constructor(h):
    """0x42A530 builds the animation around the source's range and the driven object's keys"""
    heap0 = h.heap_ptr
    try:
        call_logs = _stub_callees(h)
        keys = _keys(h, ((0.0, 0.0, 1.5), (2.0, 0.0, 2.5), (5.0, 0.0, 3.5)))
        driven = Driven(h, {0xe0: (3, 0, 0), 0xe4: (keys, 0, 0)})
        h.uc.mem_write(driven.obj + 0x1d8, _dword(0x0BADBEEF))
        source = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(source + 0x1c, _dword(1))
        h.uc.mem_write(source + 0x20, _dword(2))
        a = h.alloc(0x200, bytes(0x200))
        _put_string(h, a + 8, 'walk;12')
        diffs = h.compare(CTOR, args=[source, driven.obj, 1], regs={UC_X86_REG_ECX: a})
        if diffs:
            return diffs
        res = h.call(CTOR, args=[source, driven.obj, 1], regs={UC_X86_REG_ECX: a})
        problems = []
        if res['eax'] != a:
            problems.append('the constructor returned %#x' % res['eax'])
        if _u32(h, a) != VT_SKIP:
            problems.append('the vtable is %#x' % _u32(h, a))
        if _string_text(h, a + 8) != '12':
            problems.append('the name tail is %r' % _string_text(h, a + 8))
        if _u32(h, a + 0x1c4) != driven.obj:
            problems.append('the driven object is %#x' % _u32(h, a + 0x1c4))
        if h.uc.mem_read(driven.obj + 0x1d4, 1)[0] != 0:
            problems.append('the driven object was not marked as not animating')
        if h.uc.mem_read(a + 0x1e5, 1)[0] != 1:
            problems.append('the owning flag is %d' % h.uc.mem_read(a + 0x1e5, 1)[0])
        if _u32(h, a + 0x1c8) != 3:
            problems.append('the key count is %d' % _u32(h, a + 0x1c8))
        if _u32(h, a + 0x1d8) != keys:
            problems.append('the key vector is %#x' % _u32(h, a + 0x1d8))
        if _u32(h, a + 0x1d0) != 1 or _u32(h, a + 0x1d4) != 2:
            problems.append('the range is %d..%d' % (_u32(h, a + 0x1d0), _u32(h, a + 0x1d4)))
        if _u32(h, a + 0x1cc) != 1 or _u32(h, driven.obj + 0x1d8) != 1:
            problems.append('the start index is %d / %d'
                            % (_u32(h, a + 0x1cc), _u32(h, driven.obj + 0x1d8)))
        if h.uc.mem_read(a + 0x1dc, 1)[0] != 0 or h.uc.mem_read(a + 0x1e4, 1)[0] != 0:
            problems.append('the flags were not cleared')
        f = struct.unpack('<f', h.uc.mem_read(a + 0x1e0, 4))[0]
        if abs(f - (-1.0)) > 1e-6:
            problems.append('the height difference is %r' % f)
        log = call_logs[BASE_CTOR]
        if _u32(h, log) != a or _arg(h, log, 0) != source:
            problems.append('the base constructor got (%#x, %#x)' % (_u32(h, log), _arg(h, log, 0)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_constructor_clamps(h):
    """0x42A530 clamps the end index to the last key when the range ends past it"""
    heap0 = h.heap_ptr
    try:
        _stub_callees(h)
        keys = _keys(h, ((0.0, 0.0, 1.5), (2.0, 0.0, 2.5), (5.0, 0.0, 3.5)))
        driven = Driven(h, {0xe0: (3, 0, 0), 0xe4: (keys, 0, 0)})
        source = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(source + 0x1c, _dword(0))
        h.uc.mem_write(source + 0x20, _dword(9))
        a = h.alloc(0x200, bytes(0x200))
        _put_string(h, a + 8, 'walk')
        diffs = h.compare(CTOR, args=[source, driven.obj, 0], regs={UC_X86_REG_ECX: a})
        if diffs:
            return diffs
        h.call(CTOR, args=[source, driven.obj, 0], regs={UC_X86_REG_ECX: a})
        problems = []
        if _u32(h, a + 0x1d4) != 2:
            problems.append('the end index is %d' % _u32(h, a + 0x1d4))
        f = struct.unpack('<f', h.uc.mem_read(a + 0x1e0, 4))[0]
        if abs(f - (-2.0)) > 1e-6:
            problems.append('the height difference is %r' % f)
        if _string_text(h, a + 8) != 'walk':
            problems.append('the name changed to %r' % _string_text(h, a + 8))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _direction(h, entry, index, first, angle, rows):
    a = h.alloc(0x200, bytes(0x200))
    vec = _keys(h, rows)
    h.uc.mem_write(a + 0x1cc, _dword(index))
    h.uc.mem_write(a + 0x1d0, _dword(first))
    h.uc.mem_write(a + 0x1d8, _dword(vec))
    out = h.alloc(8, bytes(8))
    return a, out, struct.unpack('<I', struct.pack('<f', angle))[0]


def test_directions(h):
    """0x42A980..0x42AAB0 turn the current segment's steps by the angle; 0x42AB70 takes the angle first (arg 1 is the
    angle, as its code reads its float from there) and reports whether it wrote"""
    heap0 = h.heap_ptr
    try:
        rows = ((0.0, 1.0, 1.5), (2.0, 2.0, 2.5), (5.0, 4.0, 3.5))
        problems = []
        for entry in (DIR_XZ, DIR_ZY, DIR_MOTION, DIR_MOTION_IF):
            for index, first in ((2, 0), (1, 0), (0, 0)):
                for angle in (0.0, 0.25, 1.0):
                    a, out, bits = _direction(h, entry, index, first, angle, rows)
                    args = [bits, out] if entry == DIR_MOTION_IF else [out, bits]
                    diffs = h.compare(entry, args=args, regs={UC_X86_REG_ECX: a}, ret=None)
                    if diffs:
                        problems.extend('%08X index %d angle %r: %s' % (entry, index, angle, d) for d in diffs)
                        continue
                    res = h.call(entry, args=args, regs={UC_X86_REG_ECX: a})
                    if res['fault']:
                        problems.append('%08X: the replacement faulted: %s' % (entry, res['fault']))
                        continue
                    want = out if entry != DIR_MOTION_IF else int(index != first)
                    if res['eax'] != want:
                        problems.append('%08X index %d angle %r: the result is %#x, not %#x'
                                        % (entry, index, angle, res['eax'], want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
