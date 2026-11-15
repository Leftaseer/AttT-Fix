"""CMeshObject2DRes ctor (0x0047A0D0): initializes the base, sets the vftable 0x60EC94, finishes with 0x479F50 and
returns this.  The base initializer and the finisher are recording stubs that also sample the vftable."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x0047A0D0
BASE = 0x004AC0F0
FINISH = 0x00479F50

VFTABLE = 0x0060EC94

LOG_BASE_THIS = 0x00
LOG_BASE_VFT = 0x04
LOG_BASE_COUNT = 0x08
LOG_FIN_THIS = 0x0C
LOG_FIN_VFT = 0x10
LOG_FIN_COUNT = 0x14

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _stub(h, address, this_slot, vft_slot, count_slot):
    code = (b'\x89\x0D' + struct.pack('<I', this_slot)              # mov [this], ecx
            + b'\x8B\x01'                                           # mov eax, [ecx]
            + b'\xA3' + struct.pack('<I', vft_slot)                 # mov [vft], eax
            + b'\xFF\x05' + struct.pack('<I', count_slot)           # inc [count]
            + b'\xC3')                                              # ret
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def test_cmesh2dres_ctor(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        _stub(h, BASE, log + LOG_BASE_THIS, log + LOG_BASE_VFT, log + LOG_BASE_COUNT)
        _stub(h, FINISH, log + LOG_FIN_THIS, log + LOG_FIN_VFT, log + LOG_FIN_COUNT)
        obj = h.alloc(0x100, bytes(0x100))
        diffs = h.compare(CTOR, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x20))
        res = h.call(CTOR, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_BASE_COUNT) != 1 or _u32(h, log + LOG_BASE_THIS) != obj:
            return ['base initialized %d times on %08X' % (_u32(h, log + LOG_BASE_COUNT),
                                                           _u32(h, log + LOG_BASE_THIS))]
        if _u32(h, log + LOG_FIN_COUNT) != 1 or _u32(h, log + LOG_FIN_THIS) != obj:
            return ['finisher called %d times on %08X' % (_u32(h, log + LOG_FIN_COUNT),
                                                          _u32(h, log + LOG_FIN_THIS))]
        if _u32(h, log + LOG_FIN_VFT) != VFTABLE:
            return ['finisher saw vftable %08X' % _u32(h, log + LOG_FIN_VFT)]
        if _u32(h, obj) != VFTABLE:
            return ['vftable %08X' % _u32(h, obj)]
        if res['eax'] != obj:
            return ['returned %08X, want this %08X' % (res['eax'], obj)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
