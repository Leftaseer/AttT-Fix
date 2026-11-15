"""CInvSimpleAnimation vf48 (0x0042AEE0): with +0x49 clear the input EAX passes through; otherwise the step count
(+0x1C8 minus +0x1CC, less one) goes to +0x1D8 of the object at +0x1C4 and the argument to its slot 0xCC, whose
result is returned.  The vtable target is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

VF = 0x0042AEE0

LOG_VF_THIS = 0x00
LOG_VF_ARG = 0x04
LOG_VF_COUNT = 0x08

def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _vf_stub(h, log, marker):
    code = (b'\x89\x0D' + struct.pack('<I', log + LOG_VF_THIS)         # mov [this], ecx
            + b'\x8B\x44\x24\x04'                                       # mov eax, [esp+4]
            + b'\xA3' + struct.pack('<I', log + LOG_VF_ARG)             # mov [arg], eax
            + b'\xFF\x05' + struct.pack('<I', log + LOG_VF_COUNT)       # inc [count]
            + b'\xB8' + struct.pack('<I', marker)                       # mov eax, marker
            + b'\xC2\x04\x00')                                          # ret 4
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def test_cinv_vf48(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        vf = _vf_stub(h, log, 0xABCD0003)
        table = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(table + 0xCC, struct.pack('<I', vf))
        for flag49, a, b in ((0, 10, 3), (1, 10, 3), (1, 0, 1)):
            h.uc.mem_write(log, bytes(0x20))
            inner = h.alloc(0x200, bytes(0x200))
            h.uc.mem_write(inner, struct.pack('<I', table))
            obj = h.alloc(0x200, bytes(0x200))
            h.uc.mem_write(obj + 0x49, bytes([flag49]))
            h.uc.mem_write(obj + 0x1C4, struct.pack('<I', inner))
            h.uc.mem_write(obj + 0x1C8, struct.pack('<I', a))
            h.uc.mem_write(obj + 0x1CC, struct.pack('<I', b))
            arg, in_eax = 0x3F800000, 0xFEEDFACE
            diffs = h.compare(VF, args=[arg], regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
            if diffs:
                return ['%d %d/%d: %s' % (flag49, a, b, d) for d in diffs]
            h.uc.mem_write(log, bytes(0x20))
            res = h.call(VF, args=[arg], regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
            if res['fault']:
                return ['%d %d/%d: replacement faulted: %s' % (flag49, a, b, res['fault'])]
            tag = '%d %d/%d' % (flag49, a, b)
            if _u32(h, log + LOG_VF_COUNT) != int(flag49):
                return ['%s: slot called %d times' % (tag, _u32(h, log + LOG_VF_COUNT))]
            if flag49:
                if _u32(h, log + LOG_VF_THIS) != inner or _u32(h, log + LOG_VF_ARG) != arg:
                    return ['%s: slot called on %08X with %08X' % (tag, _u32(h, log + LOG_VF_THIS),
                                                                   _u32(h, log + LOG_VF_ARG))]
                want_count = (a - b - 1) & 0xFFFFFFFF
                if _u32(h, inner + 0x1D8) != want_count:
                    return ['%s: count %08X, want %08X' % (tag, _u32(h, inner + 0x1D8), want_count)]
            want = 0xABCD0003 if flag49 else in_eax
            if res['eax'] != want:
                return ['%s: returned %08X, want %08X' % (tag, res['eax'], want)]
    finally:
        h.heap_ptr = heap0
    return None
