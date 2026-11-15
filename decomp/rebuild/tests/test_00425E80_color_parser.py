"""0x00425E80 (one string argument, ret 4): the "r:g:b" text parser.  The string is copied to a 256-byte buffer, split
by the delimiter at 0x00607EC8 (strtok) and each field converted (atoi); the result, returned in st0, is
b * 0x00607EC0 + g * 0x0068AE10 + r * 0x00607EB8 * 0x0068AE10 in double precision narrowed to a float.  Both
imports are stubs; the first token call reports the first buffer dword so the copy can be checked."""
import struct

THIS = 0x00425E80
STRTOK_SLOT = 0x006073CC
ATOI_SLOT = 0x006073C8
STRTOK_SYM = '__imp__strtok'
ATOI_SYM = '__imp__atoi'
DELIM = 0x00607EC8
SCALE_B = 0x00607EC0
SCALE_G = 0x0068AE10
SCALE_R = 0x00607EB8

L_TOKENS = 0x00
L_ATOIS = 0x04
L_HEAD = 0x08
L_DELIM = 0x0C
L_VALUES = 0x10
LOG_SIZE = 0x30

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


def _f64(h, addr):
    return struct.unpack('<d', h.uc.mem_read(addr, 8))[0]


def test_00425E80(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        token = h.alloc(0x20, b'7\0' + bytes(0x1D))
        _patch_import(h, STRTOK_SLOT, STRTOK_SYM,
                      b'\xFF\x05' + _dword(log + L_TOKENS)                     # inc [tokens]
                      + b'\x8B\x54\x24\x08'                                    # edx = delimiter
                      + b'\x89\x15' + _dword(log + L_DELIM)                    # -> [log+0C]
                      + b'\x8B\x44\x24\x04'                                    # eax = the buffer
                      + b'\x85\xC0'                                            # test eax, eax
                      + b'\x74\x13'                                            # jz  (continuation call)
                      + b'\x8B\x15' + _dword(log + L_TOKENS)                   # edx = call count
                      + b'\x83\xFA\x01'                                        # cmp edx, 1
                      + b'\x75\x08'                                            # jne (later call)
                      + b'\x8B\x10'                                            # edx = [buffer]
                      + b'\x89\x15' + _dword(log + L_HEAD)                     # first dword of the copy
                      + b'\xB8' + _dword(token)                                # eax = token text
                      + b'\xC3')                                               # cdecl: the caller cleans
        _patch_import(h, ATOI_SLOT, ATOI_SYM,
                      b'\xFF\x05' + _dword(log + L_ATOIS)                      # inc [atois]
                      + b'\xA1' + _dword(log + L_ATOIS)                        # eax = count
                      + b'\x48'                                                # dec eax
                      + b'\x8B\x04\x85' + _dword(log + L_VALUES)               # eax = values[i]
                      + b'\xC3')                                               # ret
        text = h.alloc(0x20, b'12:34:56\0' + bytes(0x17))
        r, g, b = 7, 9, 200
        h.uc.mem_write(log + L_VALUES, struct.pack('<III', r, g, b))

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_VALUES, struct.pack('<III', r, g, b))

        expected = struct.unpack('<f', struct.pack(
            '<f', b * _f64(h, SCALE_B) + g * _f64(h, SCALE_G) + r * _f64(h, SCALE_R) * _f64(h, SCALE_G)))[0]

        setup()
        diffs = h.compare(THIS, args=[text], ret='st0')
        if diffs:
            return [str(d) for d in diffs]
        setup()
        res = h.call(THIS, args=[text])
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if res['st0'] != expected:
            return ['returned %r, expected %r' % (res['st0'], expected)]
        if _u32(h, log + L_TOKENS) != 3 or _u32(h, log + L_ATOIS) != 3:
            return ['%d tokens, %d conversions' % (_u32(h, log + L_TOKENS), _u32(h, log + L_ATOIS))]
        if _u32(h, log + L_DELIM) != DELIM:
            return ['split by %08X' % _u32(h, log + L_DELIM)]
        if _u32(h, log + L_HEAD) != 0x333A3231:
            return ['the buffer starts with %08X' % _u32(h, log + L_HEAD)]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
