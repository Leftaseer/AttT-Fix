"""0x42B390 collects the key indices a loop animation visits over a span of time into an int buffer.

The buffer type has its data pointer at +4 and its used count at +8; the function resizes it first (0x42B1F0)
and then appends the keys. `*scale` is the speed factor that makes the run last the requested time."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

BUILD = 0x0042B390


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _fbits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def _layout(h, first=1, last=6, start=2, end=4, bottom=0.2, top=0.3, step=0.25):
    a = h.alloc(0x240, bytes(0x240))
    vec = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(a + 0x1d0, _dword(first))
    h.uc.mem_write(a + 0x1d4, _dword(last))
    h.uc.mem_write(a + 0x204, _dword(start))
    h.uc.mem_write(a + 0x208, _dword(end))
    h.uc.mem_write(a + 0x210, struct.pack('<f', bottom))
    h.uc.mem_write(a + 0x214, struct.pack('<f', top))
    h.uc.mem_write(a + 0x218, struct.pack('<f', step))
    return a, vec


def _keys(h, vec):
    data = _u32(h, vec + 4)
    count = _u32(h, vec + 8)
    return [_u32(h, data + 4 * i) for i in range(count)]


def _build(h, a, vec, time):
    """run the original and the replacement on the same state; return (problems, keys, scale) of the replacement"""
    scale = h.alloc(4, bytes(4))
    diffs = h.compare(BUILD, args=[vec, _fbits(time), scale], regs={UC_X86_REG_ECX: a}, ret='eax')
    if diffs:
        return diffs, None, None
    h.uc.mem_write(scale, bytes(4))
    res = h.call(BUILD, args=[vec, _fbits(time), scale], regs={UC_X86_REG_ECX: a})
    problems = []
    if res['fault']:
        problems.append(res['fault'])
    return problems, _keys(h, vec), _f32(h, scale)


def test_before_one_cycle(h):
    """a time below the cycle height never enters the repeat branch"""
    heap0 = h.heap_ptr
    try:
        a, vec = _layout(h)
        problems, keys, scale = _build(h, a, vec, 0.4)
        if problems:
            return problems
        if keys != [1, 5, 6]:
            return ['the key list is %r' % (keys,)]
        if abs(scale - 0.8) > 1e-6:
            return ['the scale is %r' % scale]
        return None
    finally:
        h.heap_ptr = heap0


def test_one_and_a_half_cycles(h):
    """a time of exactly two step heights plus the first step rounds up to the second cycle boundary"""
    heap0 = h.heap_ptr
    try:
        a, vec = _layout(h)
        problems, keys, scale = _build(h, a, vec, 1.0)
        if problems:
            return problems
        if keys != [1, 2, 3, 4, 2, 3, 4, 5, 6]:
            return ['the key list is %r' % (keys,)]
        if abs(scale - 1.0) > 1e-6:
            return ['the scale is %r' % scale]
        return None
    finally:
        h.heap_ptr = heap0


def test_exact_total(h):
    """time == the cycle height still takes the single-cycle branch (the compare is a strict one)"""
    heap0 = h.heap_ptr
    try:
        a, vec = _layout(h)
        problems, keys, scale = _build(h, a, vec, 0.5)
        if problems:
            return problems
        if keys != [1, 5, 6]:
            return ['the key list is %r' % (keys,)]
        if abs(scale - 1.0) > 1e-6:
            return ['the scale is %r' % scale]
        return None
    finally:
        h.heap_ptr = heap0


def test_two_cycles(h):
    """a time near the lower key of the second cycle keeps the truncated cycle count"""
    heap0 = h.heap_ptr
    try:
        a, vec = _layout(h)
        problems, keys, scale = _build(h, a, vec, 1.1)
        if problems:
            return problems
        if keys != [1, 2, 3, 4, 2, 3, 4, 5, 6]:
            return ['the key list is %r' % (keys,)]
        if abs(scale - 1.1) > 1e-6:
            return ['the scale is %r' % scale]
        return None
    finally:
        h.heap_ptr = heap0


def test_rounds_up_to_the_next_cycle(h):
    """a time closer to the next cycle boundary takes one more repetition"""
    heap0 = h.heap_ptr
    try:
        a, vec = _layout(h)
        problems, keys, scale = _build(h, a, vec, 1.13)
        if problems:
            return problems
        if keys != [1, 2, 3, 4, 2, 3, 4, 2, 3, 4, 5, 6]:
            return ['the key list is %r' % (keys,)]
        if abs(scale - 1.13 / 1.25) > 1e-6:
            return ['the scale is %r' % scale]
        return None
    finally:
        h.heap_ptr = heap0


def test_zero_cycles(h):
    """a time past the total but within the first step repeats nothing"""
    heap0 = h.heap_ptr
    try:
        a, vec = _layout(h, step=0.4)
        problems, keys, scale = _build(h, a, vec, 0.7)
        if problems:
            return problems
        if keys != [1, 5, 6]:
            return ['the key list is %r' % (keys,)]
        if abs(scale - 1.4) > 1e-6:
            return ['the scale is %r' % scale]
        return None
    finally:
        h.heap_ptr = heap0


def test_loop_covers_the_whole_list(h):
    """first == loop start and loop end == last leave nothing on either side of the loop"""
    heap0 = h.heap_ptr
    try:
        a, vec = _layout(h, first=2, start=2, last=4, end=4)
        problems, keys, scale = _build(h, a, vec, 1.1)
        if problems:
            return problems
        if keys != [2, 3, 4, 2, 3, 4]:
            return ['the key list is %r' % (keys,)]
        return None
    finally:
        h.heap_ptr = heap0


def test_result_is_the_next_index(h):
    """the result is the index one past the last appended key (end+1 when the tail is empty)"""
    heap0 = h.heap_ptr
    try:
        a, vec = _layout(h, first=1, last=4, start=2, end=4)
        scale = h.alloc(4, bytes(4))
        diffs = h.compare(BUILD, args=[vec, _fbits(0.25), scale], regs={UC_X86_REG_ECX: a}, ret='eax')
        if diffs:
            return diffs
        res = h.call(BUILD, args=[vec, _fbits(0.25), scale], regs={UC_X86_REG_ECX: a})
        if res['eax'] != 5:
            return ['the result is %d' % res['eax']]
        a2, vec2 = _layout(h, first=1, last=6, start=2, end=4)
        scale2 = h.alloc(4, bytes(4))
        res = h.call(BUILD, args=[vec2, _fbits(0.25), scale2], regs={UC_X86_REG_ECX: a2})
        if res['eax'] != 7:
            return ['the result with a tail is %d' % res['eax']]
        return None
    finally:
        h.heap_ptr = heap0
