"""CFileSystem ctor/dtor (0x00451E00 / 0x00452580): the two fs maps, the archive name and the embedded object."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

VFT_FILESYSTEM = 0x0060B1A8
VFT_SINGLETON = 0x0060B140


def _fill_empty(h, obj):
    h.uc.mem_write(obj, struct.pack('<I', VFT_FILESYSTEM))
    alloc = h.alloc(1, b'\0')
    h.call(0x00451430, args=[alloc, alloc], regs={UC_X86_REG_ECX: obj + 0x10})
    h.call(0x00489710, args=[alloc, alloc], regs={UC_X86_REG_ECX: obj + 0x38})
    h.uc.mem_write(obj + 0x60, bytes(0x1C))
    h.uc.mem_write(obj + 0x60 + 0x18, struct.pack('<I', 15))
    h.uc.mem_write(obj + 0x84, bytes(4))
    h.call(0x00577C60, regs={UC_X86_REG_ECX: obj + 0x88})


def test_filesystem_ctor(h):
    obj = h.alloc(0xB8, bytes(0xB8))
    diffs = h.compare(0x00451E00, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00451E00, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['ctor returned %#x, not this' % res['eax']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_FILESYSTEM:
        return ['the vtable is not at +0']
    for off in (0x10, 0x38):
        sentinel, size = struct.unpack('<II', h.uc.mem_read(obj + off + 8, 8))
        mask, count = struct.unpack('<II', h.uc.mem_read(obj + off + 0x20, 8))
        if sentinel == 0 or size != 0:
            return ['map +0x%X: sentinel %#x size %d' % (off, sentinel, size)]
        if mask != 1 or count != 1:
            return ['map +0x%X: mask %d count %d' % (off, mask, count)]
    if struct.unpack('<I', h.uc.mem_read(obj + 0x84, 4))[0] != 0:
        return ['+0x84 is not cleared']
    if struct.unpack('<I', h.uc.mem_read(obj + 0xA8, 4))[0] == 0:
        return ['the embedded map has no sentinel']
    return []


def test_filesystem_dtor(h):
    obj = h.alloc(0xB8, bytes(0xB8))

    def setup(h):
        _fill_empty(h, obj)

    diffs = h.compare(0x00452580, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(0x00452580, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_SINGLETON:
        return ['the CSingleton vtable is not at +0 after the dtor']
    for off in (0x18, 0x40, 0xA8):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['+0x%X is not cleared' % off]
    for off in (0x24, 0x4C):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['bucket begin +0x%X is not cleared' % off]
    return []
