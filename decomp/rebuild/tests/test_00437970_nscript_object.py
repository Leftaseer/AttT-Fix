"""sub_00437970 (size 112, ECX thiscall, ret 8): builds an nScript object from the script handle arg 1: the vtable
0x00608260 at +0, +4 = 0, +8 = the handle, +0xC = the stack top of the Lua state at 0x008D122C (0x00402A60, kept to
be restored), +0x10 = 0, the byte arg 2 at +0x14.  Returns the object."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00437970
TOP = 0x00402A60
LUA = 0x008D122C
VTABLE = 0x00608260
MARK = 0x77770000

T_COUNT = 0x00
T_ARG = 0x04
LOG_SIZE = 0x10

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def test_00437970_nscript_object(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        code = (b'\xFF\x05' + _dword(log + T_COUNT)                          # inc [calls]
                + b'\x8B\x44\x24\x04\xA3' + _dword(log + T_ARG)              # [esp+4] -> log
                + b'\xB8' + _dword(MARK)                                     # eax = marker
                + b'\xC3')
        stub = h.alloc(len(code), code)
        _patch(h, TOP, b'\xE9' + struct.pack('<i', stub - (TOP + 5)))
        state = h.alloc(0x20, bytes(0x20))
        saved[LUA] = bytes(h.uc.mem_read(LUA, 4))
        h.uc.mem_write(LUA, _dword(state))
        this = h.alloc(0x40, b'\xCC' * 0x40)

        def setup(handle, flag):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(this, b'\xCC' * 0x40)
            return [handle, flag]

        for name, handle, flag in (('plain', 0x11110000, 0), ('flagged', 0x22220000, 0x1ff)):
            args = setup(handle, flag)
            diffs = h.compare(VF, args=args, regs={UC_X86_REG_ECX: this})
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            args = setup(handle, flag)
            res = h.call(VF, args=args, regs={UC_X86_REG_ECX: this})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if _u32(h, log + T_COUNT) != 1 or _u32(h, log + T_ARG) != state:
                return ['%s: the stack top was asked %d times on %08X' % (name, _u32(h, log + T_COUNT),
                                                                          _u32(h, log + T_ARG))]
            want = _dword(VTABLE) + _dword(0) + _dword(handle) + _dword(MARK) + _dword(0) + bytes([flag & 0xff])
            if bytes(h.uc.mem_read(this, len(want))) != want:
                return ['%s: the object is %s' % (name, bytes(h.uc.mem_read(this, len(want))).hex())]
            if bytes(h.uc.mem_read(this + len(want), 0x40 - len(want))) != b'\xCC' * (0x40 - len(want)):
                return ['%s: the object was written past +0x14' % name]
            if res['eax'] != this:
                return ['%s: returned %08X' % (name, res['eax'])]
    finally:
        for address, value in saved.items():
            h.uc.mem_write(address, value)
            h.uc.ctl_remove_cache(address, address + len(value))
        saved.clear()
        h.heap_ptr = heap0
    return None
