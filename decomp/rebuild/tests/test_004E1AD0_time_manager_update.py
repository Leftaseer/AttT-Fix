"""nTime::TimeManager::Update (0x004E1AD0): the frame time reaches the base update and the time tick, then the clock's
two counters are formatted with "%02u:%02u" into a scratch buffer.  The two updates are recording stubs; sprintf is
observed through a hook on the emulated import, which checks the format string and both counters."""
import struct

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP

UPDATE = 0x004E1AD0
BASE = 0x00424D90
TICK = 0x004E1350
SPRINTF_SLOT = 0x006073D0

FORMAT = 0x00612658

LOG_BASE_THIS = 0x00
LOG_BASE_DT = 0x04
LOG_BASE_COUNT = 0x08
LOG_TICK_THIS = 0x0C
LOG_TICK_DT = 0x10
LOG_TICK_COUNT = 0x14
LOG_FMT = 0x18
LOG_MIN = 0x1C
LOG_SEC = 0x20
LOG_FMT_COUNT = 0x24
LOG_SIZE = 0x28


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _store_eax(addr):
    return b'\xA3' + struct.pack('<I', addr)


def _store_ecx(addr):
    return b'\x89\x0D' + struct.pack('<I', addr)


def _inc(addr):
    return b'\xFF\x05' + struct.pack('<I', addr)


def _mov_eax_arg(index):
    return b'\x8B\x44\x24' + bytes([4 * index])


def _ret4():
    return b'\xC2\x04\x00'


def _patch(h, address, code, saved):
    if address not in saved:
        saved[address] = bytes(h.uc.mem_read(address, len(code)))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _update_stub(log, this_slot, dt_slot, count_slot):
    return (_mov_eax_arg(1) + _store_eax(log + dt_slot)        # the float passed on the stack
            + _store_ecx(log + this_slot)
            + _inc(log + count_slot)
            + _ret4())


def _stubs(h, log):
    _patch(h, BASE, _update_stub(log, LOG_BASE_THIS, LOG_BASE_DT, LOG_BASE_COUNT), _stubs.saved)
    _patch(h, TICK, _update_stub(log, LOG_TICK_THIS, LOG_TICK_DT, LOG_TICK_COUNT), _stubs.saved)


_stubs.saved = {}


def _clock(h, minutes, seconds):
    clock = h.alloc(0x60, bytes(0x60))
    h.uc.mem_write(clock + 0x50, struct.pack('<II', minutes, seconds))
    obj = h.alloc(0x40, bytes(0x40))
    h.uc.mem_write(obj + 0x3C, struct.pack('<I', clock))
    return obj, clock


def test_time_manager_update(h):
    _stubs.saved = {}
    heap0 = h.heap_ptr
    sprintf = _u32(h, SPRINTF_SLOT)
    try:
        for dt in (0.016, 0.0, -0.5):
            for minutes, seconds in ((0, 0), (12, 34), (99, 59)):
                log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
                obj, clock = _clock(h, minutes, seconds)
                _stubs(h, log)

                def record(uc, addr, size, user, log=log):
                    esp = uc.reg_read(UC_X86_REG_ESP)   # the emulated import sees the arguments from ESP
                    args = struct.unpack('<IIII', uc.mem_read(esp, 16))
                    uc.mem_write(log + LOG_FMT, struct.pack('<III', args[1], args[2], args[3]))
                    uc.mem_write(log + LOG_FMT_COUNT, struct.pack('<I', _u32(h, log + LOG_FMT_COUNT) + 1))

                hook = h.uc.hook_add(UC_HOOK_CODE, record, begin=sprintf, end=sprintf + 1)
                try:
                    diffs = h.compare(UPDATE, args=[_bits(dt)], regs={UC_X86_REG_ECX: obj})
                finally:
                    h.uc.hook_del(hook)
                if diffs:
                    return ['dt %r clock %02d:%02d: %s' % (dt, minutes, seconds, d) for d in diffs]
                hook = h.uc.hook_add(UC_HOOK_CODE, record, begin=sprintf, end=sprintf + 1)
                try:
                    res = h.call(UPDATE, args=[_bits(dt)], regs={UC_X86_REG_ECX: obj})
                finally:
                    h.uc.hook_del(hook)
                if res['fault']:
                    return ['dt %r clock %02d:%02d: replacement faulted: %s' % (dt, minutes, seconds, res['fault'])]
                if _u32(h, log + LOG_BASE_COUNT) != 1 or _u32(h, log + LOG_BASE_THIS) != obj:
                    return ['dt %r: base update %d times on %08X' % (dt, _u32(h, log + LOG_BASE_COUNT),
                                                                     _u32(h, log + LOG_BASE_THIS))]
                if _u32(h, log + LOG_TICK_COUNT) != 1 or _u32(h, log + LOG_TICK_THIS) != obj:
                    return ['dt %r: time tick %d times on %08X' % (dt, _u32(h, log + LOG_TICK_COUNT),
                                                                   _u32(h, log + LOG_TICK_THIS))]
                if _u32(h, log + LOG_BASE_DT) != _bits(dt) or _u32(h, log + LOG_TICK_DT) != _bits(dt):
                    return ['dt %r: forwarded as %08X/%08X' % (dt, _u32(h, log + LOG_BASE_DT),
                                                               _u32(h, log + LOG_TICK_DT))]
                if _u32(h, log + LOG_FMT_COUNT) != 1:
                    return ['dt %r: formatted %d times' % (dt, _u32(h, log + LOG_FMT_COUNT))]
                if (_u32(h, log + LOG_FMT) != FORMAT or _u32(h, log + LOG_MIN) != minutes
                        or _u32(h, log + LOG_SEC) != seconds):
                    return ['dt %r: formatted %08X with %d,%d' % (dt, _u32(h, log + LOG_FMT),
                                                                 _u32(h, log + LOG_MIN), _u32(h, log + LOG_SEC))]
                h.heap_ptr = heap0
    finally:
        for address, code in _stubs.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        _stubs.saved = {}
        h.heap_ptr = heap0
    return None
