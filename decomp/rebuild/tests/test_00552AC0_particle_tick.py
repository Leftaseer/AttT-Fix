"""NParticleSystem::CParticleSystem::Tick (0x00552AC0): ticks the particle system with mode 3.  The tick
implementation is replaced by a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

TICK = 0x00552AC0
TICK_IMPL = 0x00551F60

LOG_THIS = 0x00
LOG_MODE = 0x04
LOG_COUNT = 0x08

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _stub(h, log):
    code = (b'\x89\x0D' + struct.pack('<I', log + LOG_THIS)      # mov [this], ecx
            + b'\x8B\x44\x24\x04'                                # mov eax, [esp+4]
            + b'\xA3' + struct.pack('<I', log + LOG_MODE)        # mov [mode], eax
            + b'\xFF\x05' + struct.pack('<I', log + LOG_COUNT)   # inc [count]
            + b'\xB8\x44\x33\x22\x11'                            # mov eax, 0x11223344
            + b'\xC2\x04\x00')                                   # ret 4
    saved.setdefault(TICK_IMPL, bytes(h.uc.mem_read(TICK_IMPL, len(code))))
    h.uc.mem_write(TICK_IMPL, code)
    h.uc.ctl_remove_cache(TICK_IMPL, TICK_IMPL + len(code))


def _clear(h, log):
    h.uc.mem_write(log, bytes(12))


def test_particle_system_tick(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(16, bytes(16))
        obj = h.alloc(0x40, bytes(0x40))
        _stub(h, log)
        diffs = h.compare(TICK, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        _clear(h, log)
        res = h.call(TICK, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_COUNT) != 1:
            return ['impl called %d times' % _u32(h, log + LOG_COUNT)]
        if _u32(h, log + LOG_THIS) != obj:
            return ['impl called on %08X, want %08X' % (_u32(h, log + LOG_THIS), obj)]
        if _u32(h, log + LOG_MODE) != 3:
            return ['impl called with mode %d, want 3' % _u32(h, log + LOG_MODE)]
        if res['eax'] != 0x11223344:
            return ['returned %08X, want the impl result 11223344' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
