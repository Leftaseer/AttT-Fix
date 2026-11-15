"""std exception deleting destructor and small accessors around 0x427020:
0x00427020 (ECX, ret 4): vtable 0x00607B18, destroys the message string at +0xC (MSVCP80), the std::exception base,
then deletes on flag bit 0; returns this.
0x00427070 (ECX): the float at +0x94.
0x00427080 (ECX): writes (0, -1, -1) over 12 bytes.
0x004270A0 (ECX): puts the vtable 0x00608214 at +0.
0x004270B0 (ECX, ret 4): passes the argument on with +0x44 as this (0x00458B50)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VTABLE = 0x00607B18
IAT_STR_DTOR = 0x00607330
IAT_EXC_DTOR = 0x006073AC
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
EXC_DTOR_SYM = '__imp_??1exception@std@@UAE@XZ'

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _f(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    return stub


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def test_00427020(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        _patch_import(h, IAT_STR_DTOR, STR_DTOR_SYM,
                      b'\xFF\x05' + _dword(log) + b'\x89\x0D' + _dword(log + 4) + b'\xC3')
        _patch_import(h, IAT_EXC_DTOR, EXC_DTOR_SYM,
                      b'\xFF\x05' + _dword(log + 8) + b'\x89\x0D' + _dword(log + 0xc) + b'\xC3')
        delete = 0x005E3E9C
        _hook(h, delete, b'\xFF\x05' + _dword(log + 0x10)
              + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 0x14) + b'\xC3')
        obj = h.alloc(0x40, b'\x11' * 0x40)

        for flags in (0, 1, 2, 3):
            def setup():
                h.uc.mem_write(log, bytes(0x40))
                h.uc.mem_write(obj, b'\x11' * 0x40)

            setup()
            diffs = h.compare(0x00427020, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            setup()
            res = h.call(0x00427020, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['flags %d: returned %08X' % (flags, res['eax'])]
            if _u32(h, obj) != VTABLE:
                return ['flags %d: the vtable is %08X' % (flags, _u32(h, obj))]
            if _u32(h, log) != 1 or _u32(h, log + 4) != obj + 0xc:
                return ['flags %d: the string destructor got %08X (%d times)'
                        % (flags, _u32(h, log + 4), _u32(h, log))]
            if _u32(h, log + 8) != 1 or _u32(h, log + 0xc) != obj:
                return ['flags %d: the base destructor got %08X (%d times)'
                        % (flags, _u32(h, log + 0xc), _u32(h, log + 8))]
            want = 1 if flags & 1 else 0
            if _u32(h, log + 0x10) != want:
                return ['flags %d: the delete ran %d times' % (flags, _u32(h, log + 0x10))]
            if want and _u32(h, log + 0x14) != obj:
                return ['flags %d: the delete got %08X' % (flags, _u32(h, log + 0x14))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00427070(h):
    obj = h.alloc(0x20, b'\xEE' * 0x20)
    for value in (1.5, -3.25, 0.0):
        h.uc.mem_write(obj + 0x94, struct.pack('<f', value))
        diffs = h.compare(0x00427070, regs={UC_X86_REG_ECX: obj}, ret='st0')
        if diffs:
            return ['value %r: %s' % (value, d) for d in diffs]
        res = h.call(0x00427070, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['value %r: replacement faulted: %s' % (value, res['fault'])]
        if res['st0'] != value:
            return ['value %r: returned %r' % (value, res['st0'])]
    return None


def test_00427080(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        diffs = h.compare(0x00427080, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        res = h.call(0x00427080, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if struct.unpack('<III', h.uc.mem_read(obj, 12)) != (0, 0xffffffff, 0xffffffff):
            return ['the triple is %r' % (struct.unpack('<III', h.uc.mem_read(obj, 12)),)]
        if bytes(h.uc.mem_read(obj + 12, 0x14)) != b'\xEE' * 0x14:
            return ['bytes past the triple changed']
        return None
    finally:
        h.heap_ptr = heap0


def test_004270A0(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        diffs = h.compare(0x004270A0, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        res = h.call(0x004270A0, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, obj) != 0x00608214:
            return ['the vtable is %08X' % _u32(h, obj)]
        if bytes(h.uc.mem_read(obj + 4, 0x1c)) != b'\xEE' * 0x1c:
            return ['bytes past the vtable changed']
        return None
    finally:
        h.heap_ptr = heap0


def test_004270B0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        _hook(h, 0x00458B50, b'\x89\x0D' + _dword(log)
              + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4)
              + b'\xB8' + _dword(0x12345678) + b'\xC2\x04\x00')
        obj = h.alloc(0x120, b'\xEE' * 0x120)
        name = h.alloc(0x20, b'file.dat\0' + bytes(0x17))

        def setup():
            h.uc.mem_write(log, bytes(0x20))

        setup()
        diffs = h.compare(0x004270B0, args=[name], regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        setup()
        res = h.call(0x004270B0, args=[name], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, log) != obj + 0x44 or _u32(h, log + 4) != name:
            return ['0x458B50 got (%08X, %08X)' % (_u32(h, log), _u32(h, log + 4))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_004270C0(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x120, b'\xEE' * 0x120)
        point = h.alloc(0x10, bytes(0x10))
        out = h.alloc(0x10, b'\xEE' * 0x10)
        h.uc.mem_write(obj + 0x5c, _dword(10))
        h.uc.mem_write(obj + 0x60, _dword(8))
        h.uc.mem_write(obj + 0x78, struct.pack('<f', 32.0))
        h.uc.mem_write(obj + 0x7c, struct.pack('<f', 16.0))
        cases = [
            ('centre', 16.0, 0.0, 8.0),
            ('origin', 0.0, 0.0, 0.0),
            ('under', -16.0, 0.0, -16.0),
            ('past', 400.0, 0.0, 200.0),
            ('negative y', 16.0, 99.0, -40.0),
        ]
        for name, x, y, z in cases:
            def setup(x=x, y=y, z=z):
                h.uc.mem_write(point, struct.pack('<fff', x, y, z) + bytes(4))
                h.uc.mem_write(out, b'\xEE' * 0x10)
            setup()
            diffs = h.compare(0x004270C0, args=[out, point], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(0x004270C0, args=[out, point], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != out:
                return ['%s: returned %08X' % (name, res['eax'])]
            cx, cy = struct.unpack('<ii', h.uc.mem_read(out, 8))
            want_cx = int(10 * (x + 16.0) / 32.0)
            want_cy = -int(8 * (z - 8.0) / 16.0)
            if not 0 <= want_cx <= 9:
                want_cx = 0 if want_cx < 0 else 9
            if not 0 <= want_cy <= 7:
                want_cy = 0 if want_cy < 0 else 7
            if (cx, cy) != (want_cx, want_cy):
                return ['%s: the cell is (%d, %d), expected (%d, %d)' % ((name, cx, cy, want_cx, want_cy))]
        # a zero-sized grid: the >= branch wins over the < 0 one
        h.uc.mem_write(obj + 0x5c, _dword(0))
        h.uc.mem_write(obj + 0x60, _dword(0))
        h.uc.mem_write(point, struct.pack('<fff', 1.0, 0.0, 1.0))
        diffs = h.compare(0x004270C0, args=[out, point], regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return ['zero grid: %s' % d for d in diffs]
        res = h.call(0x004270C0, args=[out, point], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['zero grid: replacement faulted: %s' % (res['fault'],)]
        if struct.unpack('<ii', h.uc.mem_read(out, 8)) != (-1, -1):
            return ['zero grid: the cell is %r' % (struct.unpack('<ii', h.uc.mem_read(out, 8)),)]
        return None
    finally:
        h.heap_ptr = heap0

