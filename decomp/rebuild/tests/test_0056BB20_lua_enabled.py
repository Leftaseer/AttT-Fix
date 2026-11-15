"""Lua_006C7460::Enabled method wrapper (0x0056BB20): walks this+8 -> [+4] -> [+8] to the lua object and forwards
the argument to Enabled (0x5339E0), returning its result.  Enabled is replaced by a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

WRAPPER = 0x0056BB20
ENABLED = 0x005339E0

LOG_THIS = 0x00
LOG_ARG = 0x04
LOG_COUNT = 0x08

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _stub(h, log):
    code = (b'\x89\x0D' + struct.pack('<I', log + LOG_THIS)      # mov [this], ecx
            + b'\x8B\x44\x24\x04'                                # mov eax, [esp+4]
            + b'\xA3' + struct.pack('<I', log + LOG_ARG)         # mov [arg], eax
            + b'\xFF\x05' + struct.pack('<I', log + LOG_COUNT)   # inc [count]
            + b'\xB8\x78\x56\x00\x00'                            # mov eax, 0x5678
            + b'\xC2\x04\x00')                                   # ret 4
    saved.setdefault(ENABLED, bytes(h.uc.mem_read(ENABLED, len(code))))
    h.uc.mem_write(ENABLED, code)
    h.uc.ctl_remove_cache(ENABLED, ENABLED + len(code))


def test_enabled_wrapper(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(16, bytes(16))
        for arg in (0, 1, -1):
            a = h.alloc(0x10, bytes(0x10))
            b = h.alloc(0x10, bytes(0x10))
            lua = h.alloc(0x40, bytes(0x40))
            h.uc.mem_write(a + 4, struct.pack('<I', b))
            h.uc.mem_write(b + 8, struct.pack('<I', lua))
            w = h.alloc(0x10, bytes(0x10))
            h.uc.mem_write(w + 8, struct.pack('<I', a))
            h.uc.mem_write(log, bytes(12))
            _stub(h, log)
            diffs = h.compare(WRAPPER, args=[arg & 0xFFFFFFFF], regs={UC_X86_REG_ECX: w})
            if diffs:
                return ['arg %d: %s' % (arg, d) for d in diffs]
            h.uc.mem_write(log, bytes(12))
            res = h.call(WRAPPER, args=[arg & 0xFFFFFFFF], regs={UC_X86_REG_ECX: w})
            if res['fault']:
                return ['arg %d: replacement faulted: %s' % (arg, res['fault'])]
            if _u32(h, log + LOG_COUNT) != 1:
                return ['arg %d: enabled called %d times' % (arg, _u32(h, log + LOG_COUNT))]
            if _u32(h, log + LOG_THIS) != lua:
                return ['arg %d: enabled called on %08X, want %08X' % (arg, _u32(h, log + LOG_THIS), lua)]
            if _u32(h, log + LOG_ARG) != (arg & 0xFFFFFFFF):
                return ['arg %d: forwarded %08X' % (arg, _u32(h, log + LOG_ARG))]
            if res['eax'] != 0x5678:
                return ['arg %d: returned %08X, want the enabled result 5678' % (arg, res['eax'])]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
