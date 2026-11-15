"""sub_00420C80 (size 96, ECX thiscall, ret 4): copies the std::exception arg 1 through its copy constructor
(MSVCR80 IAT 0x6073BC, base copy), then restores the vtable 0x00607B18 at +0 and copies the message string at +0xC
with its copy constructor (MSVCP80 IAT 0x607334, this+0xC from arg+0xC).  Returns this."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00420C80
VTABLE = 0x00607B18
IAT_BASE = 0x006073BC
IAT_STR = 0x00607334

L_BASE_COUNT = 0x00
L_BASE_THIS = 0x04
L_BASE_SRC = 0x08
L_STR_COUNT = 0x0C
L_STR_THIS = 0x10
L_STR_SRC = 0x14
LOG_SIZE = 0x20

BASE_SYM = '__imp_??0exception@std@@QAE@ABV01@@Z'
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z'

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


def test_00420C80(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, IAT_BASE, BASE_SYM,
                      b'\xFF\x05' + _dword(log + L_BASE_COUNT)                # inc [base copies]
                      + b'\x89\x0D' + _dword(log + L_BASE_THIS)               # ecx -> base this
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_BASE_SRC)    # [esp+4] -> base src
                      + b'\xC7\x01' + _dword(0xAAAAAAAA)                      # mov [ecx], AAAA (base vtable)
                      + b'\xC2\x04\x00')                                      # ret 4
        _patch_import(h, IAT_STR, STR_SYM,
                      b'\xFF\x05' + _dword(log + L_STR_COUNT)                 # inc [string copies]
                      + b'\x89\x0D' + _dword(log + L_STR_THIS)                # ecx -> string this
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_STR_SRC)     # [esp+4] -> string src
                      + b'\xC7\x01' + _dword(0xBBBBBBBB)                      # mov [ecx], BBBB
                      + b'\xC7\x41\x04' + _dword(0xCCCCCCCC)                  # mov [ecx+4], CCCC
                      + b'\xC7\x41\x08' + _dword(0xDDDDDDDD)                  # mov [ecx+8], DDDD
                      + b'\xC2\x04\x00')                                      # ret 4
        this = h.alloc(0x40, bytes(0x40))
        src = h.alloc(0x40, bytes(0x40))
        SRC = bytes(range(0x40))

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(this, b'\x11' * 0x40)
            h.uc.mem_write(src, SRC)

        setup()
        diffs = h.compare(VF, args=[src], regs={UC_X86_REG_ECX: this})
        if diffs:
            return diffs
        setup()
        res = h.call(VF, args=[src], regs={UC_X86_REG_ECX: this})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != this:
            return ['the copy is returned as %08X' % res['eax']]
        if _u32(h, log + L_BASE_COUNT) != 1:
            return ['the base was copied %d times' % _u32(h, log + L_BASE_COUNT)]
        if _u32(h, log + L_BASE_THIS) != this or _u32(h, log + L_BASE_SRC) != src:
            return ['the base copy went to %08X from %08X'
                    % (_u32(h, log + L_BASE_THIS), _u32(h, log + L_BASE_SRC))]
        if _u32(h, log + L_STR_COUNT) != 1:
            return ['the message was copied %d times' % _u32(h, log + L_STR_COUNT)]
        if _u32(h, log + L_STR_THIS) != this + 0xc or _u32(h, log + L_STR_SRC) != src + 0xc:
            return ['the message copy went to %08X from %08X'
                    % (_u32(h, log + L_STR_THIS), _u32(h, log + L_STR_SRC))]
        if _u32(h, this) != VTABLE:
            return ['the vtable is %08X' % _u32(h, this)]
        for i, want in enumerate((0xBBBBBBBB, 0xCCCCCCCC, 0xDDDDDDDD)):
            if _u32(h, this + 0xc + i * 4) != want:
                return ['this+%X is %08X' % (0xc + i * 4, _u32(h, this + 0xc + i * 4))]
        if bytes(h.uc.mem_read(src, 0x40)) != SRC:
            return ['the source changed']
        if h.uc.mem_read(this + 0x18, 0x28) != b'\x11' * 0x28:
            return ['bytes past the copy changed']
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
