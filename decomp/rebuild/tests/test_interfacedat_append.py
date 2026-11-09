"""The interface vectors' append, one instantiation per element type (0x4A54F0 / 0x4A5710 / 0x4A5930 / 0x4A6B70 /
0x4A5BB0 / 0x4A5DF0).

A push_back copies the item after the last element.  With room it constructs in place; an empty or full vector
allocates a new buffer half again as large (but at least one more element), copies the elements and the item,
destroys the old ones and releases the old buffer.  The item is copied once before the buffer is allocated, so
long strings allocate in the same order as the original."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

CASES = (
    (0x004A54F0, 0x4C, (0x00, 0x1C)),
    (0x004A5710, 0x48, (0x00, 0x1C)),
    (0x004A5930, 0x2C, (0x00,)),
    (0x004A6B70, 0x64, (0x00, 0x28, 0x48)),
    (0x004A5BB0, 0xE4, (0x00, 0x28, 0x48, 0x70, 0x90, 0xAC, 0xC8)),
    (0x004A5DF0, 0x118, (0x00, 0x28, 0x48, 0x74, 0x94, 0xB4, 0xDC, 0xFC)),
)


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


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


def _put_element(h, base, offsets, prefix):
    for i, off in enumerate(offsets):
        _put_str(h, base + off, prefix + bytes([0x41 + i]))


def _put_vector(h, addr, begin, end, limit):
    h.uc.mem_write(addr, b'\x11\x22\x33\x44')
    h.uc.mem_write(addr + 4, struct.pack('<III', begin, end, limit))


def _run(h, addr, element, offsets, mode, long_strings=False):
    item = h.alloc(element, bytes([0xA5]) * element)
    rows = h.alloc(element * 4, bytes([0xA5]) * (element * 4))
    vector = h.alloc(0x10, bytes(0x10))
    prefix = b'a long item string' if long_strings else b'item'

    def setup(h):
        _put_element(h, item, offsets, prefix)
        if mode == 'room':
            _put_element(h, rows, offsets, b'old')
            _put_vector(h, vector, rows, rows + element, rows + 2 * element)
        elif mode == 'grow':
            _put_element(h, rows, offsets, b'old')
            _put_vector(h, vector, rows, rows + element, rows + element)
        elif mode == 'half':
            for i, old_prefix in enumerate((b'old', b'mid', b'mi2', b'mi3')):
                _put_element(h, rows + i * element, offsets, old_prefix)
            _put_vector(h, vector, rows, rows + 4 * element, rows + 4 * element)
        else:
            _put_vector(h, vector, 0, 0, 0)

    diffs = h.compare(addr, args=[item], regs={UC_X86_REG_ECX: vector}, setup=setup, ret=None)
    if diffs:
        return diffs

    res = h.call(addr, args=[item], regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]

    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vector + 4, 12))
    if mode == 'room':
        if (begin, end, limit) != (rows, rows + 2 * element, rows + 2 * element):
            return ['the vector moved: %08X %08X %08X' % (begin, end, limit)]
    elif mode == 'grow':
        if begin == rows or end - begin != 2 * element or limit - begin != 2 * element:
            return ['the vector grew wrong: %08X %08X %08X' % (begin, end, limit)]
    elif mode == 'half':
        if begin == rows or end - begin != 5 * element or limit - begin != 6 * element:
            return ['the vector grew wrong: %08X %08X %08X' % (begin, end, limit)]
    elif not begin or end - begin != element or limit - begin != element:
        return ['the empty vector did not take one element: %08X %08X %08X' % (begin, end, limit)]

    new = end - element
    for i, off in enumerate(offsets):
        want = prefix + bytes([0x41 + i])
        if _get_str(h, new + off) != want:
            return ['the appended element has %r, wanted %r' % (_get_str(h, new + off), want)]
        if _get_str(h, item + off) != want:
            return ['the source item changed: %r' % _get_str(h, item + off)]
    moved = {'room': 1, 'grow': 1, 'half': 4}.get(mode, 0)
    names = (b'old', b'mid', b'mi2', b'mi3')
    for i in range(moved):
        for j, off in enumerate(offsets):
            want = names[i] + bytes([0x41 + j])
            if _get_str(h, begin + i * element + off) != want:
                return ['the moved element %d has %r' % (i, _get_str(h, begin + i * element + off))]
    return None


def test_copy_item_4c(h):
    src = h.alloc(0x4C, bytes([0xA5]) * 0x4C)
    dst = h.alloc(0x4C, bytes([0x5A]) * 0x4C)

    def setup(h):
        _put_element(h, src, (0x00, 0x1C), b'item')
        h.uc.mem_write(src + 0x38, b'\x33')
        for off in (0x3C, 0x40, 0x44, 0x48):
            h.uc.mem_write(src + off, struct.pack('<f', off + 0.5))

    diffs = h.compare(0x00421020, args=[src], regs={UC_X86_REG_ECX: dst}, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00421020, args=[src], regs={UC_X86_REG_ECX: dst})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    padding = bytes(h.uc.mem_read(dst + 0x39, 3))
    if padding != b'\x5a\x5a\x5a':
        return ['the flag padding changed: %s' % padding.hex()]
    if h.uc.mem_read(dst + 0x38, 1) != b'\x33':
        return ['the flag is not copied']
    for off in (0x3C, 0x40, 0x44, 0x48):
        if h.uc.mem_read(dst + off, 4) != struct.pack('<f', off + 0.5):
            return ['the number at %02X is not copied' % off]
    return None


def test_push_item_4c(h):
    return _run(h, 0x004A54F0, 0x4C, (0x00, 0x1C), 'grow')


def test_push_item_48(h):
    return _run(h, 0x004A5710, 0x48, (0x00, 0x1C), 'grow')


def test_push_item_2c(h):
    return _run(h, 0x004A5930, 0x2C, (0x00,), 'grow')


def test_push_item_64(h):
    return _run(h, 0x004A6B70, 0x64, (0x00, 0x28, 0x48), 'grow')


def test_push_item_e4(h):
    return _run(h, 0x004A5BB0, 0xE4, (0x00, 0x28, 0x48, 0x70, 0x90, 0xAC, 0xC8), 'grow')


def test_push_item_118(h):
    return _run(h, 0x004A5DF0, 0x118, (0x00, 0x28, 0x48, 0x74, 0x94, 0xB4, 0xDC, 0xFC), 'grow')


def test_push_into_empty(h):
    for addr, element, offsets in CASES:
        diffs = _run(h, addr, element, offsets, 'empty')
        if diffs:
            return ['%08X: %s' % (addr, d) for d in diffs]
    return None


def test_push_with_room(h):
    for addr, element, offsets in CASES:
        diffs = _run(h, addr, element, offsets, 'room')
        if diffs:
            return ['%08X: %s' % (addr, d) for d in diffs]
    return None


def test_push_half_growth(h):
    for addr, element, offsets in CASES:
        diffs = _run(h, addr, element, offsets, 'half')
        if diffs:
            return ['%08X: %s' % (addr, d) for d in diffs]
    return None


def test_push_long_strings(h):
    for addr, element, offsets in CASES:
        diffs = _run(h, addr, element, offsets, 'grow', long_strings=True)
        if diffs:
            return ['%08X: %s' % (addr, d) for d in diffs]
    return None
