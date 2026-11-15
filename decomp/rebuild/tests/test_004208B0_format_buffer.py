"""sub_004208B0 (size 96, stdcall, 16 bytes of arguments, EAX result): formats into the buffer arg 1 of size arg 2
with _vsnprintf (MSVCR80 IAT 0x607398) over (buffer, size - 1, format arg 3, arguments arg 4): a zero size is
E_INVALIDARG (0x80070057) without a call, a negative or oversized result is E_INSUFFICIENT_BUFFER (0x8007007A) with
the last byte forced to zero, an exact fill of size - 1 also zeroes the last byte, and anything shorter just returns
S_OK (0)."""
import struct

VF = 0x004208B0
IAT_VSNPRINTF = 0x00607398

L_CALLS = 0x00
L_BUF = 0x04
L_CNT = 0x08
L_FMT = 0x0C
L_AP = 0x10
L_VALUE = 0x14
LOG_SIZE = 0x20

SYM = '__imp___vsnprintf'

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


def test_004208B0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, IAT_VSNPRINTF, SYM,
                      b'\xFF\x05' + _dword(log + L_CALLS)                       # inc [calls]
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_BUF)           # [esp+4] -> buffer
                      + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_CNT)           # [esp+8] -> count
                      + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_FMT)           # [esp+12] -> format
                      + b'\x8B\x44\x24\x10\xA3' + _dword(log + L_AP)            # [esp+16] -> arguments
                      + b'\xA1' + _dword(log + L_VALUE)                         # mov eax, [result]
                      + b'\xC3')                                                # ret
        buf = h.alloc(0x20, bytes(0x20))
        fmt = h.alloc(0x10, b'%d\x00' + bytes(0x0d))
        ap = h.alloc(0x10, bytes(range(0x10)))

        def setup(value):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_VALUE, _dword(value & 0xFFFFFFFF))
            h.uc.mem_write(buf, b'\xAA' * 0x20)

        cases = [('zero-size', 0, -1, 0x80070057, None),
                 ('negative', 5, -1, 0x8007007a, 0),
                 ('oversized', 5, 6, 0x8007007a, 0),
                 ('exact', 5, 4, 0, 0),
                 ('short', 5, 3, 0, None)]
        for name, size, value, want, term in cases:
            setup(value)
            diffs = h.compare(VF, args=[buf, size, fmt, ap])
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(value)
            res = h.call(VF, args=[buf, size, fmt, ap])
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != want:
                return ['%s: the result is %08X' % (name, res['eax'])]
            if size == 0:
                if _u32(h, log + L_CALLS) != 0:
                    return ['%s: the formatter was called' % name]
                if bytes(h.uc.mem_read(buf, 0x20)) != b'\xAA' * 0x20:
                    return ['%s: the buffer changed' % name]
                continue
            if _u32(h, log + L_CALLS) != 1:
                return ['%s: the formatter ran %d times' % (name, _u32(h, log + L_CALLS))]
            if _u32(h, log + L_BUF) != buf or _u32(h, log + L_CNT) != size - 1 \
                    or _u32(h, log + L_FMT) != fmt or _u32(h, log + L_AP) != ap:
                return ['%s: the formatter got (%08X, %d, %08X, %08X)'
                        % (name, _u32(h, log + L_BUF), _u32(h, log + L_CNT),
                           _u32(h, log + L_FMT), _u32(h, log + L_AP))]
            last = h.uc.mem_read(buf + size - 1, 1)[0]
            if term is not None and last != term:
                return ['%s: the last byte is %02X' % (name, last)]
            if term is None and last != 0xAA:
                return ['%s: the last byte was written as %02X' % (name, last)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
