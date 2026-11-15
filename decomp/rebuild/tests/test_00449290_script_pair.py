"""sub_00449290 (size 128, ECX thiscall, ret 40): builds the pair of a script value - the table by value (12 bytes)
 * into +0 through 0x00435D90, the string by value (28 bytes) into +0xC through its copy constructor - then destroys
 * the by-value arguments (the table with 0x004220A0, the string with its destructor) and returns the pair."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00449290
COPY_TABLE = 0x00435D90
DTOR_TABLE = 0x004220A0
IAT_STR_COPY = 0x00607334
IAT_STR_DTOR = 0x00607330

LOG_T = 0x00
LOG_T_THIS = 0x04
LOG_T_SRC0 = 0x08
LOG_T_SRC8 = 0x0C
LOG_S = 0x10
LOG_S_THIS = 0x14
LOG_S_SRC0 = 0x18
LOG_S_SRC24 = 0x1C
LOG_DT = 0x20
LOG_DT_THIS = 0x24
LOG_DT_VAL = 0x28
LOG_DS = 0x2C
LOG_DS_THIS = 0x30
LOG_DS_VAL = 0x34
LOG_SIZE = 0x40

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


def test_script_pair(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, COPY_TABLE,
               b'\xFF\x05' + _dword(log + LOG_T)                                     # inc [copy table]
               + b'\x89\x0D' + _dword(log + LOG_T_THIS)                              # mov [this], ecx
               + b'\x8B\x44\x24\x04\x8B\x00\xA3' + _dword(log + LOG_T_SRC0)          # [src] -> src0
               + b'\x8B\x44\x24\x04\x8B\x40\x08\xA3' + _dword(log + LOG_T_SRC8)      # [src+8] -> src8
               + b'\xC7\x01' + _dword(0x11111111)                                    # mov [ecx], 1111
               + b'\xC7\x41\x04' + _dword(0x22222222)                                # mov [ecx+4], 2222
               + b'\xC7\x41\x08' + _dword(0x33333333)                                # mov [ecx+8], 3333
               + b'\xC2\x04\x00')                                                    # ret 4
        _patch(h, DTOR_TABLE,
               b'\xFF\x05' + _dword(log + LOG_DT)                                    # inc [dtor table]
               + b'\x89\x0D' + _dword(log + LOG_DT_THIS)                             # mov [this], ecx
               + b'\x8B\x01\xA3' + _dword(log + LOG_DT_VAL)                          # [ecx] -> val
               + b'\xC3')                                                            # ret
        _patch_import(h, IAT_STR_COPY,
                      '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z',
                      b'\xFF\x05' + _dword(log + LOG_S)                              # inc [copy string]
                      + b'\x89\x0D' + _dword(log + LOG_S_THIS)                       # mov [this], ecx
                      + b'\x8B\x44\x24\x04\x8B\x00\xA3' + _dword(log + LOG_S_SRC0)   # [src] -> src0
                      + b'\x8B\x44\x24\x04\x8B\x40\x18\xA3' + _dword(log + LOG_S_SRC24)  # [src+18] -> src24
                      + b'\xC7\x01' + _dword(0x44444444)                             # mov [ecx], 4444
                      + b'\xC7\x41\x18' + _dword(0x55555555)                         # mov [ecx+18], 5555
                      + b'\xC2\x04\x00')                                             # ret 4
        _patch_import(h, IAT_STR_DTOR,
                      '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ',
                      b'\xFF\x05' + _dword(log + LOG_DS)                             # inc [dtor string]
                      + b'\x89\x0D' + _dword(log + LOG_DS_THIS)                      # mov [this], ecx
                      + b'\x8B\x01\xA3' + _dword(log + LOG_DS_VAL)                   # [ecx] -> val
                      + b'\xC3')                                                     # ret
        pair = h.alloc(0x40, bytes(0x40))
        args = [0xA1, 0xB2, 0xC3, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57]
        diffs = h.compare(VF, args=args, regs={UC_X86_REG_ECX: pair})
        if diffs:
            return diffs
        h.uc.mem_write(pair, bytes(0x40))
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(VF, args=args, regs={UC_X86_REG_ECX: pair})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        for off, name in ((LOG_T, 'table copy'), (LOG_S, 'string copy'), (LOG_DT, 'table dtor'),
                          (LOG_DS, 'string dtor')):
            if _u32(h, log + off) != 1:
                return ['%s called %d times' % (name, _u32(h, log + off))]
        if _u32(h, log + LOG_T_THIS) != pair or _u32(h, log + LOG_S_THIS) != pair + 0xC:
            return ['pair parts built at %08X/%08X' % (_u32(h, log + LOG_T_THIS), _u32(h, log + LOG_S_THIS))]
        if _u32(h, log + LOG_T_SRC0) != 0xA1 or _u32(h, log + LOG_T_SRC8) != 0xC3:
            return ['table copy read %08X..%08X' % (_u32(h, log + LOG_T_SRC0), _u32(h, log + LOG_T_SRC8))]
        if _u32(h, log + LOG_S_SRC0) != 0x51 or _u32(h, log + LOG_S_SRC24) != 0x57:
            return ['string copy read %08X..%08X' % (_u32(h, log + LOG_S_SRC0), _u32(h, log + LOG_S_SRC24))]
        if _u32(h, log + LOG_DT_VAL) != 0xA1 or _u32(h, log + LOG_DS_VAL) != 0x51:
            return ['dtors got %08X/%08X' % (_u32(h, log + LOG_DT_VAL), _u32(h, log + LOG_DS_VAL))]
        want = {0x00: 0x11111111, 0x04: 0x22222222, 0x08: 0x33333333, 0x0C: 0x44444444, 0x24: 0x55555555}
        for off, value in want.items():
            if _u32(h, pair + off) != value:
                return ['pair+%02X is %08X' % (off, _u32(h, pair + off))]
        if res['eax'] != pair:
            return ['returned %08X' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
