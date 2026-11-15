"""Span serialization (0x00431270): the dwords at +4 and +8 go to the stream as four bytes each, then the buffer
at +0 with the count from +4; AL is set and the rest of the result is what the stream's write returned.  The
ostream::write import is replaced by a recording stub in both import tables."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00431270
IAT_WRITE = 0x006071B0
WRITE_SYMBOL = '__imp_?write@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAEAAV12@PBDH@Z'

LOG_COUNT = 0x00
LOG_THIS = 0x04
LOG_BUFS = 0x10
LOG_SIZES = 0x20
LOG_SIZE = 0x40

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _dword(addr):
    return struct.pack('<I', addr)


def test_span_serialize(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        code = (b'\x89\x0D' + _dword(log + LOG_THIS)                          # mov [log+4], ecx
                + b'\x8B\x05' + _dword(log + LOG_COUNT)                       # mov eax, [log]
                + b'\x8B\x54\x24\x04'                                         # mov edx, [esp+4]
                + b'\x89\x14\x85' + _dword(log + LOG_BUFS)                    # mov [eax*4+bufs], edx
                + b'\x8B\x54\x24\x08'                                         # mov edx, [esp+8]
                + b'\x89\x14\x85' + _dword(log + LOG_SIZES)                   # mov [eax*4+sizes], edx
                + b'\xFF\x05' + _dword(log + LOG_COUNT)                       # inc [log]
                + b'\x8B\xC1'                                                 # mov eax, ecx
                + b'\xC2\x08\x00')                                            # ret 8
        stub = h.alloc(len(code), code)
        h.uc.ctl_remove_cache(stub, stub + len(code))
        for slot in (IAT_WRITE, h.symbols[WRITE_SYMBOL]):
            _patch(h, slot, _dword(stub))
        buffer = 0x2000BEEF
        obj = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(obj, _dword(buffer))
        h.uc.mem_write(obj + 4, _dword(5))
        h.uc.mem_write(obj + 8, _dword(0x11223344))
        stream = h.alloc(0x40, bytes(0x40))
        diffs = h.compare(FN, args=[stream], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(FN, args=[stream], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_COUNT) != 3:
            return ['wrote %d times' % _u32(h, log + LOG_COUNT)]
        if _u32(h, log + LOG_THIS) != stream:
            return ['stream is %08X' % _u32(h, log + LOG_THIS)]
        want = [(obj + 4, 4), (obj + 8, 4), (buffer, 5)]
        for i, (buf, size) in enumerate(want):
            if _u32(h, log + LOG_BUFS + 4 * i) != buf or _u32(h, log + LOG_SIZES + 4 * i) != size:
                return ['write %d is (%08X, %d), want (%08X, %d)' % (
                    i, _u32(h, log + LOG_BUFS + 4 * i), _u32(h, log + LOG_SIZES + 4 * i), buf, size)]
        if res['eax'] != ((stream & 0xFFFFFF00) | 1):
            return ['returned %08X' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
