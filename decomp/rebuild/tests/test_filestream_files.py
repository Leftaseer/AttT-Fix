"""The file system's file objects: the base file's lifetime (0x450A80 / 0x450AA0 / 0x450AB0), a pak section
(0x450AE0 and its position methods 0x42B630 / 0x450B10 / 0x5B42C0) and the tell of a disk file (0x450C70).

The disk file's constructor and its read/seek close over MSVCP80's ifstream, which the verifier does not
emulate, so only the tell is compared there: both halves stop at the same unemulated import with the same
stack and registers, which checks the prologue and the hidden fpos buffer of the replacement."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

CBaseFile_VTABLE = 0x60B148
CArchFile_VTABLE = 0x60B160
CFstreamFile_VTABLE = 0x60B18C
CGameObject_VTABLE = 0x607D14


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def test_base_file_lifetime(h):
    obj = h.alloc(0xC, b'\xff' * 0xC)
    diffs = h.compare(0x00450A80, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    h.call(0x00450A80, regs={UC_X86_REG_ECX: obj})
    if (_u32(h, obj), _u32(h, obj + 4), _u32(h, obj + 8)) != (CBaseFile_VTABLE, 0, 0):
        return ['the base constructor left %08X %08X %08X'
                % (_u32(h, obj), _u32(h, obj + 4), _u32(h, obj + 8))]

    # the flag must be 0: the CGameObject destructor throws otherwise
    h.uc.mem_write(obj + 4, struct.pack('<I', 0))
    diffs = h.compare(0x00450AA0, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    h.call(0x00450AA0, regs={UC_X86_REG_ECX: obj})
    if _u32(h, obj) != CGameObject_VTABLE:
        return ['the base destructor left vtable %08X' % _u32(h, obj)]

    # the deleting destructor with flags 0 only destroys (bit 0 would free the verifier's memory)
    obj = h.alloc(0xC, struct.pack('<III', CArchFile_VTABLE, 0, 7))
    diffs = h.compare(0x00450AB0, args=[0], regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00450AB0, args=[0], regs={UC_X86_REG_ECX: obj})
    if res['eax'] != obj:
        return ['the deleting destructor returned %08X, not the object' % res['eax']]
    if _u32(h, obj + 8) != 7:
        return ['the deleting destructor changed the size field']
    return None


def test_arch_file_ctor(h):
    for stream, size, offset, encrypted in ((0x12345678, 0x400, 0x8, 0),
                                            (0x00ABCDEF, 0, 0x1000, 1)):
        obj = h.alloc(0x1C, b'\xcc' * 0x1C)
        diffs = h.compare(0x00450AE0, args=[stream, size, offset, encrypted],
                          regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        res = h.call(0x00450AE0, args=[stream, size, offset, encrypted],
                     regs={UC_X86_REG_ECX: obj})
        if res['eax'] != obj:
            return ['the constructor returned %08X, not the object' % res['eax']]
        want = (CArchFile_VTABLE, 0, size, stream, 0, offset)
        got = tuple(_u32(h, obj + off) for off in (0, 4, 8, 0xC, 0x10, 0x14))
        if got != want:
            return ['the archive object is %r, want %r' % (got, want)]
        if h.uc.mem_read(obj + 0x18, 1) != bytes([encrypted]):
            return ['the encryption flag is %d, want %d' % (h.uc.mem_read(obj + 0x18, 1)[0], encrypted)]
    return None


def test_arch_file_position(h):
    obj = h.alloc(0x1C, struct.pack('<III', CArchFile_VTABLE, 0, 0x400))
    h.uc.mem_write(obj + 0x10, struct.pack('<I', 0x20))
    for addr, arg, want in ((0x0042B630, 0x40, 0x40),
                            (0x00450B10, 7, 0x47),
                            (0x00450B10, -0x10, 0x37),
                            (0x005B42C0, None, 0x37)):
        diffs = h.compare(addr, args=[] if arg is None else [arg],
                          regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        res = h.call(addr, args=[] if arg is None else [arg], regs={UC_X86_REG_ECX: obj})
        if _u32(h, obj + 0x10) != want:
            return ['%08X: the position is %d, want %d' % (addr, _u32(h, obj + 0x10), want)]
        if arg is not None and res['eax'] != (arg & 0xFFFFFFFF):
            return ['%08X returned %08X, not its argument' % (addr, res['eax'])]
    return None


def test_fstream_tell(h):
    # the tellg import is not emulated: both halves must stop at it with the same stack and registers
    obj = h.alloc(0x98, bytes(0x98))
    diffs = h.compare(0x00450C70, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    return None
