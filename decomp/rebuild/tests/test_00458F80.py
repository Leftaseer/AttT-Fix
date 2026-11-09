"""CGameFile::Read (0x00458F80): a buffer reads straight into it; no buffer keeps the whole file in data, sized
to the file plus a NUL unless another size was asked for, in which case the buffer is reallocated.  The file
object is a stub that only returns from its read method."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX


def _make_file(h, size):
    read = h.alloc(3, b'\xc2\x08\x00')        # slot 1: ret 8 (the buffer and its length)
    vtable = h.alloc(8, struct.pack('<II', 0, read))
    return h.alloc(0xC, struct.pack('<III', vtable, 0, size))


def _get_u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _read(h, obj, buf, n):
    diffs = h.compare(0x00458F80, args=[buf, n], regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs, None
    return [], h.call(0x00458F80, args=[buf, n], regs={UC_X86_REG_ECX: obj})


def _case(h, size, n, old_data, buf):
    obj = h.alloc(0x30, bytes(0x30))
    h.uc.mem_write(obj + 0x04, struct.pack('<I', 0x77))       # an untouched field to compare
    h.uc.mem_write(obj + 0x24, struct.pack('<I', _make_file(h, size)))
    if old_data:
        h.uc.mem_write(obj + 0x28, struct.pack('<I', old_data))
    diffs, res = _read(h, obj, buf, n)
    if diffs:
        return diffs
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    data = _get_u32(h, obj + 0x28)
    if buf:
        if data != old_data:
            return ['with a buffer, data changed from %#x to %#x' % (old_data, data)]
        return None
    if not data:
        return ['without a buffer, data was not allocated']
    if n != 0 and n != size:
        if data == old_data and old_data:
            return ['a fresh size did not reallocate the old buffer']
        if _get_u32(h, obj + 0x28) != data:
            return ['data is not the new buffer']
        return None
    # the whole-file path: the existing buffer is kept; a freshly allocated one is size + 1 bytes with a NUL
    if old_data:
        return None if data == old_data else ['the existing whole-file buffer was replaced']
    if h.uc.mem_read(data + size, 1) != b'\0':
        return ['no NUL at [size] of the whole-file buffer']
    return None


def test_cgamefile_read(h):
    old = h.alloc(32, b'o' * 32)
    buf = h.alloc(32, b'b' * 32)
    for size, n, old_data, p in ((5, 0, 0, 0),           # whole file, freshly allocated with a NUL
                                 (5, 5, 0, 0),           # as large as the file: the same whole-file path
                                 (7, 0, old, 0),         # whole file into the existing buffer
                                 (7, 7, old, 0),
                                 (5, 16, 0, 0),          # a fresh size allocates exactly it
                                 (5, 16, old, 0),        # ... and releases the old buffer first
                                 (5, 16, 0, buf),        # a caller buffer reads straight into it
                                 (5, 0, 0, buf),
                                 (0, 0, 0, 0)):          # an empty file
        diffs = _case(h, size, n, old_data, p)
        if diffs:
            return diffs
    return []
