"""sub_004210A0 (size 112, ECX thiscall, ret 4): copy constructor for a record with two strings - the one at +0 and
the one at +0x1C through the MSVCP80 string copy constructor (IAT 0x607334) - then the four dwords at +0x38, +0x3C,
+0x40 and +0x44 are copied.  Returns this."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x004210A0
IAT_STR = 0x00607334

L_CALLS = 0x00
L_THIS = 0x04
L_SRC = 0x0C
LOG_SIZE = 0x20

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


def test_004210A0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, IAT_STR, STR_SYM,
                      b'\xFF\x05' + _dword(log + L_CALLS)                       # inc [copies]
                      + b'\xA1' + _dword(log + L_CALLS)                         # mov eax, [copies]
                      + b'\x48'                                                 # dec eax (call index)
                      + b'\x89\x0C\x85' + _dword(log + L_THIS)                  # ecx -> this[index]
                      + b'\x8B\x54\x24\x04'                                     # mov edx, [esp+4] (src)
                      + b'\x89\x14\x85' + _dword(log + L_SRC)                   # edx -> src[index]
                      + b'\xC7\x01' + _dword(0xBBBBBBBB)                        # mov [ecx], BBBB
                      + b'\xC7\x41\x04' + _dword(0xCCCCCCCC)                    # mov [ecx+4], CCCC
                      + b'\xC7\x41\x08' + _dword(0xDDDDDDDD)                    # mov [ecx+8], DDDD
                      + b'\xC2\x04\x00')                                        # ret 4
        this = h.alloc(0x80, bytes(0x80))
        src = h.alloc(0x80, bytes(0x80))
        SRC = bytes(range(0x80))

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(this, b'\x11' * 0x80)
            h.uc.mem_write(src, SRC)

        diffs = h.compare(VF, args=[src], regs={UC_X86_REG_ECX: this}, setup=lambda hh: setup(), ret='eax')
        if diffs:
            return diffs
        setup()
        res = h.call(VF, args=[src], regs={UC_X86_REG_ECX: this})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != this:
            return ['the copy is returned as %08X' % res['eax']]
        if _u32(h, log + L_CALLS) != 2:
            return ['the strings were copied %d times' % _u32(h, log + L_CALLS)]
        for i, off in enumerate((0x00, 0x1c)):
            if _u32(h, log + L_THIS + 4 * i) != this + off or _u32(h, log + L_SRC + 4 * i) != src + off:
                return ['string %d copied from (%08X, %08X)'
                        % (i, _u32(h, log + L_THIS + 4 * i), _u32(h, log + L_SRC + 4 * i))]
        for base in (0x00, 0x1C):
            for i, want in enumerate((0xBBBBBBBB, 0xCCCCCCCC, 0xDDDDDDDD)):
                if _u32(h, this + base + 4 * i) != want:
                    return ['this+%X is %08X' % (base + 4 * i, _u32(h, this + base + 4 * i))]
        for i in range(4):
            if _u32(h, this + 0x38 + 4 * i) != _u32(h, src + 0x38 + 4 * i):
                return ['this+%X did not copy src+%X' % (0x38 + 4 * i, 0x38 + 4 * i)]
        if bytes(h.uc.mem_read(src, 0x80)) != SRC:
            return ['the source changed']
        if bytes(h.uc.mem_read(this + 0x0c, 0x10)) != b'\x11' * 0x10:
            return ['bytes +0x0C..+0x1B changed']
        if bytes(h.uc.mem_read(this + 0x28, 0x10)) != b'\x11' * 0x10:
            return ['bytes +0x28..+0x37 changed']
        if bytes(h.uc.mem_read(this + 0x48, 0x38)) != b'\x11' * 0x38:
            return ['bytes past the copy changed']
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
