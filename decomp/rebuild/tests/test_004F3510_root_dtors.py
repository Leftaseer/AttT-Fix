"""sub_004F3510 / sub_004F4390 (size 96, ECX thiscall, ret 4): scalar deleting destructors.  The pointer at +0x14
is freed (if set), +0x14..+0x1C are cleared, the member at +4 is released through 0x4F1AC0 (or 0x4F20B0), the
pointer at +8 is freed and cleared and, with bit 0 of the flags set, the object itself is freed.  All callees are
recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

PAIRS = ((0x004F3510, 0x004F1AC0), (0x004F4390, 0x004F20B0))
FREE = 0x005E3E9C

LOG_RELEASE = 0x00
LOG_RELEASE_THIS = 0x04
LOG_FREE_COUNT = 0x08
LOG_FREE_SEQ = 0x10
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


def _install(h, log):
    _patch(h, FREE,
           b'\x8B\x15' + _dword(log + LOG_FREE_COUNT)                          # mov edx, [count]
           + b'\x8B\x44\x24\x04'                                               # mov eax, [esp+4]
           + b'\x89\x04\x95' + _dword(log + LOG_FREE_SEQ)                      # mov [edx*4+seq], eax
           + b'\xFF\x05' + _dword(log + LOG_FREE_COUNT)                        # inc [count]
           + b'\x33\xC0'                                                       # xor eax, eax
           + b'\xC3')                                                          # ret
    for _, release in PAIRS:
        _patch(h, release,
               b'\x89\x0D' + _dword(log + LOG_RELEASE_THIS)                    # mov [release this], ecx
               + b'\xFF\x05' + _dword(log + LOG_RELEASE)                       # inc [release]
               + b'\xC3')                                                      # ret


def test_root_dtors(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _install(h, log)
        for entry, _ in PAIRS:
            for flags, have_field in ((0, 1), (1, 1), (0, 0)):
                tag = '%08X flags %d field %d' % (entry, flags, have_field)
                h.uc.mem_write(log, bytes(LOG_SIZE))
                obj = h.alloc(0x40, bytes(0x40))
                field = h.alloc(0x10, bytes(0x10))
                spare = h.alloc(0x10, bytes(0x10))
                h.uc.mem_write(obj + 0x14, _dword(field if have_field else 0))
                h.uc.mem_write(obj + 0x18, _dword(0x11111111))
                h.uc.mem_write(obj + 0x1C, _dword(0x22222222))
                h.uc.mem_write(obj + 8, _dword(spare))
                diffs = h.compare(entry, args=[flags], regs={UC_X86_REG_ECX: obj})
                if diffs:
                    return ['%s: %s' % (tag, d) for d in diffs]
                h.uc.mem_write(log, bytes(LOG_SIZE))
                res = h.call(entry, args=[flags], regs={UC_X86_REG_ECX: obj})
                if res['fault']:
                    return ['%s: replacement faulted: %s' % (tag, res['fault'])]
                if _u32(h, log + LOG_RELEASE) != 1 or _u32(h, log + LOG_RELEASE_THIS) != obj + 4:
                    return ['%s: release called %d times on %08X' % (tag, _u32(h, log + LOG_RELEASE),
                                                                     _u32(h, log + LOG_RELEASE_THIS))]
                if any(_u32(h, obj + off) for off in (0x14, 0x18, 0x1C, 8)):
                    return ['%s: pointers are %08X %08X %08X %08X' % (tag, _u32(h, obj + 0x14), _u32(h, obj + 0x18),
                                                                      _u32(h, obj + 0x1C), _u32(h, obj + 8))]
                seq = [_u32(h, log + LOG_FREE_SEQ + 4 * i) for i in range(_u32(h, log + LOG_FREE_COUNT))]
                want = ([field] if have_field else []) + [spare] + ([obj] if flags & 1 else [])
                if seq != want:
                    return ['%s: freed %r, want %r' % (tag, [hex(x) for x in seq], [hex(x) for x in want])]
                if res['eax'] != obj:
                    return ['%s: returned %08X' % (tag, res['eax'])]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
