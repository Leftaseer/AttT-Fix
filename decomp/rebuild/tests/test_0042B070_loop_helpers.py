"""The CLoopAnimation helpers (0x42B070..0x42B160) and the CSimpleAnimation subclass destructors/constructor
(0x42B240..0x42B360).

The height queries and the index stepper work on a plain key vector; the destructors are checked against stubs of the
base destructor (0x42A720) and operator delete (0x5E3E9C); 0x42B1F0's operator new/delete (0x5E3B10 / 0x5E3EBA) are
stubs as well; 0x42B290 mirrors 0x42AF50 with the other vtable."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

HEIGHT = 0x0042B070
RESTART = 0x0042B0A0
BACKWARDS = 0x0042B0D0
AT_LOOP_END = 0x0042B0E0
LOOP_HEIGHT = 0x0042B100
LOOP_START = 0x0042B130
LOOP_END = 0x0042B140
LOOP_DTOR_BODY = 0x0042B150
STEP = 0x0042B160
RESIZE = 0x0042B1F0
DTOR_BASE = 0x0042B240
DTOR_INV = 0x0042B260
CTOR_OTHER = 0x0042B290
DTOR_CRIT = 0x0042B330
DTOR_LOOP = 0x0042B360

BASE_DTOR = 0x0042A720
BASE_ANIM_CTOR = 0x0042A530
RENDER_CTOR = 0x004AD180
OP_DELETE_THIS = 0x005E3E9C
OP_NEW = 0x005E3B10
OP_DELETE = 0x005E3EBA

VT_INV = 0x00608534
VT_OTHER = 0x0060863C
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


def _callee_stub(h, log, value, pop, args):
    code = b'\x89\x0D' + _dword(log)
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _arg_stub(h, log, value, pop, args):
    """like _callee_stub but logs only the stack arguments (a cdecl callee's ECX is not an argument)"""
    code = b''
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _arg(h, log, i):
    return _u32(h, log + 4 + 4 * i)


def _log(h, size=0x20):
    return h.alloc(size, bytes(size))


def _keys(h, rows):
    return h.alloc(12 * len(rows), b''.join(struct.pack('<3f', *r) for r in rows))


def _loop(h, rows, first=1, start=3, last=3, driven_index=0, flags=0):
    a = h.alloc(0x240, bytes(0x240))
    driven = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(a + 0x1c4, _dword(driven))
    h.uc.mem_write(a + 0x1d8, _dword(_keys(h, rows)))
    h.uc.mem_write(a + 0x1d0, _dword(first))
    h.uc.mem_write(a + 0x1d4, _dword(last))
    h.uc.mem_write(a + 0x204, _dword(start))
    h.uc.mem_write(a + 0x208, _dword(last))
    h.uc.mem_write(a + 0x1cc, _dword(start))
    h.uc.mem_write(a + 0x20c, bytes([flags & 1]))
    h.uc.mem_write(a + 0x1dc, bytes([(flags >> 1) & 1]))
    h.uc.mem_write(driven + 0x1d8, _dword(driven_index))
    return a, driven


ROWS = ((0.0, 0.0, 1.0), (2.0, 0.0, 3.0), (5.0, 0.0, 7.0), (9.0, 0.0, 2.5))


def test_height(h):
    """0x42B070 returns the height difference of two keys through st0"""
    heap0 = h.heap_ptr
    try:
        problems = []
        a, _ = _loop(h, ROWS)
        for i, j in ((3, 1), (2, 0), (0, 3)):
            diffs = h.compare(HEIGHT, args=[i, j], regs={UC_X86_REG_ECX: a}, ret='st0')
            if diffs:
                problems.extend('%d-%d: %s' % (i, j, d) for d in diffs)
                continue
            res = h.call(HEIGHT, args=[i, j], regs={UC_X86_REG_ECX: a})
            want = ROWS[i][2] - ROWS[j][2]
            if res['st0'] is None or abs(res['st0'] - want) > 1e-6:
                problems.append('%d-%d: %r, not %r' % (i, j, res['st0'], want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_restart(h):
    """0x42B0A0 puts the current index back to the first key and clears the flags"""
    heap0 = h.heap_ptr
    try:
        a, driven = _loop(h, ROWS, first=0x105, start=3, flags=3)
        diffs = h.compare(RESTART, regs={UC_X86_REG_ECX: a})
        if diffs:
            return diffs
        res = h.call(RESTART, regs={UC_X86_REG_ECX: a})
        problems = []
        if res['eax'] != 0x100:
            problems.append('the result is %#x' % res['eax'])
        if _u32(h, a + 0x1cc) != 0x105:
            problems.append('the index is %d' % _u32(h, a + 0x1cc))
        if _u32(h, driven + 0x1d8) != 0x105:
            problems.append("the driven index is %d" % _u32(h, driven + 0x1d8))
        if h.uc.mem_read(a + 0x20c, 1)[0] or h.uc.mem_read(a + 0x1dc, 1)[0]:
            problems.append('the flags are still set')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_backwards(h):
    """0x42B0D0 sets the direction byte and returns EAX untouched"""
    heap0 = h.heap_ptr
    try:
        a, _ = _loop(h, ROWS)
        sentinel = 0x0BB0BB0B
        diffs = h.compare(BACKWARDS, regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
        if diffs:
            return diffs
        res = h.call(BACKWARDS, regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
        problems = []
        if res['eax'] != sentinel:
            problems.append('the result is %#x' % res['eax'])
        if h.uc.mem_read(a + 0x20c, 1)[0] != 1:
            problems.append('the direction byte is %d' % h.uc.mem_read(a + 0x20c, 1)[0])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_at_loop_end(h):
    """0x42B0E0 compares the driven index with the loop's end key"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for driven_index in (3, 2):
            a, _ = _loop(h, ROWS, last=3, driven_index=driven_index)
            diffs = h.compare(AT_LOOP_END, regs={UC_X86_REG_ECX: a})
            if diffs:
                problems.extend('index %d: %s' % (driven_index, d) for d in diffs)
                continue
            res = h.call(AT_LOOP_END, regs={UC_X86_REG_ECX: a})
            if res['eax'] != int(driven_index == 3):
                problems.append('index %d gives %d' % (driven_index, res['eax']))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_loop_height(h):
    """0x42B100 returns the height difference of the loop's two end keys through st0"""
    heap0 = h.heap_ptr
    try:
        a, _ = _loop(h, ROWS, start=3, last=2)
        diffs = h.compare(LOOP_HEIGHT, regs={UC_X86_REG_ECX: a}, ret='st0')
        if diffs:
            return diffs
        res = h.call(LOOP_HEIGHT, regs={UC_X86_REG_ECX: a})
        want = ROWS[3][2] - ROWS[2][2]
        if res['st0'] is None or abs(res['st0'] - want) > 1e-6:
            return ['the result is %r, not %r' % (res['st0'], want)]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_loop_ends(h):
    """0x42B130 / 0x42B140 read the loop's start and end keys"""
    heap0 = h.heap_ptr
    try:
        a = h.alloc(0x240, bytes(0x240))
        h.uc.mem_write(a + 0x204, _dword(4))
        h.uc.mem_write(a + 0x208, _dword(9))
        problems = []
        for entry, want in ((LOOP_START, 4), (LOOP_END, 9)):
            diffs = h.compare(entry, regs={UC_X86_REG_ECX: a})
            if diffs:
                problems.extend(diffs)
                continue
            res = h.call(entry, regs={UC_X86_REG_ECX: a})
            if res['eax'] != want:
                problems.append('%08X gives %d' % (entry, res['eax']))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_step(h):
    """0x42B160 advances the current key in the selected direction and lets the driven object follow"""
    heap0 = h.heap_ptr
    try:
        problems = []
        # (direction byte, stopped, current index, want index, want stop flag)
        cases = ((0, 0, 2, 3, 0),                   # forwards: plain increment
                 (0, 0, 3, 3, 0),                   # forwards at +0x208: 3+1 = +0x208+1 wraps to +0x204
                 (1, 0, 2, 4, 0),                   # backwards at +0x204: jumps to +0x208+1
                 (1, 0, 3, 3, 1),                   # backwards past +0x1D4: stops at the last key
                 (1, 0, 4, 3, 1),                   # backwards already past +0x1D4: same clamp
                 (0, 1, 2, 2, 1))                   # already stopped: nothing moves
        for direction, stopped, index, want_index, want_stopped in cases:
            a, driven = _loop(h, ROWS, first=1, start=3, last=3, driven_index=index,
                              flags=direction | (stopped << 1))
            h.uc.mem_write(a + 0x1cc, _dword(index))
            sentinel = 0x0BB0BB0B
            diffs = h.compare(STEP, regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
            if diffs:
                problems.extend('dir %d stopped %d index %d: %s' % (direction, stopped, index, d)
                                for d in diffs)
                continue
            res = h.call(STEP, regs={UC_X86_REG_ECX: a, UC_X86_REG_EAX: sentinel})
            got = (_u32(h, a + 0x1cc), h.uc.mem_read(a + 0x1dc, 1)[0], _u32(h, driven + 0x1d8))
            want = (want_index, want_stopped, want_index)
            if got != want:
                problems.append('dir %d stopped %d index %d: (%d, %d, %d), not %r'
                                % (direction, stopped, index, got[0], got[1], got[2], want))
            want_eax = sentinel if stopped else want_index
            if res['eax'] != want_eax:
                problems.append('dir %d stopped %d index %d: the result is %#x, not %#x'
                                % (direction, stopped, index, res['eax'], want_eax))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_resize(h):
    """0x42B1F0 frees the old int buffer, allocates the new one and resets the count"""
    heap0 = h.heap_ptr
    try:
        vec = h.alloc(0x10, bytes(0x10))
        old = h.alloc(4, b'\x01\x02\x03\x04')
        h.uc.mem_write(vec + 4, _dword(old))
        h.uc.mem_write(vec + 8, _dword(1))
        freed = _log(h)
        new = _log(h)
        _hook(h, OP_DELETE, _arg_stub(h, freed, 0x0DE1E7E8, 0, 1))
        _hook(h, OP_NEW, _arg_stub(h, new, 0x0A11C0DE, 0, 1))
        diffs = h.compare(RESIZE, args=[6], regs={UC_X86_REG_ECX: vec}, ret=None)
        if diffs:
            return diffs
        h.call(RESIZE, args=[6], regs={UC_X86_REG_ECX: vec})
        problems = []
        if _arg(h, freed, 0) != old:
            problems.append('operator delete got %#x' % _arg(h, freed, 0))
        if _arg(h, new, 0) != 24:
            problems.append('operator new got %d bytes' % _arg(h, new, 0))
        if _u32(h, vec + 4) != 0x0A11C0DE:
            problems.append('the buffer is %#x' % _u32(h, vec + 4))
        if _u32(h, vec + 8) != 0:
            problems.append('the count is %d' % _u32(h, vec + 8))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_deleting_destructors(h):
    """0x42B240/0x42B260/0x42B330/0x42B360 set their vtable, run the base destructor and delete only with the flag"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for entry, vtable in ((DTOR_BASE, None), (DTOR_INV, VT_INV), (DTOR_CRIT, VT_OTHER), (DTOR_LOOP, VT_LOOP)):
            for freeing in (0, 1):
                obj = h.alloc(0x240, bytes(0x240))
                h.uc.mem_write(obj, _dword(0x0DEAD0B1))
                base_log = _log(h)
                del_log = _log(h)
                _hook(h, BASE_DTOR, _callee_stub(h, base_log, 0x0AD02000, 0, 0))
                _hook(h, OP_DELETE_THIS, _callee_stub(h, del_log, 0x0DE1E7E9, 0, 1))
                diffs = h.compare(entry, args=[freeing], regs={UC_X86_REG_ECX: obj})
                if diffs:
                    problems.extend('%08X freeing %d: %s' % (entry, freeing, d) for d in diffs)
                    _restore(h)
                    continue
                res = h.call(entry, args=[freeing], regs={UC_X86_REG_ECX: obj})
                if res['eax'] != obj:
                    problems.append('%08X freeing %d: the result is %#x' % (entry, freeing, res['eax']))
                want_vt = 0x0DEAD0B1 if vtable is None else vtable
                if _u32(h, obj) != want_vt:
                    problems.append('%08X freeing %d: the vtable is %#x' % (entry, freeing, _u32(h, obj)))
                if _u32(h, base_log) != obj:
                    problems.append('%08X freeing %d: the base destructor got %#x'
                                    % (entry, freeing, _u32(h, base_log)))
                if freeing:
                    if _u32(h, del_log) != obj:
                        problems.append('%08X: operator delete got %#x' % (entry, _u32(h, del_log)))
                elif _u32(h, del_log):
                    problems.append('%08X freeing 0: operator delete ran' % entry)
                _restore(h)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


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


def _driven(h, count, keys):
    obj = h.alloc(0x200, bytes(0x200))
    vt = h.alloc(0x100 * 4, bytes(0x100 * 4))
    log = _log(h, 0x100)
    for off, value in ((0xe0, count), (0xe4, keys)):
        stub = _callee_stub(h, log + off // 4, value, 0, 0)
        h.uc.mem_write(vt + off, _dword(stub))
    h.uc.mem_write(obj, _dword(vt))
    return obj


def test_other_constructor(h):
    """0x42B290 builds the base animation from the descriptor's name and range and takes +0x20 for +0x204"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for name, a, b, start in (('idle', 1, 3, 2), ('a-long-animation-name', 0, 7, 5)):
            log = _log(h)
            _hook(h, RENDER_CTOR, _callee_stub(h, log, 0x0AD18000, 12, 0))
            desc = h.alloc(0x40, bytes(0x40))
            _put_string(h, desc, name)
            h.uc.mem_write(desc + 0x1c, _dword(a))
            h.uc.mem_write(desc + 0x20, _dword(start))
            h.uc.mem_write(desc + 0x24, _dword(b))
            driven = _driven(h, 8, _keys(h, ROWS))
            anim = h.alloc(0x240, bytes(0x240))
            diffs = h.compare(CTOR_OTHER, args=[desc, driven, 0], regs={UC_X86_REG_ECX: anim})
            if diffs:
                problems.extend('%r: %s' % (name, d) for d in diffs)
                _restore(h)
                h.heap_ptr = heap0
                continue
            _restore(h)
            log = _log(h)
            _hook(h, RENDER_CTOR, _callee_stub(h, log, 0x0AD18000, 12, 0))
            desc = h.alloc(0x40, bytes(0x40))
            _put_string(h, desc, name)
            h.uc.mem_write(desc + 0x1c, _dword(a))
            h.uc.mem_write(desc + 0x20, _dword(start))
            h.uc.mem_write(desc + 0x24, _dword(b))
            driven = _driven(h, 8, _keys(h, ROWS))
            anim = h.alloc(0x240, bytes(0x240))
            res = h.call(CTOR_OTHER, args=[desc, driven, 0], regs={UC_X86_REG_ECX: anim})
            if res['fault']:
                problems.append('%r: the replacement faulted: %s' % (name, res['fault']))
            elif res['eax'] != anim:
                problems.append('%r: the constructor returned %#x' % (name, res['eax']))
            else:
                if _u32(h, anim) != VT_OTHER:
                    problems.append('%r: the vtable is %#x' % (name, _u32(h, anim)))
                if _u32(h, anim + 0x204) != start:
                    problems.append('%r: +0x204 is %d' % (name, _u32(h, anim + 0x204)))
                if _u32(h, anim + 0x1d0) != a or _u32(h, anim + 0x1d4) != min(b, 7):
                    problems.append('%r: the range is %d..%d'
                                    % (name, _u32(h, anim + 0x1d0), _u32(h, anim + 0x1d4)))
                if _u32(h, log) != anim:
                    problems.append('%r: the base constructor got %#x' % (name, _u32(h, log)))
            _restore(h)
            h.heap_ptr = heap0
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
