"""sub_00431100 (size 80, ECX thiscall, ret 4): reads the capacity into +4 and the size into +8 from the stream,
asks the span setter 0x4310A0 for the size, reads the payload into *this and returns the stream reference with
AL forced to 1.  The stream is replaced by a recording read stub in both IAT copies, the setter by a stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00431100
IAT_READ = 0x006071A0
SETTER = 0x004310A0

LOG_CALLS = 0x00
LOG_STREAM = 0x04
LOG_BUF = 0x08
LOG_N = 0x0C
LOG_SET = 0x10
LOG_SET_THIS = 0x14
LOG_SET_COUNT = 0x18
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
    """the original body reads the IAT copy at its own address, the rebuilt code the relinked slot"""
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def test_span_read(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, IAT_READ,
                      '__imp_?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z',
                      b'\x89\x0D' + _dword(log + LOG_STREAM)                       # mov [stream], ecx
                      + b'\x8B\x44\x24\x04'                                        # mov eax, [esp+4]
                      + b'\x8B\x54\x24\x08'                                        # mov edx, [esp+8]
                      + b'\x89\x05' + _dword(log + LOG_BUF)                        # mov [buf], eax
                      + b'\x89\x15' + _dword(log + LOG_N)                          # mov [n], edx
                      + b'\x89\x10'                                                # mov [eax], edx
                      + b'\xFF\x05' + _dword(log + LOG_CALLS)                      # inc [calls]
                      + b'\x8B\x05' + _dword(log + LOG_STREAM)                     # mov eax, [stream]
                      + b'\xC2\x08\x00')                                           # ret 8
        _patch(h, SETTER,
               b'\x89\x0D' + _dword(log + LOG_SET_THIS)                            # mov [set this], ecx
               + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_SET_COUNT)             # [esp+4] -> count
               + b'\xFF\x05' + _dword(log + LOG_SET)                               # inc [set]
               + b'\xC2\x04\x00')                                                  # ret 4
        obj = h.alloc(0x40, bytes(0x40))
        payload = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(obj, _dword(payload))
        stream = 0x2F000010
        diffs = h.compare(VF, args=[stream], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(obj + 4, bytes(8))
        h.uc.mem_write(payload, bytes(0x10))
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(VF, args=[stream], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_CALLS) != 3:
            return ['read called %d times' % _u32(h, log + LOG_CALLS)]
        if _u32(h, log + LOG_STREAM) != stream:
            return ['stream is %08X' % _u32(h, log + LOG_STREAM)]
        if _u32(h, log + LOG_BUF) != payload or _u32(h, log + LOG_N) != 4:
            return ['last read on %08X of %d bytes' % (_u32(h, log + LOG_BUF), _u32(h, log + LOG_N))]
        if _u32(h, obj + 4) != 4 or _u32(h, obj + 8) != 4:
            return ['span holds capacity %d size %d' % (_u32(h, obj + 4), _u32(h, obj + 8))]
        if _u32(h, payload) != 4:
            return ['payload starts with %08X' % _u32(h, payload)]
        if _u32(h, log + LOG_SET) != 1 or _u32(h, log + LOG_SET_THIS) != obj or _u32(h, log + LOG_SET_COUNT) != 4:
            return ['setter called %d times on %08X with %d' % (_u32(h, log + LOG_SET),
                                                                _u32(h, log + LOG_SET_THIS),
                                                                _u32(h, log + LOG_SET_COUNT))]
        if res['eax'] != ((stream & 0xFFFFFF00) | 1):
            return ['returned %08X' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
