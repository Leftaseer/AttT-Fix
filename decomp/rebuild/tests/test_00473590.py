"""CMapHeight scalar deleting destructor (0x00473590): the destructor runs, the object is released only when bit 0
of the argument is set, and the object address is returned.  The import thunk 0x005E3E9C jumps through the same
IAT slot as the operator delete the rebuilt C++ calls, so pointing the slot at a recorder catches both paths."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

DELETE = 0x005E3E9C


def _patch_import(h, entry, body):
    assert h.uc.mem_read(entry, 2) == b'\xff\x25'
    slot = struct.unpack('<I', h.uc.mem_read(entry + 2, 4))[0]
    saved = bytes(h.uc.mem_read(slot, 4))
    h.uc.mem_write(slot, struct.pack('<I', body))
    return slot, saved


def _recorder(h):
    count = h.alloc(4, bytes(4))
    array = h.alloc(64, bytes(64))
    body = h.alloc(32, bytes(32))
    h.uc.mem_write(body, b'\x8b\x44\x24\x04'
                        + b'\x8b\x0d' + struct.pack('<I', count)
                        + b'\x89\x04\x8d' + struct.pack('<I', array)
                        + b'\xff\x05' + struct.pack('<I', count)
                        + b'\xc3')
    return count, array, body


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def test_map_height_destroy(h):
    count, array, body = _recorder(h)
    slot, saved = _patch_import(h, DELETE, body)
    try:
        for flags, freed in ((0, 0), (1, 1), (2, 0), (0xFFFFFFFF, 1)):
            obj = h.alloc(0x30, bytes(0x30))
            h.uc.mem_write(obj, struct.pack('<I', 0x0060E764))
            diffs = h.compare(0x00473590, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['flags %#x: %s' % (flags, d) for d in diffs]
            h.uc.mem_write(count, bytes(4))
            res = h.call(0x00473590, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %#x: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['flags %#x: returned %08X, this %08X' % (flags, res['eax'], obj)]
            if _u32(h, obj) != 0x0060E75C:
                return ['flags %#x: final vtable %08X' % (flags, _u32(h, obj))]
            if _u32(h, count) != freed:
                return ['flags %#x: %d deletes, want %d' % (flags, _u32(h, count), freed)]
            if freed and _u32(h, array) != obj:
                return ['flags %#x: deleted %08X, want %08X' % (flags, _u32(h, array), obj)]
        return []
    finally:
        h.uc.mem_write(slot, saved)
