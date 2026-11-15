"""sub_00422CE0 (size 106, cdecl, 3 stack args): copies the 0x64-byte records of [first, last) into dst through the
MSVCP80 string copy (IAT 0x607334, destination +0, source +0) and the block copy 0x00421150 (destination +0x1C,
source +0x1C); a null destination only advances.  Returns the destination past the last record."""
import struct

RECORD = 0x64
IAT_STR = 0x00607334
BLOCK = 0x00421150

L_STR_CALLS = 0x00
L_STR_ARGS = 0x08
L_BLK_CALLS = 0x28
L_BLK_ARGS = 0x30
LOG_SIZE = 0x60

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


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _patch_callee(h, address, code):
    _patch_thunk(h, address, code)
    target = h.symbols.get('_sub_%08X' % address)
    if target is not None and target != address:
        _patch_thunk(h, target, code)


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _pair_stub(log, calls, args, marker):
    return (b'\xFF\x05' + _dword(log + calls)                               # inc [calls]
            + b'\xA1' + _dword(log + calls)                                 # mov eax, [calls]
            + b'\x48'                                                       # dec eax (call index)
            + b'\x89\x0C\xC5' + _dword(log + args)                          # ecx -> dst[index]
            + b'\x8B\x54\x24\x04'                                           # mov edx, [esp+4] (src)
            + b'\x89\x14\xC5' + _dword(log + args + 4)                      # edx -> src[index]
            + marker
            + b'\xC2\x04\x00')                                              # ret 4


def test_00422CE0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, IAT_STR, STR_SYM, _pair_stub(
            log, L_STR_CALLS, L_STR_ARGS,
            b'\xC7\x01' + _dword(0xAAAAAAAA)                                # mov [ecx], AAAA
            + b'\xC7\x41\x08' + _dword(0xBBBBBBBB)))                        # mov [ecx+8], BBBB
        _patch_callee(h, BLOCK, _pair_stub(
            log, L_BLK_CALLS, L_BLK_ARGS, b'\xC7\x01' + _dword(0xCCCCCCCC)))  # mov [ecx], CCCC
        first = h.alloc(4 * RECORD, b'\x22' * (4 * RECORD))
        dst = h.alloc(5 * RECORD, b'\x77' * (5 * RECORD))
        for count, null_dst in ((1, False), (3, False), (4, False), (1, True)):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(dst, b'\x77' * (5 * RECORD))
            last = first + count * RECORD
            out = 0 if null_dst else dst
            diffs = h.compare(0x00422CE0, args=[first, last, out], setup=lambda hh: setup(), ret='eax')
            if diffs:
                return ['%d records%s: %s' % (count, ' null' if null_dst else '', d) for d in diffs]
            setup()
            res = h.call(0x00422CE0, args=[first, last, out])
            if res['fault']:
                return ['%d records%s: replacement faulted: %s'
                        % (count, ' null' if null_dst else '', res['fault'])]
            if res['eax'] != out + count * RECORD:
                return ['%d records%s: returned %08X' % (count, ' null' if null_dst else '', res['eax'])]
            if null_dst:
                if _u32(h, log + L_STR_CALLS) or _u32(h, log + L_BLK_CALLS):
                    return ['a null destination was written through anyway']
                if bytes(h.uc.mem_read(dst, 4 * RECORD)) != b"\x77" * (4 * RECORD):
                    return ['a null destination changed the output']
                continue
            if _u32(h, log + L_STR_CALLS) != count or _u32(h, log + L_BLK_CALLS) != count:
                return ['%d records: %d strings and %d blocks copied'
                        % (count, _u32(h, log + L_STR_CALLS), _u32(h, log + L_BLK_CALLS))]
            for i in range(count):
                got = (_u32(h, log + L_STR_ARGS + 8 * i), _u32(h, log + L_STR_ARGS + 8 * i + 4))
                if got != (dst + i * RECORD, first + i * RECORD):
                    return ['string %d copied from (%08X, %08X)' % (i, got[0], got[1])]
                got = (_u32(h, log + L_BLK_ARGS + 8 * i), _u32(h, log + L_BLK_ARGS + 8 * i + 4))
                if got != (dst + i * RECORD + 0x1C, first + i * RECORD + 0x1C):
                    return ['block %d copied from (%08X, %08X)' % (i, got[0], got[1])]
                if _u32(h, dst + i * RECORD) != 0xAAAAAAAA or _u32(h, dst + i * RECORD + 8) != 0xBBBBBBBB:
                    return ['record %d: the string was not copied to +0/+8' % i]
                if _u32(h, dst + i * RECORD + 0x1C) != 0xCCCCCCCC:
                    return ['record %d: the block was not copied to +0x1C' % i]
                if h.uc.mem_read(dst + i * RECORD + 0x10, 1) != b'\x77':
                    return ['record %d: something outside the two fields changed' % i]
            if bytes(h.uc.mem_read(dst + count * RECORD, RECORD)) != b'\x77' * RECORD:
                return ['%d records: the output went past the last one' % count]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
