"""0x00425F20 (ECX = the object, ret 0): stores the ActionScript singleton vtable 0x00607ED0 and returns this."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425F20
VTABLE = 0x00607ED0


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def test_00425F20(h):
    obj = h.alloc(0x20, b'\xEE' * 0x20)
    diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x20)
    res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if res['eax'] != obj:
        return ['returned %08X' % res['eax']]
    if _u32(h, obj) != VTABLE:
        return ['the vtable is %08X' % _u32(h, obj)]
    return None
