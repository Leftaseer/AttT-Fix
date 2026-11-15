"""sub_0053A620 (size 112, ECX thiscall, ret 0x20): assigns the 28-byte string passed by value as the second stack
argument (the first is ignored) to the string at +0x254 of the object in ECX and destroys the caller's temporary.
Both imports are recording stubs in both IAT copies."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x0053A620
IAT_ASSIGN = 0x0060731C
IAT_DTOR = 0x00607330

LOG_ASSIGN = 0x00
LOG_ASSIGN_THIS = 0x04
LOG_ASSIGN_SRC = 0x08
LOG_DTOR = 0x0C
LOG_DTOR_SRC = 0x10
LOG_BYTES = 0x40

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def test_third_component_name(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_BYTES, bytes(LOG_BYTES))
        _patch_import(h, IAT_ASSIGN,
                      '__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z',
                      b'\xFF\x05' + _dword(log + LOG_ASSIGN)                        # inc [assign]
                      + b'\x89\x0D' + _dword(log + LOG_ASSIGN_THIS)                 # mov [this], ecx
                      + b'\x8B\x44\x24\x04\x8B\x00\xA3' + _dword(log + LOG_ASSIGN_SRC)  # [[esp+4]] -> src
                      + b'\x8B\xC1'                                                 # mov eax, ecx
                      + b'\xC2\x04\x00')                                            # ret 4
        _patch_import(h, IAT_DTOR,
                      '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ',
                      b'\xFF\x05' + _dword(log + LOG_DTOR)                          # inc [dtor]
                      + b'\x8B\x01\xA3' + _dword(log + LOG_DTOR_SRC)                # [ecx] -> dtor src
                      + b'\xC3')                                                    # ret
        obj = h.alloc(0x300, bytes(0x300))
        args = [0x77, 0xAB, 0xCD, 0xEF, 0x11, 0x22, 0x33, 0x44]
        diffs = h.compare(VF, args=args, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_BYTES))
        res = h.call(VF, args=args, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_ASSIGN) != 1 or _u32(h, log + LOG_DTOR) != 1:
            return ['assign/dtor called %d/%d times' % (_u32(h, log + LOG_ASSIGN), _u32(h, log + LOG_DTOR))]
        if _u32(h, log + LOG_ASSIGN_THIS) != obj + 0x254:
            return ['assigned on %08X' % _u32(h, log + LOG_ASSIGN_THIS)]
        if _u32(h, log + LOG_ASSIGN_SRC) != 0xAB or _u32(h, log + LOG_DTOR_SRC) != 0xAB:
            return ['arguments hold %08X/%08X' % (_u32(h, log + LOG_ASSIGN_SRC), _u32(h, log + LOG_DTOR_SRC))]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
