"""nSpell::Regeneration::vf34 (0x00573D40): forwards to the regeneration's end step 0x00573AE0, passing the spell by
address the way the original thunk does; whatever EAX that call leaves is the result.  0x00573AE0 is replaced by a
stub that records the spell and the value it was passed by address, and returns a fixed value."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THUNK = 0x00573D40
STEP = 0x00573AE0
RESULT = 0x12345678

LOG_THIS = 0x00
LOG_REF = 0x04
LOG_VALUE = 0x08
LOG_COUNT = 0x0C


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _mov_eax(value):
    return b'\xB8' + struct.pack('<I', value)


def _mov_eax_arg(index):
    return b'\x8B\x44\x24' + bytes([4 * index])


def _store_eax(addr):
    return b'\xA3' + struct.pack('<I', addr)


def _store_ecx(addr):
    return b'\x89\x0D' + struct.pack('<I', addr)


def _store_edx(addr):
    return b'\x89\x15' + struct.pack('<I', addr)


def _inc(addr):
    return b'\xFF\x05' + struct.pack('<I', addr)


def _ret4():
    return b'\xC2\x04\x00'


def _patch(h, address, code, saved):
    if address not in saved:
        saved[address] = bytes(h.uc.mem_read(address, 32))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, log):
    _patch(h, STEP,
           _store_ecx(log + LOG_THIS)
           + _mov_eax_arg(1) + _store_eax(log + LOG_REF)       # the pointer the spell came in
           + b'\x8B\x10' + _store_edx(log + LOG_VALUE)        # the value at it
           + _mov_eax(RESULT)
           + _inc(log + LOG_COUNT)
           + _ret4(), _stub.saved)


_stub.saved = {}


def test_regeneration_vf34(h):
    _stub.saved = {}
    heap0 = h.heap_ptr
    try:
        for value in (0x20000100, 0x1234, 0):
            log = h.alloc(0x20, bytes(0x20))
            _stub(h, log)
            diffs = h.compare(THUNK, regs={UC_X86_REG_ECX: value}, ret='eax')
            if diffs:
                return ['spell %08X: %s' % (value, d) for d in diffs]
            res = h.call(THUNK, regs={UC_X86_REG_ECX: value})
            if res['fault']:
                return ['spell %08X: replacement faulted: %s' % (value, res['fault'])]
            if res['eax'] != RESULT:
                return ['spell %08X: returned %08X' % (value, res['eax'])]
            if _u32(h, log + LOG_COUNT) != 1:
                return ['spell %08X: forwarded %d times' % (value, _u32(h, log + LOG_COUNT))]
            if _u32(h, log + LOG_THIS) != value or _u32(h, log + LOG_VALUE) != value:
                return ['spell %08X: forwarded %08X, by address %08X' % (value, _u32(h, log + LOG_THIS),
                                                                         _u32(h, log + LOG_VALUE))]
            h.heap_ptr = heap0
    finally:
        for address, code in _stub.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + 32)
        _stub.saved = {}
        h.heap_ptr = heap0
    return None
