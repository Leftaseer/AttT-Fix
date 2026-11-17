"""0x585210 four-argument render-object constructor; setup calls and vtable slots are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00585210
BASE_CTOR = 0x00582350
SET_VALUE = 0x004AB870
FINISH = 0x005850A0
VTABLE = 0x0061DBEC
saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


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


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _log_ecx(log, offset):
    return b'\x89\x0D' + _dword(log + offset) + b'\xFF\x05' + _dword(log + offset + 4)


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def test_render_object_constructor(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        obj = h.alloc(0x218, bytes(0x218))
        args = tuple(h.alloc(0x10, bytes(0x10)) for _ in range(4))
        _hook(h, BASE_CTOR, _log_ecx(log, 0x00) + b'\xC3')
        _hook(h, SET_VALUE, _log_ecx(log, 0x14) + _arg(4, log + 0x1c) + b'\xC2\x04\x00')
        _hook(h, FINISH, _log_ecx(log, 0x38) + b'\xC3')
        static_setup = _stub(h, _log_ecx(log, 0x08) + _arg(4, log + 0x10) + b'\xC2\x04\x00')
        setup6c = _stub(h, _log_ecx(log, 0x20) + _arg(4, log + 0x28) + b'\xC2\x04\x00')
        setup98 = _stub(h, _log_ecx(log, 0x2c) + _arg(4, log + 0x34) + b'\xC2\x04\x00')
        for base in {VTABLE, h.to_rebuilt(VTABLE)}:
            for offset, stub in ((0x28, static_setup), (0x6c, setup6c), (0x98, setup98)):
                _patch(h, base + offset, _dword(stub))

        diffs = h.compare(FN, args=args, regs={UC_X86_REG_ECX: obj}, ret='eax', mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x40))
        result = h.call(FN, args=args, regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return [result['fault']]
        problems = []
        if result['eax'] != obj or _u32(h, obj) != VTABLE or _u32(h, obj + 0x214) != 0x0061DBE0:
            problems.append('constructor result or vtables are wrong')
        expected = ((0x00, obj, 'base self'), (0x04, 1, 'base calls'),
                    (0x08, obj, 'static setup self'), (0x0c, 1, 'static setup calls'), (0x10, args[3], 'fourth argument'),
                    (0x14, obj, 'value setup self'), (0x18, 1, 'value setup calls'), (0x1c, args[2], 'third argument'),
                    (0x20, obj, 'virtual 6c self'), (0x24, 1, 'virtual 6c calls'), (0x28, args[1], 'second argument'),
                    (0x2c, obj, 'virtual 98 self'), (0x30, 1, 'virtual 98 calls'), (0x34, args[0], 'first argument'),
                    (0x38, obj, 'finish self'), (0x3c, 1, 'finish calls'))
        for offset, want, name in expected:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (name, got, want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_render_object_sizing(h):
    heap0 = h.heap_ptr
    fn = 0x00585360
    try:
        log = h.alloc(0x70, bytes(0x70))
        obj = h.alloc(0x100, bytes(0x100))
        fifth = h.alloc(0x10, bytes(0x10))
        sixth = h.alloc(0x10, bytes(0x10))

        pair2c = _stub(h, _log_ecx(log, 0x00) + _arg(4, log + 0x08) + _arg(8, log + 0x0c) +
                       b'\xC2\x08\x00')
        pair38 = _stub(h, _log_ecx(log, 0x10) + _arg(4, log + 0x18) + _arg(8, log + 0x1c) +
                       b'\xC2\x08\x00')
        set68 = _stub(h, _log_ecx(log, 0x20) + _arg(4, log + 0x28) + _arg(8, log + 0x2c) +
                      b'\xC2\x08\x00')
        set94 = _stub(h, _log_ecx(log, 0x30) + _arg(4, log + 0x38) + _arg(8, log + 0x3c) +
                      b'\xC2\x08\x00')
        obj_vtable = h.alloc(0x98, bytes(0x98))
        for offset, stub in ((0x2c, pair2c), (0x38, pair38), (0x68, set68), (0x94, set94)):
            h.uc.mem_write(obj_vtable + offset, _dword(stub))
        h.uc.mem_write(obj, _dword(obj_vtable))

        get_height = _stub(h, _log_ecx(log, 0x50) + b'\xA1' + _dword(log + 0x64) + b'\xC3')
        get_width = _stub(h, _log_ecx(log, 0x48) + b'\xA1' + _dword(log + 0x60) + b'\xC3')
        child_vtable = h.alloc(0x18, bytes(0x18))
        h.uc.mem_write(child_vtable + 0x10, _dword(get_height))
        h.uc.mem_write(child_vtable + 0x14, _dword(get_width))
        child = h.alloc(4, _dword(child_vtable))
        other_child = h.alloc(0x10, bytes(0x10))
        table = h.alloc(8, _dword(other_child) + _dword(child))
        selector = h.alloc(0x44, bytes(0x44))
        h.uc.mem_write(selector + 0x38, _dword(table))
        h.uc.mem_write(selector + 0x40, _dword(1))
        h.uc.mem_write(obj + 0x44, _dword(selector))
        _hook(h, FINISH, _log_ecx(log, 0x40) + b'\xC3')

        problems = []
        for height, width, child_height, child_width in (
            (_bits(3.5), _bits(4.5), 480, 640),
            (0, 0, 480, 640),
            (0, 0, 0x80000000, 0xFFFFFFFF),
        ):
            h.uc.mem_write(log + 0x60, _dword(child_width))
            h.uc.mem_write(log + 0x64, _dword(child_height))
            args = (_bits(1.5), _bits(2.5), height, width, fifth, sixth)
            label = 'size %#x/%#x child %#x/%#x' % (height, width, child_height, child_width)
            diffs = h.compare(fn, args=args, regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
            if diffs:
                problems += ['%s: %s' % (label, d) for d in diffs]
                continue
            h.uc.mem_write(log, bytes(0x60))
            result = h.call(fn, args=args, regs={UC_X86_REG_ECX: obj})
            if result['fault']:
                problems.append('%s: %s' % (label, result['fault']))
                continue
            automatic_height = height == 0
            automatic_width = width == 0
            want_height = _bits(float(child_height)) if automatic_height else height
            want_width = _bits(float(child_width)) if automatic_width else width
            expected = ((0x00, obj, 'pair 2c self'), (0x04, 1, 'pair 2c calls'),
                        (0x08, sixth, 'sixth argument'), (0x0c, 0, 'pair 2c zero'),
                        (0x10, obj, 'pair 38 self'), (0x14, 1, 'pair 38 calls'),
                        (0x18, fifth, 'fifth argument'), (0x1c, 0, 'pair 38 zero'),
                        (0x20, obj, 'float 68 self'), (0x24, 1, 'float 68 calls'),
                        (0x28, _bits(1.5), 'first float'), (0x2c, _bits(2.5), 'second float'),
                        (0x30, obj, 'float 94 self'), (0x34, 1, 'float 94 calls'),
                        (0x38, want_height, 'final height'), (0x3c, want_width, 'final width'),
                        (0x40, obj, 'finish self'), (0x44, 1, 'finish calls'),
                        (0x48, child if automatic_width else 0, 'width child'),
                        (0x4c, int(automatic_width), 'width calls'),
                        (0x50, child if automatic_height else 0, 'height child'),
                        (0x54, int(automatic_height), 'height calls'))
            for offset, want, name in expected:
                got = _u32(h, log + offset)
                if got != want:
                    problems.append('%s: %s is %#x, want %#x' % (label, name, got, want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
