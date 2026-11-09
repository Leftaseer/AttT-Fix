"""CGameFile ctor (0x00459200): the vtable, the empty name string, the null fields and the reader count.

The count is preset so the original does not have to create the file system (0x0044ABE0), which the verifier
cannot emulate."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

VFTABLE = 0x0060B71C
COUNT = 0x006C8DE0


def test_cgamefile_ctor(h):
    obj = h.alloc(0x30, bytes(0x30))

    def setup(h):
        h.uc.mem_write(COUNT, struct.pack('<I', 1))

    diffs = h.compare(0x00459200, regs={UC_X86_REG_ECX: obj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00459200, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['ctor returned %#x, not this' % res['eax']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFTABLE:
        return ['the vtable is not at +0']
    if struct.unpack('<I', h.uc.mem_read(obj + 4, 4))[0] != 0:
        return ['the object flag at +4 is not cleared']
    if struct.unpack('<II', h.uc.mem_read(obj + 0x1C, 8)) != (0, 15):
        return ['the name string is not empty']
    for off in (0x24, 0x28, 0x2C):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['+0x%X is not cleared' % off]
    if struct.unpack('<I', h.uc.mem_read(COUNT, 4))[0] != 2:
        return ['the reader count is not one higher']
    return []
