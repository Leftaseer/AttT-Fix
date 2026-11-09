"""The interface record's copy constructor (0x423AE0) and the copies it makes: the vectors of every element type
(0x4232B0 / 0x423380 / 0x423490 / 0x423560 / 0x423630 / 0x423720) and the titled collections (0x423810 /
0x4238F0 / 0x4239D0).

A copy constructs into raw storage: the strings copy themselves, the vectors get a fresh buffer of the source's
size and their elements are copy-constructed into it.  The vectors' allocator dwords are never written, so they
keep whatever the destination held."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

COPY_RECORD = 0x00423AE0
COPY_ITEMS_4C = 0x004232B0
COPY_ITEMS_48 = 0x00423380
COPY_ITEMS_2C = 0x00423490
COPY_ITEMS_64 = 0x00423560
COPY_ITEMS_E4 = 0x00423630
COPY_ITEMS_118 = 0x00423720
COPY_COLLECTION_4C = 0x00423810
COPY_COLLECTION_48 = 0x004238F0
COPY_COLLECTION_2C = 0x004239D0

RECORD_SIZE = 0x138

# (element size, string offsets) of the interface items
ELEMENTS = {
    0x4C: (0x00, 0x1C),
    0x48: (0x00, 0x1C),
    0x2C: (0x00,),
    0x64: (0x00, 0x28, 0x48),
    0xE4: (0x00, 0x28, 0x48, 0x70, 0x90, 0xAC, 0xC8),
    0x118: (0x00, 0x28, 0x48, 0x74, 0x94, 0xB4, 0xDC, 0xFC),
}

# the record's vector parts: items143, items144, items145, items146, items14A, items14C
RECORD_VECTORS = ((0x70, 0x4C), (0x9C, 0x48), (0xC8, 0x2C), (0xD8, 0x64), (0x118, 0xE4), (0x128, 0x118))
# the record's strings: name, text142[2], the three titles, text147
RECORD_STRINGS = (0x00, 0x1C, 0x38, 0x54, 0x80, 0xAC, 0xE8)


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
    ptr = addr + 4 if cap < 16 else _u32(h, addr + 4)
    return bytes(h.uc.mem_read(ptr, size))


def _element_strings(tag, size):
    return [tag + b'%d' % i for i in range(len(ELEMENTS[size]))]


def _put_element(h, addr, size, tag, fill=0x22, long_at=None):
    """an element with the given byte fill and its strings; long_at is the string index made longer than inline"""
    h.uc.mem_write(addr, bytes([fill]) * size)
    for i, off in enumerate(ELEMENTS[size]):
        data = tag + b'%d' % i
        if long_at == i:
            data = b'a long %s string' % data
        _put_str(h, addr + off, data)


def _check_element(h, addr, size, tag, long_at=None):
    for i, off in enumerate(ELEMENTS[size]):
        want = tag + b'%d' % i
        if long_at == i:
            want = b'a long %s string' % want
        if _get_str(h, addr + off) != want:
            return 'the string at +%02X is %r, wanted %r' % (off, _get_str(h, addr + off), want)
    return None


def _put_vector(h, vector, size, tags, fill=0x22):
    """a vector of elements at the vector part (allocator, begin, end, limit), its buffer allocated in the heap"""
    buffer = h.alloc(size * len(tags), bytes([fill]) * (size * len(tags)))
    for i, tag in enumerate(tags):
        _put_element(h, buffer + i * size, size, tag, fill, 0 if size == 0xE4 and i == 0 else None)
    h.uc.mem_write(vector, struct.pack('<III', buffer, buffer + size * len(tags), buffer + size * len(tags)))
    return buffer


def _check_vector(h, vector, size, tags):
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vector, 12))
    if end - begin != size * len(tags):
        return 'the vector holds %d bytes, wanted %d' % (end - begin, size * len(tags))
    if limit - begin != size * len(tags):
        return 'the vector capacity is %d bytes, wanted %d' % (limit - begin, size * len(tags))
    for i, tag in enumerate(tags):
        diffs = _check_element(h, begin + i * size, size, tag, 0 if size == 0xE4 and i == 0 else None)
        if diffs:
            return 'element %d: %s' % (i, diffs)
    return None


def test_copy_items_4c(h):
    """0x4232B0 copies three 0x4C elements into a fresh buffer; the allocator dword stays."""
    other = h.alloc(0x10, struct.pack('<III', 0, 0, 0))
    vector = h.alloc(0x10, bytes([0x5A]) * 0x10)
    tags = (b'a', b'b', b'c')
    state = {}

    def setup(h):
        h.uc.mem_write(other, struct.pack('<I', 0x77777777))
        _put_vector(h, other + 4, 0x4C, tags)
        state['heap'] = h.heap_ptr

    diffs = h.compare(COPY_ITEMS_4C, args=[other], regs={UC_X86_REG_ECX: vector}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(COPY_ITEMS_4C, args=[other], regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != vector:
        return ['returned %#x, not the vector' % res['eax']]
    if _u32(h, vector) != 0x5A5A5A5A:
        return ['the allocator dword was written']
    diffs = _check_vector(h, vector + 4, 0x4C, tags)
    return [diffs] if diffs else []


def test_copy_items_48(h):
    """0x423380 copies 0x48 elements."""
    other = h.alloc(0x10, struct.pack('<III', 0, 0, 0))
    vector = h.alloc(0x10, bytes([0x5A]) * 0x10)
    tags = (b'x', b'y')
    state = {}

    def setup(h):
        h.uc.mem_write(other, struct.pack('<I', 0x77777777))
        _put_vector(h, other + 4, 0x48, tags)
        state['heap'] = h.heap_ptr

    diffs = h.compare(COPY_ITEMS_48, args=[other], regs={UC_X86_REG_ECX: vector}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(COPY_ITEMS_48, args=[other], regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, vector) != 0x5A5A5A5A:
        return ['the allocator dword was written']
    diffs = _check_vector(h, vector + 4, 0x48, tags)
    return [diffs] if diffs else []


def test_copy_items_2c(h):
    """0x423490 copies 0x2C elements."""
    other = h.alloc(0x10, struct.pack('<III', 0, 0, 0))
    vector = h.alloc(0x10, bytes([0x5A]) * 0x10)
    tags = (b'p', b'q', b'r', b's')
    state = {}

    def setup(h):
        h.uc.mem_write(other, struct.pack('<I', 0x77777777))
        _put_vector(h, other + 4, 0x2C, tags)
        state['heap'] = h.heap_ptr

    diffs = h.compare(COPY_ITEMS_2C, args=[other], regs={UC_X86_REG_ECX: vector}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(COPY_ITEMS_2C, args=[other], regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, vector) != 0x5A5A5A5A:
        return ['the allocator dword was written']
    diffs = _check_vector(h, vector + 4, 0x2C, tags)
    return [diffs] if diffs else []


def test_copy_items_64(h):
    """0x423560 copies 0x64 elements, whose flags are lone bytes (the padding stays the destination's)."""
    other = h.alloc(0x10, struct.pack('<III', 0, 0, 0))
    vector = h.alloc(0x10, bytes([0x5A]) * 0x10)
    tags = (b'm', b'n')
    state = {}

    def setup(h):
        h.uc.mem_write(other, struct.pack('<I', 0x77777777))
        _put_vector(h, other + 4, 0x64, tags)
        state['heap'] = h.heap_ptr

    diffs = h.compare(COPY_ITEMS_64, args=[other], regs={UC_X86_REG_ECX: vector}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(COPY_ITEMS_64, args=[other], regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, vector) != 0x5A5A5A5A:
        return ['the allocator dword was written']
    diffs = _check_vector(h, vector + 4, 0x64, tags)
    if diffs:
        return [diffs]
    begin = _u32(h, vector + 4)
    for i in range(len(tags)):
        if h.uc.mem_read(begin + i * 0x64 + 0x25, 3) != b'\0\0\0':
            return ['the flag padding of element %d was written' % i]
    return []


def test_copy_items_e4(h):
    """0x423630 copies 0xE4 elements, one of whose strings is long enough to allocate."""
    other = h.alloc(0x10, struct.pack('<III', 0, 0, 0))
    vector = h.alloc(0x10, bytes([0x5A]) * 0x10)
    tags = (b'u',)
    state = {}

    def setup(h):
        h.uc.mem_write(other, struct.pack('<I', 0x77777777))
        _put_vector(h, other + 4, 0xE4, tags)
        state['heap'] = h.heap_ptr

    diffs = h.compare(COPY_ITEMS_E4, args=[other], regs={UC_X86_REG_ECX: vector}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(COPY_ITEMS_E4, args=[other], regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, vector) != 0x5A5A5A5A:
        return ['the allocator dword was written']
    diffs = _check_vector(h, vector + 4, 0xE4, tags)
    return [diffs] if diffs else []


def test_copy_items_118(h):
    """0x423720 copies 0x118 elements."""
    other = h.alloc(0x10, struct.pack('<III', 0, 0, 0))
    vector = h.alloc(0x10, bytes([0x5A]) * 0x10)
    tags = (b'v', b'w')
    state = {}

    def setup(h):
        h.uc.mem_write(other, struct.pack('<I', 0x77777777))
        _put_vector(h, other + 4, 0x118, tags)
        state['heap'] = h.heap_ptr

    diffs = h.compare(COPY_ITEMS_118, args=[other], regs={UC_X86_REG_ECX: vector}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(COPY_ITEMS_118, args=[other], regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, vector) != 0x5A5A5A5A:
        return ['the allocator dword was written']
    diffs = _check_vector(h, vector + 4, 0x118, tags)
    return [diffs] if diffs else []


def _collection_case(h, entry, size, tag):
    other = h.alloc(0x2C, bytes(0x2C))
    collection = h.alloc(0x2C, bytes([0x5A]) * 0x2C)
    tags = (tag, tag + b'2')
    state = {}

    def setup(h):
        _put_str(h, other, b'the title')
        h.uc.mem_write(other + 0x1C, struct.pack('<I', 0x77777777))
        _put_vector(h, other + 0x20, size, tags)
        state['heap'] = h.heap_ptr

    diffs = h.compare(entry, args=[other], regs={UC_X86_REG_ECX: collection}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(entry, args=[other], regs={UC_X86_REG_ECX: collection})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != collection:
        return ['returned %#x, not the collection' % res['eax']]
    if _get_str(h, collection) != b'the title':
        return ['the title is %r' % _get_str(h, collection)]
    if _u32(h, collection + 0x1C) != 0x5A5A5A5A:
        return ['the allocator dword was written']
    diffs = _check_vector(h, collection + 0x20, size, tags)
    return [diffs] if diffs else []


def test_copy_collection_4c(h):
    """0x423810 copies a 0x143 collection: its title, then its 0x4C elements."""
    return _collection_case(h, COPY_COLLECTION_4C, 0x4C, b'c')


def test_copy_collection_48(h):
    """0x4238F0 copies a 0x144 collection."""
    return _collection_case(h, COPY_COLLECTION_48, 0x48, b'd')


def test_copy_collection_2c(h):
    """0x4239D0 copies a 0x145 collection."""
    return _collection_case(h, COPY_COLLECTION_2C, 0x2C, b'e')


def test_copy_record(h):
    """0x423AE0 copies a whole record: its seven strings, six populated vectors and the numbers, while the
    destination's six vector allocator dwords keep their bytes."""
    source = h.alloc(RECORD_SIZE, bytes(RECORD_SIZE))
    record = h.alloc(RECORD_SIZE, bytes([0x5A]) * RECORD_SIZE)
    state = {}
    # per-vector tags, one per element
    tags = {
        0x4C: (b'i', b'j'),
        0x48: (b'k',),
        0x2C: (b'l', b'm'),
        0x64: (b'n',),
        0xE4: (b'o',),
        0x118: (b'p',),
    }

    def setup(h):
        h.uc.mem_write(source, bytes([0x11]) * RECORD_SIZE)
        strings = (b'main-record', b'first-text', b'a longer second text', b'items143', b'items144',
                   b'items145', b'tail')
        for off, data in zip(RECORD_STRINGS, strings):
            _put_str(h, source + off, data)
        for vector, size in RECORD_VECTORS:
            h.uc.mem_write(source + vector, struct.pack('<I', 0x77777777))
            _put_vector(h, source + vector + 4, size, tags[size])
        h.uc.mem_write(source + 0x104, struct.pack('<f', 7.5))
        h.uc.mem_write(source + 0x108, struct.pack('<4f', 1.5, -2.25, 3.0, 4.0))
        state['heap'] = h.heap_ptr

    diffs = h.compare(COPY_RECORD, args=[source], regs={UC_X86_REG_ECX: record}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(COPY_RECORD, args=[source], regs={UC_X86_REG_ECX: record})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != record:
        return ['returned %#x, not the record' % res['eax']]
    strings = (b'main-record', b'first-text', b'a longer second text', b'items143', b'items144',
               b'items145', b'tail')
    for off, data in zip(RECORD_STRINGS, strings):
        if _get_str(h, record + off) != data:
            return ['the string at +%02X is %r, wanted %r' % (off, _get_str(h, record + off), data)]
    for vector, size in RECORD_VECTORS:
        if _u32(h, record + vector) != 0x5A5A5A5A:
            return ['the allocator dword of +%02X was written' % vector]
        diffs = _check_vector(h, record + vector + 4, size, tags[size])
        if diffs:
            return ['the vector at +%02X: %s' % (vector, diffs)]
    if struct.unpack('<f', h.uc.mem_read(record + 0x104, 4))[0] != 7.5:
        return ['the 0x14B float was not copied']
    if struct.unpack('<4f', h.uc.mem_read(record + 0x108, 16)) != (1.5, -2.25, 3.0, 4.0):
        return ['the 0x149 floats were not copied']
    return []
