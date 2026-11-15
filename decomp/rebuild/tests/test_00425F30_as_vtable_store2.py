"""0x00425F30 (ECX = the object, ret 0): stores the ActionScript singleton vtable 0x00607ED0."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425F30
VTABLE = 0x00607ED0


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def test_00425F30(h):
    obj = h.alloc(0x20, b'\xEE' * 0x20)
    diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x20)
    res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if _u32(h, obj) != VTABLE:
        return ['the vtable is %08X' % _u32(h, obj)]
    return None
