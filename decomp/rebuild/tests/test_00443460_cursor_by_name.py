"""sub_00443460 (size 192, ECX thiscall, ret 4): selects the cursor named by arg 1: the name goes to the state string
 * at +0x23C, the cursor map at +0x258 is searched (0x00422D80); a miss builds "literal + name", copies it into the
 * exception object and throws it (0x005E3EC0, ThrowInfo 0x0069916C); either way slot 0xE8 gets the cursor found in
 * the map node (+0x24)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00443460
FIND = 0x00422D80
IAT_ASSIGN = 0x0060731C
IAT_CSTR = 0x00607324
IAT_OPPLUS = 0x006071C0
IAT_COPY = 0x00607334

LOG_A = 0x00
LOG_A_OFF = 0x04
LOG_A_SRC0 = 0x08
LOG_F = 0x0C
LOG_F_OFF = 0x10
LOG_F_KEY0 = 0x14
LOG_C = 0x18
LOG_C_LIT = 0x1C
LOG_O = 0x20
LOG_O_A0 = 0x24
LOG_O_B0 = 0x28
LOG_SC = 0x2C
LOG_SC_SRC0 = 0x30
LOG_V = 0x40
LOG_V_OFF = 0x44
LOG_V_CUR = 0x48
LOG_SIZE = 0x80

LITERAL = 0x0060A318

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


def test_cursor_by_name(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        this_slot = h.alloc(4, bytes(4))
        node_sel = h.alloc(4, bytes(4))
        this = h.alloc(0x300, bytes(0x300))
        h.uc.mem_write(this_slot, _dword(this))
        _patch_import(h, IAT_ASSIGN,
                      '__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z',
                      b'\xFF\x05' + _dword(log + LOG_A)                              # inc [assign]
                      + b'\x8B\xC1\x2B\x05' + _dword(this_slot) + b'\xA3' + _dword(log + LOG_A_OFF)  # ecx-this
                      + b'\x8B\x44\x24\x04\x8B\x00\xA3' + _dword(log + LOG_A_SRC0)   # [src] -> src0
                      + b'\xC7\x01' + _dword(0x11110001)                             # mov [ecx], marker
                      + b'\x8B\xC1\xC2\x04\x00')                                     # eax = ecx, ret 4
        _patch(h, FIND,
               b'\xFF\x05' + _dword(log + LOG_F)                                     # inc [find]
               + b'\x8B\xC1\x2B\x05' + _dword(this_slot) + b'\xA3' + _dword(log + LOG_F_OFF)  # ecx-this
               + b'\x8B\x44\x24\x08\x8B\x00\xA3' + _dword(log + LOG_F_KEY0)          # [key] -> key0
               + b'\x8B\x44\x24\x04'                                                 # mov eax, [esp+4]
               + b'\x8B\x15' + _dword(node_sel)                                      # mov edx, [node]
               + b'\x89\x10\xC2\x08\x00')                                            # mov [eax], edx; ret 8
        _patch_import(h, IAT_CSTR,
                      '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z',
                      b'\xFF\x05' + _dword(log + LOG_C)                              # inc [cstr]
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_C_LIT)            # [esp+4] -> literal
                      + b'\xC7\x01' + _dword(0xAAAA0001)                             # mov [ecx], marker
                      + b'\x8B\xC1\xC2\x04\x00')                                     # eax = ecx, ret 4
        _patch_import(h, IAT_OPPLUS,
                      '__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z',
                      b'\xFF\x05' + _dword(log + LOG_O)                              # inc [plus]
                      + b'\x8B\x44\x24\x08\x8B\x00\xA3' + _dword(log + LOG_O_A0)     # [a] -> a0
                      + b'\x8B\x44\x24\x0C\x8B\x00\xA3' + _dword(log + LOG_O_B0)     # [b] -> b0
                      + b'\x8B\x44\x24\x04\xC7\x00' + _dword(0xABCD0001)             # mov [result], marker
                      + b'\xC3')                                                     # ret (cdecl)
        _patch_import(h, IAT_COPY,
                      '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z',
                      b'\xFF\x05' + _dword(log + LOG_SC)                             # inc [copy]
                      + b'\x8B\x44\x24\x04\x8B\x00\xA3' + _dword(log + LOG_SC_SRC0)  # [src] -> src0
                      + b'\xC7\x01' + _dword(0xEEEE0001)                             # mov [ecx], marker
                      + b'\x8B\xC1\xC2\x04\x00')                                     # eax = ecx, ret 4
        vt = _stub(h, b'\xFF\x05' + _dword(log + LOG_V)                              # inc [slot e8]
                      + b'\x8B\xC1\x2B\x05' + _dword(this_slot) + b'\xA3' + _dword(log + LOG_V_OFF)
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_V_CUR)            # [esp+4] -> cursor
                      + b'\xC2\x04\x00')                                             # ret 4
        table = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(table + 0xE8, _dword(vt))
        h.uc.mem_write(this, _dword(table))
        found = h.alloc(0x30, bytes(0x30))
        miss = h.alloc(0x30, bytes(0x30))
        h.uc.mem_write(found + 0x24, _dword(0x2F001000))
        h.uc.mem_write(miss + 0x24, _dword(0x2F002000))
        h.uc.mem_write(this + 0x260, _dword(miss))
        name = h.alloc(0x20, bytes(0x20))
        h.uc.mem_write(name, _dword(0x51510001))
        zero = dict((off, 0) for off in range(0, LOG_SIZE, 4))
        for node, tag in ((found, 'found'), (miss, 'missing')):
            h.uc.mem_write(node_sel, _dword(node))
            if node == found:   # the miss raises through the patched throw (never returns), so only the found path diffs
                h.uc.mem_write(log, bytes(LOG_SIZE))
                diffs = h.compare(VF, args=[name], regs={UC_X86_REG_ECX: this})
                if diffs:
                    return ['%s: %s' % (tag, d) for d in diffs]
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(this + 0x23c, bytes(0x1C))
            res = h.call(VF, args=[name], regs={UC_X86_REG_ECX: this})
            if node == miss:
                if res['fault'] != 'threw':
                    return ['missing: the run ended with %r' % res['fault']]
            elif res['fault']:
                return ['%s: replacement faulted: %s' % (tag, res['fault'])]
            if _u32(h, log + LOG_A) != 1 or _u32(h, log + LOG_F) != 1:
                return ['%s: assign/find called %d/%d' % (tag, _u32(h, log + LOG_A), _u32(h, log + LOG_F))]
            if _u32(h, log + LOG_A_OFF) != 0x23C or _u32(h, log + LOG_F_OFF) != 0x258:
                return ['%s: assign/find this offsets %X/%X' % (tag, _u32(h, log + LOG_A_OFF),
                                                                _u32(h, log + LOG_F_OFF))]
            if _u32(h, log + LOG_A_SRC0) != 0x51510001 or _u32(h, log + LOG_F_KEY0) != 0x51510001:
                return ['%s: name read as %08X/%08X' % (tag, _u32(h, log + LOG_A_SRC0),
                                                        _u32(h, log + LOG_F_KEY0))]
            if _u32(h, this + 0x23C) != 0x11110001:
                return ['%s: state string got %08X' % (tag, _u32(h, this + 0x23C))]
            if node == found:
                if _u32(h, log + LOG_V) != 1:
                    return ['found: slot E8 called %d times' % _u32(h, log + LOG_V)]
                if _u32(h, log + LOG_V_OFF) != 0 or _u32(h, log + LOG_V_CUR) != 0x2F001000:
                    return ['found: slot E8 on %d past this, cursor %08X' % (_u32(h, log + LOG_V_OFF),
                                                                             _u32(h, log + LOG_V_CUR))]
                if any(_u32(h, log + off) for off in (LOG_C, LOG_O, LOG_SC)):
                    return ['found: threw a message']
            else:
                if _u32(h, log + LOG_V) != 0:
                    return ['missing: slot E8 called %d times' % _u32(h, log + LOG_V)]
                want = {LOG_C: 1, LOG_O: 1, LOG_SC: 1, LOG_C_LIT: LITERAL,
                        LOG_O_A0: 0xAAAA0001, LOG_O_B0: 0x51510001, LOG_SC_SRC0: 0xABCD0001}
                for off, value in want.items():
                    if _u32(h, log + off) != value:
                        return ['%s: log+%02X is %08X, want %08X' % (tag, off, _u32(h, log + off), value)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
