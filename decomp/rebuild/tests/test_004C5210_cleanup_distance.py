"""0x4C5210 singleton cleanup and 0x547A80 squared x/z distance."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

CLEANUP = 0x004C5210
DISTANCE = 0x00547A80
DESTROY = 0x004C4D60
FREE = 0x005E3E9C
MAIN_SLOT = 0x006CA4AC
SECONDARY_SLOT = 0x006CA4B4
OTHER_SLOT = 0x006CA4A4
saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _float(value):
    return struct.pack('<f', value)


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


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _inc(log):
    return b'\xFF\x05' + _dword(log)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _release_object(h, log):
    stub = _stub(h, _arg(4, log) + _inc(log + 4) + b'\xC2\x04\x00')
    vtable = h.alloc(0x0c, bytes(0x0c))
    h.uc.mem_write(vtable + 8, _dword(stub))
    return h.alloc(4, _dword(vtable))


def test_singleton_cleanup(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x30, bytes(0x30))
        _hook(h, DESTROY, b'\x89\x0D' + _dword(log) + _inc(log + 4) + b'\xC3')
        _hook(h, FREE, _arg(4, log + 8) + _inc(log + 0x0c) + b'\xC3')
        secondary = h.alloc(0x20, bytes(0x20))
        main = _release_object(h, log + 0x10)
        other = _release_object(h, log + 0x18)
        for address, value in ((SECONDARY_SLOT, secondary), (MAIN_SLOT, main), (OTHER_SLOT, other)):
            _patch(h, address, _dword(value))
        problems = []
        for with_secondary, with_other in ((True, True), (False, True), (True, False), (False, False)):
            h.uc.mem_write(SECONDARY_SLOT, _dword(secondary if with_secondary else 0))
            h.uc.mem_write(MAIN_SLOT, _dword(main))
            h.uc.mem_write(OTHER_SLOT, _dword(other if with_other else 0))
            diffs = h.compare(CLEANUP, ret=None)
            label = 'secondary %d other %d' % (with_secondary, with_other)
            if diffs:
                problems += ['%s: %s' % (label, d) for d in diffs]
                continue
            h.uc.mem_write(log, bytes(0x30))
            result = h.call(CLEANUP)
            if result['fault']:
                problems.append('%s: %s' % (label, result['fault']))
                continue
            expected = (
                (0, secondary if with_secondary else 0, 'destructor object'),
                (4, int(with_secondary), 'destructor calls'),
                (8, secondary if with_secondary else 0, 'freed object'),
                (0x0c, int(with_secondary), 'free calls'),
                (0x10, main, 'main release object'), (0x14, 1, 'main release calls'),
                (0x18, other if with_other else 0, 'other release object'),
                (0x1c, int(with_other), 'other release calls'),
            )
            for offset, want, name in expected:
                got = _u32(h, log + offset)
                if got != want:
                    problems.append('%s: %s is %#x, want %#x' % (label, name, got, want))
            for address in (SECONDARY_SLOT, MAIN_SLOT, OTHER_SLOT):
                if _u32(h, address):
                    problems.append('%s: global %#x was not cleared' % (label, address))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _position_object(h, position):
    stub = _stub(h, b'\xB8' + _dword(position) + b'\xC3')
    vtable = h.alloc(0x6c, bytes(0x6c))
    h.uc.mem_write(vtable + 0x68, _dword(stub))
    return h.alloc(4, _dword(vtable))


def test_squared_xz_distance(h):
    heap0 = h.heap_ptr
    try:
        cases = (
            ((5.0, 99.0, 1.0), (2.0, 77.0, -3.0), 25.0),
            ((-1.5, 0.0, 2.25), (1.5, 8.0, -0.75), 18.0),
            ((2.0, 0.0, 3.0), (2.0, 5.0, 3.0), 0.0),
        )
        problems = []
        for a, b, want in cases:
            pa = h.alloc(12, b''.join(_float(v) for v in a))
            pb = h.alloc(12, b''.join(_float(v) for v in b))
            this = _position_object(h, pa)
            other = _position_object(h, pb)
            diffs = h.compare(DISTANCE, args=(other,), regs={UC_X86_REG_ECX: this}, ret='st0', mem=False)
            if diffs:
                problems += ['%r/%r: %s' % (a, b, d) for d in diffs]
                continue
            result = h.call(DISTANCE, args=(other,), regs={UC_X86_REG_ECX: this})
            if result['fault']:
                problems.append(result['fault'])
            elif result['st0'] != want:
                problems.append('%r/%r: got %r, want %r' % (a, b, result['st0'], want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
