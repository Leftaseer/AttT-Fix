"""CEngine::SetActive (0x449F80); Miles volume and CTimer::Resume are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00449F80
RESUME = 0x004E4200
VOLUME_SLOT = 0x00607868
VOLUME_SYM = '__imp___AIL_set_digital_master_volume_level@8'
SAVED_VOLUME = 0x006CA494
DRIVER = 0x006CA498
saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _import(h, slot, symbol, code):
    stub = _stub(h, code)
    for address in (slot, h.symbols[symbol]):
        _patch(h, address, _dword(stub))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _log_ecx(log, offset):
    return b'\x89\x0D' + _dword(log + offset) + b'\xFF\x05' + _dword(log + offset + 4)


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _case(h, log, obj, timer, active, volume_bits):
    h.uc.mem_write(timer + 0x18, b'\xAA')
    diffs = h.compare(FN, args=(active,), regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return ['active %d: %s' % (active, d) for d in diffs]
    h.uc.mem_write(log, bytes(0x20))
    h.uc.mem_write(timer + 0x18, b'\xAA')
    result = h.call(FN, args=(active,), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['active %d: %s' % (active, result['fault'])]

    problems = []
    expected = ((0x00, _u32(h, DRIVER), 'volume driver'), (0x04, 1, 'volume calls'),
                (0x08, volume_bits if active else 0, 'volume bits'),
                (0x0c, timer + 8 if active else 0, 'timer resume self'),
                (0x10, int(active), 'timer resume calls'))
    for offset, want, label in expected:
        got = _u32(h, log + offset)
        if got != want:
            problems.append('active %d: %s is %#x, want %#x' % (active, label, got, want))
    if bytes(h.uc.mem_read(timer + 0x18, 1)) != (b'\xAA' if active else b'\x00'):
        problems.append('active %d: timer running flag is wrong' % active)
    return problems


def test_engine_activation(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        obj = h.alloc(0x90, bytes(0x90))
        timer = h.alloc(0x20, bytes(0x20))
        volume_bits = 0x3FE00000
        h.uc.mem_write(obj + 0x7c, _dword(timer))
        _patch(h, SAVED_VOLUME, _dword(volume_bits))

        _import(h, VOLUME_SLOT, VOLUME_SYM, _arg(4, log + 0x00) + b'\xFF\x05' +
                _dword(log + 0x04) + _arg(8, log + 0x08) + b'\xC2\x08\x00')
        _hook(h, RESUME, _log_ecx(log, 0x0c) + b'\xC3')

        problems = []
        for active in (0, 1):
            problems += _case(h, log, obj, timer, active, volume_bits)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
