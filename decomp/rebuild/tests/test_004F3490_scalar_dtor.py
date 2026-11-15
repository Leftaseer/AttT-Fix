"""Scalar deleting destructor (0x004F3490): the object at +0xC is released (0x4F1B50), the pointer at +0x10 is
freed (0x5E3E9C) and cleared and, with the low flag bit set, the object itself is freed; the object is
returned.  Both callees are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004F3490
RELEASE = 0x004F1B50
FREE = 0x005E3E9C

LOG_RELEASE = 0x00
LOG_RELEASE_THIS = 0x04
LOG_FREE = 0x08
LOG_FREE_1 = 0x0C
LOG_FREE_2 = 0x10
LOG_SIZE = 0x20

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _dword(addr):
    return struct.pack('<I', addr)


def test_scalar_deleting_dtor(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, RELEASE,
               b'\x89\x0D' + _dword(log + LOG_RELEASE_THIS)                # mov [log+4], ecx
               + b'\xFF\x05' + _dword(log + LOG_RELEASE)                   # inc [log]
               + b'\xC3')                                                  # ret
        _patch(h, FREE,
               b'\x8B\x05' + _dword(log + LOG_FREE)                        # mov eax, [log+8]
               + b'\x8B\x4C\x24\x04'                                       # mov ecx, [esp+4]
               + b'\x89\x0C\x85' + _dword(log + LOG_FREE_1)                # mov [eax*4+log+0C], ecx
               + b'\xFF\x05' + _dword(log + LOG_FREE)                      # inc [log+8]
               + b'\xC3')                                                  # ret
        for flags in (0, 1):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            payload = h.alloc(0x10, bytes(0x10))
            obj = h.alloc(0x100, bytes(0x100))
            h.uc.mem_write(obj + 0x10, _dword(payload))
            diffs = h.compare(FN, args=[flags], regs={UC_X86_REG_ECX: obj})
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            h.uc.mem_write(log, bytes(LOG_SIZE))
            res = h.call(FN, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            tag = 'flags %d' % flags
            if _u32(h, log + LOG_RELEASE) != 1 or _u32(h, log + LOG_RELEASE_THIS) != obj + 0xC:
                return ['%s: release %d on %08X' % (tag, _u32(h, log + LOG_RELEASE),
                                                    _u32(h, log + LOG_RELEASE_THIS))]
            if _u32(h, log + LOG_FREE) != 1 + flags:
                return ['%s: free called %d times' % (tag, _u32(h, log + LOG_FREE))]
            if _u32(h, log + LOG_FREE_1) != payload:
                return ['%s: freed %08X, want %08X' % (tag, _u32(h, log + LOG_FREE_1), payload)]
            if flags and _u32(h, log + LOG_FREE_2) != obj:
                return ['%s: freed this as %08X' % (tag, _u32(h, log + LOG_FREE_2))]
            if _u32(h, obj + 0x10) != 0:
                return ['%s: member not cleared' % tag]
            if res['eax'] != obj:
                return ['%s: returned %08X' % (tag, res['eax'])]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
