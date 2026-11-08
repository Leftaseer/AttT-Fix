"""CDatFile ctor/dtor (0x00444D50 / 0x00445130): the source cache, the keyword tables and the record arrays."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

VFT_CLASS = 0x0060A560
VFT_SINGLETON = 0x0060A4C4


def _string(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 0x14, 8))
    if cap < 16:
        return bytes(h.uc.mem_read(addr + 4, size))
    ptr = struct.unpack('<I', h.uc.mem_read(addr + 4, 4))[0]
    return bytes(h.uc.mem_read(ptr, size))


def _pair(h, table, i):
    return _string(h, table + i * 0x38), _string(h, table + i * 0x38 + 0x1C)


def test_datfile_ctor(h):
    obj = h.alloc(0xBFC, bytes(0xBFC))
    diffs = h.compare(0x00444D50, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00444D50, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['ctor returned %#x, not this' % res['eax']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_CLASS:
        return ['the class vtable is not at +0']
    if _string(h, obj + 0x08) != b'':
        return ['the token text is not empty']
    for i in range(10):
        src = obj + 0x24 + i * 0x3C
        if _string(h, src) or _string(h, src + 0x1C):
            return ['source %d is not empty' % i]
        if struct.unpack('<I', h.uc.mem_read(src + 0x38, 4))[0] != 0:
            return ['source %d has a position' % i]
    for off, name in ((0x27C, 'sourceCount'), (0x280, 'currentSource'), (0x294, 'sourcePos'), (0xBF8, 'recordCount')):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['%s is not cleared' % name]
    if h.uc.mem_read(obj + 0x04, 1) != b'\0':
        return ['the token is not cleared']
    set0, set1 = struct.unpack('<II', h.uc.mem_read(obj + 0x288, 8))
    if not set0 or not set1:
        return ['the keyword tables are not allocated']
    if struct.unpack('<I', h.uc.mem_read(set0 - 4, 4))[0] != 3:
        return ['set 0 does not count 3 entries']
    if struct.unpack('<I', h.uc.mem_read(set1 - 4, 4))[0] != 8:
        return ['set 1 does not count 8 entries']
    want0 = [(b'fullscreen', b'n'), (b'resolution', b'nn'), (b'texturequality', b'n')]
    for i, want in enumerate(want0):
        if _pair(h, set0, i) != want:
            return ['set 0 entry %d is %r, not %r' % (i, _pair(h, set0, i), want)]
    want1 = [(b'cameraforward', b'w'), (b'cameraback', b'w'), (b'cameraleft', b'w'),
             (b'cameraright', b'w'), (b'cameraup', b'w'), (b'cameradown', b'w'),
             (b'gamepause', b'w'), (b'cameratoggle', b'w')]
    for i, want in enumerate(want1):
        if _pair(h, set1, i) != want:
            return ['set 1 entry %d is %r, not %r' % (i, _pair(h, set1, i), want)]
    for i in range(300):
        if h.uc.mem_read(obj + 0x298 + i * 8, 8) != bytes(8):
            return ['record %d is not empty' % i]
    return []


def test_datfile_dtor(h):
    obj = h.alloc(0xBFC, bytes(0xBFC))

    def setup(h):
        h.call(0x00444D50, regs={UC_X86_REG_ECX: obj})
        words = h.alloc(4 + 2 * 0x1C, bytes(4 + 2 * 0x1C))
        h.uc.mem_write(words, struct.pack('<I', 2))
        h.uc.mem_write(obj + 0x298, struct.pack('<I', words + 4))
        numbers = h.alloc(8, bytes(8))
        h.uc.mem_write(obj + 0x29C, struct.pack('<I', numbers))
        h.uc.mem_write(obj + 0xBF8, struct.pack('<I', 1))

    diffs = h.compare(0x00445130, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(0x00445130, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_SINGLETON:
        return ['the singleton vtable is not at +0 after the dtor']
    return []
