"""Constructor (0x004B40E0): the vtable pointer 0x610D00 is stored, +4 is cleared and the manager reached
through the singleton pointer at 0x6CA34C registers the object; the object is returned.  The registration is a
recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004B40E0
REGISTER = 0x004B5880
MANAGER = 0x006CA34C
VTABLE = 0x00610D00

LOG_COUNT = 0x00
LOG_THIS = 0x04
LOG_ARG = 0x08
LOG_SIZE = 0x20

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _dword(addr):
    return struct.pack('<I', addr)


def test_node_ctor(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, REGISTER,
               b'\x89\x0D' + _dword(log + LOG_THIS)                        # mov [log+4], ecx
               + b'\x8B\x44\x24\x04'                                       # mov eax, [esp+4]
               + b'\xA3' + _dword(log + LOG_ARG)                           # mov [log+8], eax
               + b'\xFF\x05' + _dword(log + LOG_COUNT)                     # inc [log]
               + b'\xC2\x04\x00')                                          # ret 4
        _patch(h, MANAGER, _dword(h.alloc(0x40, bytes(0x40))))
        manager = _u32(h, MANAGER)
        obj = h.alloc(0x100, bytes([0xAA]) * 0x100)
        diffs = h.compare(FN, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(FN, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, obj) != VTABLE:
            return ['vtable is %08X, want %08X' % (_u32(h, obj), VTABLE)]
        if _u32(h, obj + 4) != 0:
            return ['+4 is %08X, want 0' % _u32(h, obj + 4)]
        if _u32(h, log + LOG_COUNT) != 1:
            return ['registered %d times' % _u32(h, log + LOG_COUNT)]
        if _u32(h, log + LOG_THIS) != manager or _u32(h, log + LOG_ARG) != obj:
            return ['registered on %08X with %08X' % (_u32(h, log + LOG_THIS), _u32(h, log + LOG_ARG))]
        if res['eax'] != obj:
            return ['returned %08X' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
