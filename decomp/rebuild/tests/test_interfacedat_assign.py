"""The interface vectors' copy assignment, one instantiation per element type (0x4A5360 / 0x4A5580 / 0x4A57A0 /
0x4A69E0 / 0x4A5A10 / 0x4A5C50).

An empty source clears this vector; a source no longer than this one is assigned over and the tail destroyed; a
longer source that fits the spare capacity is assigned over and the rest constructed at the end; otherwise the
old buffer goes and one of exactly the source's size takes its place."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

# (address, element size, string offsets, (flag offset, width) pairs)
CASES = (
    (0x004A5360, 0x4C, (0x00, 0x1C), ((0x38, 1),)),
    (0x004A5580, 0x48, (0x00, 0x1C), ()),
    (0x004A57A0, 0x2C, (0x00,), ()),
    (0x004A69E0, 0x64, (0x00, 0x28, 0x48), ((0x24, 4),)),
    (0x004A5A10, 0xE4, (0x00, 0x28, 0x48, 0x70, 0x90, 0xAC, 0xC8), ((0x24, 1), (0x6C, 1))),
    (0x004A5C50, 0x118, (0x00, 0x28, 0x48, 0x74, 0x94, 0xB4, 0xDC, 0xFC),
     ((0x24, 1), (0x70, 1), (0xD8, 1))),
)


def _put_str(h, addr, data):
    if len(data) < 16:
        h.uc.mem_write(addr + 4, data + b'\0' * (16 - len(data)))
        cap = 15
    else:
        block = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', block))
        cap = len(data)
    h.uc.mem_write(addr + 20, struct.pack('<II', len(data), cap))


def _get_str(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    ptr = addr + 4 if cap < 16 else struct.unpack('<I', h.uc.mem_read(addr + 4, 4))[0]
    return bytes(h.uc.mem_read(ptr, size))


def _put_element(h, base, element, strings, flags, prefix, fill):
    h.uc.mem_write(base, bytes([fill]) * element)
    for i, off in enumerate(strings):
        _put_str(h, base + off, prefix + bytes([0x41 + i]))
    for off, width in flags:
        h.uc.mem_write(base + off, bytes([0x33 + (off & 1)] * width))


def _put_vector(h, addr, begin, end, limit):
    h.uc.mem_write(addr, b'\x11\x22\x33\x44')
    h.uc.mem_write(addr + 4, struct.pack('<III', begin, end, limit))


def _check_element(h, base, strings, flags, prefix):
    for i, off in enumerate(strings):
        want = prefix + bytes([0x41 + i])
        if _get_str(h, base + off) != want:
            return 'the string at +%02X is %r, wanted %r' % (off, _get_str(h, base + off), want)
    for off, width in flags:
        if h.uc.mem_read(base + off, 1) != bytes([0x33 + (off & 1)]):
            return 'the flag at +%02X was not copied' % off
    return None


def _run(h, addr, element, strings, flags, mode, long_strings=False):
    src_count = {'empty': 0, 'eq': 2, 'shrink': 1}.get(mode, 3)
    dst_count, dst_capacity = {'empty': (2, 3), 'shrink': (3, 5), 'tail': (1, 4),
                               'grow': (2, 2), 'bad': (0, 0), 'eq': (2, 3)}[mode]
    srcbuf = h.alloc(element * 3, bytes([0xA5]) * (element * 3))
    dstbuf = h.alloc(element * max(dst_capacity, 1), bytes([0x5A]) * (element * max(dst_capacity, 1)))
    source = h.alloc(0x10, bytes(0x10))
    vector = h.alloc(0x10, bytes(0x10))
    new_prefix = b'a long element string ' if long_strings else b'n'
    old_prefix = b'o'
    state = {}

    def setup(h):
        for i in range(src_count):
            _put_element(h, srcbuf + i * element, element, strings, flags, new_prefix + b'%d' % i, 0xA5)
        for i in range(dst_count):
            _put_element(h, dstbuf + i * element, element, strings, flags, old_prefix + b'%d' % i, 0x5A)
        _put_vector(h, source, srcbuf if src_count else 0, srcbuf + src_count * element if src_count else 0,
                    srcbuf + src_count * element if src_count else 0)
        if mode == 'bad':
            _put_vector(h, vector, 0, 0, 0)
        else:
            _put_vector(h, vector, dstbuf, dstbuf + dst_count * element, dstbuf + dst_capacity * element)
        state['heap'] = h.heap_ptr

    other = vector if mode == 'eq' else source
    diffs = h.compare(addr, args=[other], regs={UC_X86_REG_ECX: vector}, setup=setup, ret='eax')
    if diffs:
        return diffs

    h.heap_ptr = state['heap']   # the compare left the memory as setup made it but the pointer before it
    res = h.call(addr, args=[other], regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != vector:
        return ['the assignment returned %#x, not this' % res['eax']]

    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vector + 4, 12))
    want_size, want_capacity = {
        'empty': (0, 3), 'shrink': (1, 5), 'tail': (3, 4), 'grow': (3, 3), 'bad': (3, 3), 'eq': (2, 3)
    }[mode]
    if end - begin != want_size * element:
        return ['the size is %d elements, wanted %d' % ((end - begin) // element, want_size)]
    if limit - begin != want_capacity * element:
        return ['the capacity is %d elements, wanted %d' % ((limit - begin) // element, want_capacity)]
    if mode in ('shrink', 'tail', 'empty', 'eq') and begin != dstbuf:
        return ['a fitting assignment moved the buffer']
    if mode in ('grow', 'bad') and begin == dstbuf:
        return ['a too-large assignment kept the old buffer']

    want_prefix = old_prefix if mode == 'eq' else new_prefix
    for i in range(want_size):
        diffs = _check_element(h, begin + i * element, strings, flags, want_prefix + b'%d' % i)
        if diffs:
            return ['element %d: %s' % (i, diffs)]
    return None


def _each(h, mode, long_strings=False):
    for addr, element, strings, flags in CASES:
        diffs = _run(h, addr, element, strings, flags, mode, long_strings)
        if diffs:
            return ['%08X: %s' % (addr, d) for d in diffs]
    return None


def test_assign_empty_source(h):
    return _each(h, 'empty')


def test_assign_shorter(h):
    return _each(h, 'shrink')


def test_assign_tail(h):
    return _each(h, 'tail')


def test_assign_grow(h):
    return _each(h, 'grow')


def test_assign_into_empty(h):
    return _each(h, 'bad')


def test_assign_self(h):
    return _each(h, 'eq')


def test_assign_long_strings(h):
    return _each(h, 'grow', long_strings=True)
