"""StandardList vf slot (0x004CC6D0): sets the time t on the object 0x10 bytes before this and on this itself, in
that order, and returns the second call's result.  Both setters are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x004CC6D0
HEAD = 0x004CC460
SELF = 0x004F6180

LOG_HEAD_THIS = 0x00
LOG_HEAD_T = 0x04
LOG_HEAD_COUNT = 0x08
LOG_SELF_THIS = 0x0C
LOG_SELF_T = 0x10
LOG_SELF_COUNT = 0x14

saved = {}


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _stub(h, address, this_slot, t_slot, count_slot, result):
    code = (b'\x89\x0D' + struct.pack('<I', this_slot)                  # mov [this], ecx
            + b'\x8B\x44\x24\x04'                                       # mov eax, [esp+4]
            + b'\xA3' + struct.pack('<I', t_slot)                       # mov [t], eax
            + b'\xFF\x05' + struct.pack('<I', count_slot)               # inc [count]
            + b'\xB8' + struct.pack('<I', result)                       # mov eax, result
            + b'\xC2\x04\x00')                                          # ret 4
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def test_standard_list_vf(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        _stub(h, HEAD, log + LOG_HEAD_THIS, log + LOG_HEAD_T, log + LOG_HEAD_COUNT, 0x11110000)
        _stub(h, SELF, log + LOG_SELF_THIS, log + LOG_SELF_T, log + LOG_SELF_COUNT, 0x22220000)
        for t in (0.25, 0.0, -1.5):
            bits = _bits(t)
            obj = h.alloc(0x40, bytes(0x40))
            h.uc.mem_write(log, bytes(0x20))
            diffs = h.compare(VF, args=[bits], regs={UC_X86_REG_ECX: obj})
            if diffs:
                return ['t %r: %s' % (t, d) for d in diffs]
            h.uc.mem_write(log, bytes(0x20))
            res = h.call(VF, args=[bits], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['t %r: replacement faulted: %s' % (t, res['fault'])]
            if _u32(h, log + LOG_HEAD_COUNT) != 1:
                return ['t %r: head setter called %d times' % (t, _u32(h, log + LOG_HEAD_COUNT))]
            if _u32(h, log + LOG_HEAD_THIS) != obj - 0x10:
                return ['t %r: head setter got %08X, want %08X' % (t, _u32(h, log + LOG_HEAD_THIS), obj - 0x10)]
            if _u32(h, log + LOG_HEAD_T) != bits:
                return ['t %r: head setter got time %08X' % (t, _u32(h, log + LOG_HEAD_T))]
            if _u32(h, log + LOG_SELF_COUNT) != 1:
                return ['t %r: self setter called %d times' % (t, _u32(h, log + LOG_SELF_COUNT))]
            if _u32(h, log + LOG_SELF_THIS) != obj:
                return ['t %r: self setter got %08X, want %08X' % (t, _u32(h, log + LOG_SELF_THIS), obj)]
            if _u32(h, log + LOG_SELF_T) != bits:
                return ['t %r: self setter got time %08X' % (t, _u32(h, log + LOG_SELF_T))]
            if res['eax'] != 0x22220000:
                return ['t %r: returned %08X, want the self setter result 22220000' % (t, res['eax'])]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
