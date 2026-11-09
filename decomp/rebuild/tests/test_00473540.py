"""CMapHeight destructor (0x00473540): the rows are freed bottom-up through operator delete[] and the object drops
to the CSingleton vtable; with no rows nothing is freed.  The import thunk 0x005E3EBA jumps through the same IAT
slot as the delete[] the rebuilt C++ calls, so pointing the slot at a recorder catches both paths."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

DELETE = 0x005E3EBA


def _patch_import(h, entry, body):
    """point the IAT slot the thunk at `entry` jumps through at `body`"""
    assert h.uc.mem_read(entry, 2) == b'\xff\x25'
    slot = struct.unpack('<I', h.uc.mem_read(entry + 2, 4))[0]
    saved = bytes(h.uc.mem_read(slot, 4))
    h.uc.mem_write(slot, struct.pack('<I', body))
    return slot, saved


def _recorder(h):
    """appends its argument to an array and counts it (cdecl: the caller pops the argument)"""
    count = h.alloc(4, bytes(4))
    array = h.alloc(64, bytes(64))
    body = h.alloc(32, bytes(32))
    h.uc.mem_write(body, b'\x8b\x44\x24\x04'                              # mov eax, [esp+4]
                        + b'\x8b\x0d' + struct.pack('<I', count)          # mov ecx, [count]
                        + b'\x89\x04\x8d' + struct.pack('<I', array)      # mov [array+ecx*4], eax
                        + b'\xff\x05' + struct.pack('<I', count)          # inc dword [count]
                        + b'\xc3')
    return count, array, body


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _exercise(h, count, obj):
    diffs = h.compare(0x00473540, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    h.uc.mem_write(count, bytes(4))
    res = h.call(0x00473540, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, obj) != 0x0060E75C:
        return ['final vtable %08X' % _u32(h, obj)]
    return None


def test_map_height_dtor(h):
    count, array, body = _recorder(h)
    slot, saved = _patch_import(h, DELETE, body)
    try:
        # no rows: nothing is freed
        obj = h.alloc(0x30, bytes(0x30))
        h.uc.mem_write(obj, struct.pack('<I', 0x0060E764))
        diffs = _exercise(h, count, obj)
        if diffs:
            return diffs
        if _u32(h, count) != 0:
            return ['freed %d blocks without rows' % _u32(h, count)]
        if _u32(h, obj + 4) != 0:
            return ['rows changed without rows']

        # three rows: freed in order, then the row array itself
        obj = h.alloc(0x30, bytes(0x30))
        rows = h.alloc(3 * 4, bytes(12))
        row = [h.alloc(4, bytes(4)) for _ in range(3)]
        h.uc.mem_write(rows, struct.pack('<III', *row))
        h.uc.mem_write(obj, struct.pack('<III', 0x0060E764, rows, 3))
        diffs = _exercise(h, count, obj)
        if diffs:
            return diffs
        if _u32(h, count) != 4:
            return ['freed %d blocks, want 4' % _u32(h, count)]
        got = list(struct.unpack('<4I', h.uc.mem_read(array, 16)))
        if got != row + [rows]:
            return ['freed pointers %s, want %s' % (got, row + [rows])]
        return []
    finally:
        h.uc.mem_write(slot, saved)
