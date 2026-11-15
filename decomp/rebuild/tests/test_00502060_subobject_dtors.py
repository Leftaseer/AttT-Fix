"""sub_00502060 / sub_00503170 (size 80, ECX thiscall, ret 4): scalar deleting destructors.  The value in the
object at +0x14 goes through 0x4FB710 (or 0x502E40) on the sub-object at +0x10, the sub-object is freed and
+0x14/+0x18 are cleared; with bit 0 of the flags set this object is freed as well.  All callees are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

PAIRS = ((0x00502060, 0x004FB710), (0x00503170, 0x00502E40))
FREE = 0x005E3E9C

LOG_THIS = 0x00
LOG_VALUE = 0x04
LOG_OBJECT = 0x08
LOG_FREE_COUNT = 0x0C
LOG_FREE_SEQ = 0x14
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


def _free_stub(h, log):
    _patch(h, FREE,
           b'\x8B\x15' + _dword(log + LOG_FREE_COUNT)                          # mov edx, [count]
           + b'\x8B\x44\x24\x04'                                               # mov eax, [esp+4]
           + b'\x89\x04\x95' + _dword(log + LOG_FREE_SEQ)                      # mov [edx*4+seq], eax
           + b'\xFF\x05' + _dword(log + LOG_FREE_COUNT)                        # inc [count]
           + b'\x33\xC0'                                                       # xor eax, eax
           + b'\xC3')                                                          # ret


def test_subobject_dtors(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _free_stub(h, log)
        for entry, release in PAIRS:
            _patch(h, release,
                   b'\x89\x0D' + _dword(log + LOG_THIS)                        # mov [this], ecx
                   + b'\x8B\x44\x24\x08\xA3' + _dword(log + LOG_VALUE)          # [esp+8] -> value
                   + b'\x8B\x44\x24\x0C\xA3' + _dword(log + LOG_OBJECT)         # [esp+C] -> object
                   + b'\xC2\x0C\x00')                                           # ret 0xC
            for flags in (0, 1):
                tag = '%08X flags %d' % (entry, flags)
                h.uc.mem_write(log, bytes(LOG_SIZE))
                obj = h.alloc(0x40, bytes(0x40))
                field = h.alloc(0x40, bytes(0x40))
                h.uc.mem_write(field, _dword(0x7777))
                h.uc.mem_write(obj + 0x14, _dword(field))
                h.uc.mem_write(obj + 0x18, _dword(0xDEADBEEF))
                diffs = h.compare(entry, args=[flags], regs={UC_X86_REG_ECX: obj})
                if diffs:
                    return ['%s: %s' % (tag, d) for d in diffs]
                h.uc.mem_write(log, bytes(LOG_SIZE))
                res = h.call(entry, args=[flags], regs={UC_X86_REG_ECX: obj})
                if res['fault']:
                    return ['%s: replacement faulted: %s' % (tag, res['fault'])]
                if _u32(h, log + LOG_THIS) != obj + 0x10 or _u32(h, log + LOG_VALUE) != 0x7777:
                    return ['%s: release called on %08X with value %08X' % (tag, _u32(h, log + LOG_THIS),
                                                                           _u32(h, log + LOG_VALUE))]
                if _u32(h, log + LOG_OBJECT) != field:
                    return ['%s: release object is %08X' % (tag, _u32(h, log + LOG_OBJECT))]
                if _u32(h, obj + 0x14) != 0 or _u32(h, obj + 0x18) != 0:
                    return ['%s: pointers are %08X and %08X' % (tag, _u32(h, obj + 0x14), _u32(h, obj + 0x18))]
                seq = [_u32(h, log + LOG_FREE_SEQ + 4 * i) for i in range(_u32(h, log + LOG_FREE_COUNT))]
                want = [field] + ([obj] if flags & 1 else [])
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
