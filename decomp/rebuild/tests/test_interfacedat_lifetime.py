"""The interface record's element lifetime (0x420910 / 0x420F10 / 0x420F90 / 0x422B90 / 0x422BF0 / 0x422C50 / 0x497C10 /
0x423210 / 0x423260) and the clears (0x4A4C00 / 0x4A4C50 / 0x4A5270 / 0x4A52D0).

Every helper runs over an MSVC 2005 std::string field (28 bytes: allocator, 16 inline bytes, size, capacity). The
harness models the string destructor without touching the object bytes, so the checks are the offsets and the
order of the destruction calls: a wrong offset hands the destructor garbage and both runs stop differently."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

DESTROY_PAIR = 0x00420910
ITEM_E4_DTOR = 0x00420F10
ITEM_118_DTOR = 0x00420F90
DESTROY_ITEMS_4C = 0x00422B90
DESTROY_ITEMS_48 = 0x00422BF0
DESTROY_ITEMS_64 = 0x00422C50
DESTROY_VECTOR_2C = 0x00497C10
DESTROY_VECTOR_E4 = 0x00423210
DESTROY_VECTOR_118 = 0x00423260
CLEAR_VECTOR_4C = 0x004A4C00
CLEAR_VECTOR_48 = 0x004A4C50
CLEAR_COLLECTION_4C = 0x004A5270
CLEAR_COLLECTION_48 = 0x004A52D0

# the string members of each element, low to high (the destructors walk them backwards)
E4_STRINGS = (0x00, 0x28, 0x48, 0x70, 0x90, 0xAC, 0xC8)
I118_STRINGS = (0x00, 0x28, 0x48, 0x74, 0x94, 0xB4, 0xDC, 0xFC)
I4C_STRINGS = (0x00, 0x1C)
I48_STRINGS = (0x00, 0x1C)
I64_STRINGS = (0x00, 0x28, 0x48)
PAIR_STRINGS = (0x0C, 0x2C)


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _put_str(h, addr, data):
    """store an MSVC 2005 std::string: the 16 inline bytes (or a pointer), the size and the capacity"""
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


def _put_strings(h, base, offsets, prefix=b''):
    for i, off in enumerate(offsets):
        _put_str(h, base + off, prefix + bytes([0x41 + i]))


def _put_vector(h, addr, begin, end, limit, allocator=b'\x11\x22\x33\x44'):
    h.uc.mem_write(addr, allocator)
    h.uc.mem_write(addr + 4, struct.pack('<III', begin, end, limit))


def _run_regs(h, addr, this, setup):
    """run both versions from a state the setup fills; the ECX argument is the object under test"""
    return h.compare(addr, regs={UC_X86_REG_ECX: this}, setup=setup, ret=None)


def test_destroy_pair(h):
    buf = h.alloc(0x50, bytes([0xA5]) * 0x50)

    def setup(h):
        _put_strings(h, buf, PAIR_STRINGS)

    diffs = _run_regs(h, DESTROY_PAIR, buf, setup)
    if diffs:
        return diffs
    return None


def test_item_e4_dtor(h):
    item = h.alloc(0xE4, bytes([0xA5]) * 0xE4)

    def setup(h):
        _put_strings(h, item, E4_STRINGS)

    diffs = _run_regs(h, ITEM_E4_DTOR, item, setup)
    if diffs:
        return diffs
    return None


def test_item_118_dtor(h):
    item = h.alloc(0x118, bytes([0xA5]) * 0x118)

    def setup(h):
        _put_strings(h, item, I118_STRINGS)

    diffs = _run_regs(h, ITEM_118_DTOR, item, setup)
    if diffs:
        return diffs
    return None


def _range_test(h, addr, element, offsets, count=2):
    buf = h.alloc(element * count, bytes([0xA5]) * (element * count))

    def setup(h):
        for i in range(count):
            _put_strings(h, buf + i * element, offsets, bytes([0x61 + i]))

    diffs = h.compare(addr, args=[buf, buf + element * count], setup=setup, ret=None)
    if diffs:
        return diffs
    return None


def test_destroy_items_4c(h):
    return _range_test(h, DESTROY_ITEMS_4C, 0x4C, I4C_STRINGS)


def test_destroy_items_48(h):
    return _range_test(h, DESTROY_ITEMS_48, 0x48, I48_STRINGS)


def test_destroy_items_64(h):
    return _range_test(h, DESTROY_ITEMS_64, 0x64, I64_STRINGS)


def _vector_destroy_test(h, addr, element, offsets, count=2):
    elements = h.alloc(element * count, bytes([0xA5]) * (element * count))
    vector = h.alloc(0x10, bytes(0x10))

    def setup(h):
        for i in range(count):
            _put_strings(h, elements + i * element, offsets, bytes([0x41 + i]))
        _put_vector(h, vector, elements, elements + element * count, elements + element * count)

    diffs = _run_regs(h, addr, vector, setup)
    if diffs:
        return diffs
    res = h.call(addr, regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if any(_u32(h, vector + 4 + 4 * i) != 0 for i in range(3)):
        return ['the vector was not zeroed']
    return None


def test_destroy_vector_2c(h):
    return _vector_destroy_test(h, DESTROY_VECTOR_2C, 0x2C, I4C_STRINGS)


def test_destroy_vector_e4(h):
    return _vector_destroy_test(h, DESTROY_VECTOR_E4, 0xE4, E4_STRINGS)


def test_destroy_vector_118(h):
    return _vector_destroy_test(h, DESTROY_VECTOR_118, 0x118, I118_STRINGS)


def _clear_test(h, addr, element, offsets, collection, count=2):
    elements = h.alloc(element * count, bytes([0xA5]) * (element * count))
    vector = h.alloc(collection, bytes(collection))

    def setup(h):
        for i in range(count):
            _put_strings(h, elements + i * element, offsets, bytes([0x41 + i]))
        if collection == 0x2C:
            _put_str(h, vector, b'the title')
            _put_vector(h, vector + 0x1C, elements, elements + element * count,
                        elements + element * count)
        else:
            _put_vector(h, vector, elements, elements + element * count, elements + element * count)

    diffs = _run_regs(h, addr, vector, setup)
    if diffs:
        return diffs
    res = h.call(addr, regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    vec = vector + 0x1C if collection == 0x2C else vector
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if begin != elements or end != elements or limit != elements + element * count:
        return ['the vector moved: %08X %08X %08X' % (begin, end, limit)]
    if collection == 0x2C and _get_str(h, vector) != b'':
        return ['the title is not empty: %r' % _get_str(h, vector)]
    return None


def test_clear_collection_4c(h):
    return _clear_test(h, CLEAR_COLLECTION_4C, 0x4C, I4C_STRINGS, 0x2C)


def test_clear_collection_48(h):
    return _clear_test(h, CLEAR_COLLECTION_48, 0x48, I48_STRINGS, 0x2C)


def test_clear_vector_4c(h):
    return _clear_test(h, CLEAR_VECTOR_4C, 0x4C, I4C_STRINGS, 0x10)


def test_clear_vector_48(h):
    return _clear_test(h, CLEAR_VECTOR_48, 0x48, I48_STRINGS, 0x10)
