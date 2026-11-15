"""sub_004F7390 (size 80, ECX thiscall, ret 0x10): resets the object at +4 through 0x430CD0 and passes the four
integer arguments, converted to floats in their order, to 0x4CA820 at +0x1C.  Both callees are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x004F7390
RESET = 0x00430CD0
SETTER = 0x004CA820

LOG_RESET = 0x00
LOG_RESET_THIS = 0x04
LOG_SET = 0x08
LOG_SET_THIS = 0x0C
LOG_A = 0x10
LOG_B = 0x14
LOG_C = 0x18
LOG_D = 0x1C
LOG_SIZE = 0x40

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _float(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def test_volume_set(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, RESET,
               b'\x89\x0D' + _dword(log + LOG_RESET_THIS)                            # mov [reset this], ecx
               + b'\xFF\x05' + _dword(log + LOG_RESET)                               # inc [reset]
               + b'\x33\xC0'                                                         # xor eax, eax
               + b'\xC3')                                                            # ret
        _patch(h, SETTER,
               b'\x89\x0D' + _dword(log + LOG_SET_THIS)                              # mov [set this], ecx
               + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_A)                       # [esp+4] -> a
               + b'\x8B\x44\x24\x08\xA3' + _dword(log + LOG_B)                       # [esp+8] -> b
               + b'\x8B\x44\x24\x0C\xA3' + _dword(log + LOG_C)                       # [esp+C] -> c
               + b'\x8B\x44\x24\x10\xA3' + _dword(log + LOG_D)                       # [esp+10] -> d
               + b'\xFF\x05' + _dword(log + LOG_SET)                                 # inc [set]
               + b'\xB8\xBE\xBA\xFE\xCA'                                             # mov eax, CAFEBABE
               + b'\xC2\x10\x00')                                                    # ret 10
        obj = h.alloc(0x200, bytes(0x200))
        args = [-3, 7, 1 << 20, 123456]
        diffs = h.compare(VF, args=args, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(VF, args=args, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_RESET) != 1 or _u32(h, log + LOG_RESET_THIS) != obj + 4:
            return ['reset called %d times on %08X' % (_u32(h, log + LOG_RESET), _u32(h, log + LOG_RESET_THIS))]
        if _u32(h, log + LOG_SET) != 1 or _u32(h, log + LOG_SET_THIS) != obj + 0x1C:
            return ['setter called %d times on %08X' % (_u32(h, log + LOG_SET), _u32(h, log + LOG_SET_THIS))]
        got = [_u32(h, log + off) for off in (LOG_A, LOG_B, LOG_C, LOG_D)]
        want = [_float(float(v)) for v in args]
        if got != want:
            return ['floats are %r, want %r' % (got, want)]
        if res['eax'] != 0xCAFEBABE:
            return ['returned %08X' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
