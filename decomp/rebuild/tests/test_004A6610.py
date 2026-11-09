"""InterfaceRecord's lifetime (ctor 0x4A6610, dtor 0x4A6740) and assignment (0x4A6E90).

The record is 0x138 bytes: strings, three titled vectors, three plain vectors and the floats. The ctor leaves the
vector allocator bytes and the 0x149 floats untouched; the dtor frees the vectors and lets the strings go."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

SIZE = 0x138
TITLE_OFFSETS = (0x00, 0x1C, 0x38, 0x54, 0x80, 0xAC, 0xE8)      # name, text142[2], three titles, text147
VECTOR_OFFSETS = (0x74, 0xA0, 0xCC, 0xDC, 0x11C, 0x12C)         # begin pointers of the six vectors
ALLOCATOR_OFFSETS = (0x70, 0x9C, 0xC8, 0xD8, 0x118, 0x128)      # untouched by the ctor and dtor


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


def _init_strings(h, rec, prefix=b''):
    """give every string member a valid empty (or prefixed) value"""
    for i, off in enumerate(TITLE_OFFSETS):
        _put_str(h, rec + off, prefix + bytes([0x61 + i]))


def test_record_ctor(h):
    rec = h.alloc(SIZE, bytes([0xA5]) * SIZE)
    diffs = h.compare(0x004A6610, regs={UC_X86_REG_ECX: rec}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x004A6610, regs={UC_X86_REG_ECX: rec})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != rec:
        return ['ctor returned %#x, not this' % res['eax']]
    for off in TITLE_OFFSETS:
        if _get_str(h, rec + off) != b'':
            return ['the string at +%#X is not empty' % off]
    for off in VECTOR_OFFSETS:
        if any(_u32(h, rec + off + 4 * i) != 0 for i in range(3)):
            return ['the vector at +%#X is not nulled' % off]
    for off in ALLOCATOR_OFFSETS:
        if _u32(h, rec + off) != 0xA5A5A5A5:
            return ['the vector allocator at +%#X was touched' % off]
    if any(_u32(h, rec + 0x108 + 4 * i) != 0xA5A5A5A5 for i in range(4)):
        return ['the 0x149 floats were touched']
    return []


def test_record_dtor(h):
    rec = h.alloc(SIZE, bytes(SIZE))

    def setup(h):
        _init_strings(h, rec)

    diffs = h.compare(0x004A6740, regs={UC_X86_REG_ECX: rec}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(0x004A6740, regs={UC_X86_REG_ECX: rec})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    return []


def test_record_assign(h):
    src = h.alloc(SIZE, bytes(SIZE))
    dst = h.alloc(SIZE, bytes(SIZE))

    def setup(h):
        _init_strings(h, src, b'new-')
        _init_strings(h, dst, b'old-')
        h.uc.mem_write(src + 0x104, struct.pack('<f', 5.5))
        h.uc.mem_write(src + 0x108, struct.pack('<4f', 1.5, -2.25, 3.0, 4.0))

    diffs = h.compare(0x004A6E90, args=[src], regs={UC_X86_REG_ECX: dst}, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x004A6E90, args=[src], regs={UC_X86_REG_ECX: dst})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != dst:
        return ['assign returned %#x, not this' % res['eax']]
    for i, off in enumerate(TITLE_OFFSETS):
        want = b'new-' + bytes([0x61 + i])
        if _get_str(h, dst + off) != want:
            return ['the string at +%#X was not copied' % off]
    if struct.unpack('<f', h.uc.mem_read(dst + 0x104, 4))[0] != 5.5:
        return ['the 0x14B float was not copied']
    got = struct.unpack('<4f', h.uc.mem_read(dst + 0x108, 16))
    if got != (1.5, -2.25, 3.0, 4.0):
        return ['the 0x149 floats were not copied: %r' % (got,)]
    return []
