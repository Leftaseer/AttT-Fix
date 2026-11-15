"""CSimpleAnimation vf48 (0x0042A850): with +0x49 clear the input EAX passes through; otherwise 0x4AC890 is called
when +0x1E4 is set and the argument goes to slot 0xCC of the object at +0x1C4, whose result is returned.  The
release and the vtable target are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

VF = 0x0042A850
RELEASE = 0x004AC890

LOG_RELEASE_THIS = 0x00
LOG_RELEASE_COUNT = 0x04
LOG_VF_THIS = 0x08
LOG_VF_ARG = 0x0C
LOG_VF_COUNT = 0x10

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _release_stub(h, log):
    code = (b'\x89\x0D' + struct.pack('<I', log + LOG_RELEASE_THIS)     # mov [this], ecx
            + b'\xFF\x05' + struct.pack('<I', log + LOG_RELEASE_COUNT)  # inc [count]
            + b'\xC3')                                                  # ret
    saved[RELEASE] = bytes(h.uc.mem_read(RELEASE, len(code)))
    h.uc.mem_write(RELEASE, code)
    h.uc.ctl_remove_cache(RELEASE, RELEASE + len(code))


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


def test_csimple_vf48(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        _release_stub(h, log)
        vf = _vf_stub(h, log, 0xABCD0001)
        table = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(table + 0xCC, struct.pack('<I', vf))
        for flag49, flag1e4 in ((0, 0), (0, 1), (1, 0), (1, 1)):
            h.uc.mem_write(log, bytes(0x20))
            inner = h.alloc(0x40, bytes(0x40))
            h.uc.mem_write(inner, struct.pack('<I', table))
            obj = h.alloc(0x200, bytes(0x200))
            h.uc.mem_write(obj + 0x49, bytes([flag49]))
            h.uc.mem_write(obj + 0x1E4, bytes([flag1e4]))
            h.uc.mem_write(obj + 0x1C4, struct.pack('<I', inner))
            arg, in_eax = 0x3F800000, 0xFEEDFACE
            diffs = h.compare(VF, args=[arg], regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
            if diffs:
                return ['%d/%d: %s' % (flag49, flag1e4, d) for d in diffs]
            h.uc.mem_write(log, bytes(0x20))
            res = h.call(VF, args=[arg], regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
            if res['fault']:
                return ['%d/%d: replacement faulted: %s' % (flag49, flag1e4, res['fault'])]
            tag = '%d/%d' % (flag49, flag1e4)
            if _u32(h, log + LOG_RELEASE_COUNT) != int(flag49 and flag1e4):
                return ['%s: release called %d times' % (tag, _u32(h, log + LOG_RELEASE_COUNT))]
            if flag49 and flag1e4 and _u32(h, log + LOG_RELEASE_THIS) != obj:
                return ['%s: release called on %08X' % (tag, _u32(h, log + LOG_RELEASE_THIS))]
            if _u32(h, log + LOG_VF_COUNT) != int(flag49):
                return ['%s: slot called %d times' % (tag, _u32(h, log + LOG_VF_COUNT))]
            if flag49:
                if _u32(h, log + LOG_VF_THIS) != inner or _u32(h, log + LOG_VF_ARG) != arg:
                    return ['%s: slot called on %08X with %08X' % (tag, _u32(h, log + LOG_VF_THIS),
                                                                   _u32(h, log + LOG_VF_ARG))]
            want = 0xABCD0001 if flag49 else in_eax
            if res['eax'] != want:
                return ['%s: returned %08X, want %08X' % (tag, res['eax'], want)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
