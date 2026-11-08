"""CConfig ctor/dtor (0x00441D10 / 0x00441D70): CSingleton/CConfig vtables and the two std::strings."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

VFT_CONFIG = 0x0060A298
VFT_SINGLETON = 0x0060A290


def _empty_string(h, p):
    size, res = struct.unpack('<II', h.uc.mem_read(p + 0x14, 8))
    if size != 0:
        return 'size %d' % size
    if res != 15:
        return 'capacity %d' % res
    if h.uc.mem_read(p + 4, 1) != b'\0':
        return 'buffer is not empty'
    return ''


def test_config_ctor(h):
    obj = h.alloc(0x98, bytes(0x98))
    diffs = h.compare(0x00441D10, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00441D10, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['ctor returned %#x, not this' % res['eax']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_CONFIG:
        return ['the CConfig vtable is not at +0']
    for off in (0x04, 0x20):
        bad = _empty_string(h, obj + off)
        if bad:
            return ['string +0x%X: %s' % (off, bad)]
    return []


def test_config_dtor(h):
    obj = h.alloc(0x98, bytes(0x98))

    def setup(h):
        h.uc.mem_write(obj, struct.pack('<I', VFT_CONFIG))
        for off in (0x04, 0x20):
            h.uc.mem_write(obj + off + 0x14, struct.pack('<II', 0, 15))

    diffs = h.compare(0x00441D70, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(0x00441D70, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_SINGLETON:
        return ['the CSingleton vtable is not at +0 after the dtor']
    return []


def test_console_game_folder(h):
    obj = h.alloc(0x1700, bytes(0x1700))
    diffs = h.compare(0x00441C50, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00441C50, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj + 0x1638:
        return ['GameFolder returned %#x, not this+0x1638' % res['eax']]
    return []
