"""CMapHeight constructor (0x00473360): vtable 0x0060E764, the row pointer cleared, everything else untouched."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX


def test_map_height_ctor(h):
    obj = h.alloc(0x30, b'\xa5' * 0x30)
    diffs = h.compare(0x00473360, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00473360, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['returned %08X, this %08X' % (res['eax'], obj)]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != 0x0060E764:
        return ['vtable %08X' % struct.unpack('<I', h.uc.mem_read(obj, 4))[0]]
    if struct.unpack('<I', h.uc.mem_read(obj + 4, 4))[0] != 0:
        return ['rows were not cleared']
    if h.uc.mem_read(obj + 8, 0x28) != b'\xa5' * 0x28:
        return ['the constructor wrote past +4']
    return []
