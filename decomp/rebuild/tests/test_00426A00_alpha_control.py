"""The alpha button / control lifecycle:
0x00426A00 (ECX, ret 12): base ctor with arg 1, the +0x54 2D part with arg 3, vtables 0x00608188 / 0x0060809C,
a 0x54-byte texture from arg 2 stored at +0x98, +0x9C = 1, the +0x54 part finalised; returns this.
0x00426AB0 (ECX): vtables, the +0x54 part destroyed, then the 3D control.
0x004268A0 (ECX): resets the 0x00608078 / 0x00607F8C vtables and passes to 0x00426AB0.
0x004269A0 / 0x00426BC0 (ECX, ret 4): non-virtual thunks that adjust this by -0x54.
0x004269B0 (ECX, ret 4): vtables, destructor, delete if flag bit 0; returns this.
0x00426BD0 (ECX, ret 4): destructor, delete if flag bit 0; returns this.
0x00426BF0 (ECX): the address of +0x204."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


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


def _inc(log):
    return b'\xFF\x05' + _dword(log)


def _store_ecx(log):
    return b'\x89\x0D' + _dword(log)


def _store_arg(log, off):
    return b'\x8B\x44\x24' + bytes([4 + 4 * off]) + b'\xA3' + _dword(log)


# log layout for the constructor test
L_A = 0x00           # 0x004428F0: count, this, arg
L_B = 0x10           # 0x00479B30: count, this, arg
L_NEW = 0x20         # 0x005E3EAE: count, size
L_TEX = 0x30         # 0x004DF920: count, this, arg1, arg2
L_FIN = 0x40         # 0x00479870: count, this
L_RET = 0x90
LOG_SIZE = 0x100
TEX = 0x00230000


def test_00426A00(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _hook(h, 0x004428F0, _inc(log + L_A) + _store_ecx(log + L_A + 4) + _store_arg(log + L_A + 8, 0)
              + b'\xC2\x04\x00')
        _hook(h, 0x00479B30, _inc(log + L_B) + _store_ecx(log + L_B + 4) + _store_arg(log + L_B + 8, 0)
              + b'\xC2\x04\x00')
        _hook(h, 0x005E3EAE, _inc(log + L_NEW) + _store_arg(log + L_NEW + 4, 0) + b'\xB8' + _dword(TEX) + b'\xC3')
        _hook(h, 0x004DF920, _inc(log + L_TEX) + _store_ecx(log + L_TEX + 4) + _store_arg(log + L_TEX + 8, 0)
              + _store_arg(log + L_TEX + 12, 1) + b'\xB8' + _dword(TEX) + b'\xC2\x08\x00')
        _hook(h, 0x00479870, _inc(log + L_FIN) + _store_ecx(log + L_FIN + 4) + b'\xC3')
        obj = h.alloc(0xA0, b'\xEE' * 0xA0)
        a, b, c = 0x11111111, 0x22222222, 0x33333333

        def setup(alloc_zero):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(obj, b'\xEE' * 0xA0)
            if alloc_zero:
                _hook(h, 0x005E3EAE, _inc(log + L_NEW) + _store_arg(log + L_NEW + 4, 0) + b'\x31\xC0\xC3')
            else:
                _hook(h, 0x005E3EAE, _inc(log + L_NEW) + _store_arg(log + L_NEW + 4, 0)
                      + b'\xB8' + _dword(TEX) + b'\xC3')

        for alloc_zero in (0, 1):
            setup(alloc_zero)
            diffs = h.compare(0x00426A00, args=[a, b, c], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['alloc %s: %s' % (bool(alloc_zero), d) for d in diffs]
            setup(alloc_zero)
            res = h.call(0x00426A00, args=[a, b, c], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['alloc %s: replacement faulted: %s' % (bool(alloc_zero), res['fault'])]
            if res['eax'] != obj:
                return ['alloc %s: returned %08X' % (bool(alloc_zero), res['eax'])]
            if _u32(h, log + L_A) != 1 or _u32(h, log + L_A + 4) != obj or _u32(h, log + L_A + 8) != a:
                return ['alloc %s: the control base call is wrong' % bool(alloc_zero)]
            if _u32(h, log + L_B) != 1 or _u32(h, log + L_B + 4) != obj + 0x54 or _u32(h, log + L_B + 8) != c:
                return ['alloc %s: the 2D part call is wrong' % bool(alloc_zero)]
            if _u32(h, log + L_NEW) != 1 or _u32(h, log + L_NEW + 4) != 0x54:
                return ['alloc %s: the texture allocation is wrong' % bool(alloc_zero)]
            if alloc_zero:
                if _u32(h, obj + 0x98) != 0 or _u32(h, log + L_TEX) != 0:
                    return ['alloc failure: the texture is %08X' % _u32(h, obj + 0x98)]
            else:
                if _u32(h, log + L_TEX) != 1 or _u32(h, log + L_TEX + 4) != TEX:
                    return ['alloc %s: the texture ctor got this %08X' % (bool(alloc_zero), _u32(h, log + L_TEX + 4))]
                if _u32(h, log + L_TEX + 8) != b or _u32(h, log + L_TEX + 12) != 1:
                    return ['alloc %s: the texture ctor got (%08X, %d)'
                            % (bool(alloc_zero), _u32(h, log + L_TEX + 8), _u32(h, log + L_TEX + 12))]
                if _u32(h, obj + 0x98) != TEX:
                    return ['alloc %s: the texture at +0x98 is %08X' % (bool(alloc_zero), _u32(h, obj + 0x98))]
            if _u32(h, obj) != 0x00608188 or _u32(h, obj + 0x54) != 0x0060809C:
                return ['alloc %s: the vtables are %08X / %08X' % (bool(alloc_zero), _u32(h, obj), _u32(h, obj + 0x54))]
            if h.uc.mem_read(obj + 0x9c, 1)[0] != 1:
                return ['alloc %s: the +0x9C flag is not 1' % bool(alloc_zero)]
            if _u32(h, log + L_FIN) != 1 or _u32(h, log + L_FIN + 4) != obj + 0x54:
                return ['alloc %s: the finalise call is wrong' % bool(alloc_zero)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None


L_MESH = 0x00        # 0x00479660: count, this
L_BASE = 0x10        # 0x00442960: count, this
L_DTOR = 0x20        # 0x00426AB0 interception
L_FREE = 0x30        # 0x005E3E9C: count, this


def test_00426AB0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _hook(h, 0x00479660, _inc(log + L_MESH) + _store_ecx(log + L_MESH + 4) + b'\xC3')
        _hook(h, 0x00442960, _inc(log + L_BASE) + _store_ecx(log + L_BASE + 4) + b'\xC3')
        obj = h.alloc(0xA0, b'\xEE' * 0xA0)

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(obj, b'\xEE' * 0xA0)

        setup()
        diffs = h.compare(0x00426AB0, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        setup()
        res = h.call(0x00426AB0, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, obj) != 0x00608188 or _u32(h, obj + 0x54) != 0x0060809C:
            return ['the vtables are %08X / %08X' % (_u32(h, obj), _u32(h, obj + 0x54))]
        if _u32(h, log + L_MESH) != 1 or _u32(h, log + L_MESH + 4) != obj + 0x54:
            return ['the 2D part destructor got %08X' % _u32(h, log + L_MESH + 4)]
        if _u32(h, log + L_BASE) != 1 or _u32(h, log + L_BASE + 4) != obj:
            return ['the control destructor got %08X' % _u32(h, log + L_BASE + 4)]

        for target in (0x00426A00, None):
            pass
        return None
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0


def test_004268A0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _hook(h, 0x00426AB0, _inc(log + L_DTOR) + _store_ecx(log + L_DTOR + 4) + b'\xC3')
        obj = h.alloc(0xA0, b'\xEE' * 0xA0)
        h.uc.mem_write(log, bytes(LOG_SIZE))
        diffs = h.compare(0x004268A0, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(obj, b'\xEE' * 0xA0)
        res = h.call(0x004268A0, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, obj) != 0x00608078 or _u32(h, obj + 0x54) != 0x00607F8C:
            return ['the vtables are %08X / %08X' % (_u32(h, obj), _u32(h, obj + 0x54))]
        if _u32(h, log + L_DTOR) != 1 or _u32(h, log + L_DTOR + 4) != obj:
            return ['the destructor got %08X' % _u32(h, log + L_DTOR + 4)]
        return None
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0


def test_thunks(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _hook(h, 0x004269B0, _inc(log) + _store_ecx(log + 4) + b'\xB8\x78\x56\x34\x12\xC2\x04\x00')
        _hook(h, 0x00426BD0, _inc(log + 0x10) + _store_ecx(log + 0x14) + b'\xB8\xEF\xCD\xAB\x90\xC2\x04\x00')
        obj = h.alloc(0xA0, b'\xEE' * 0xA0)
        for addr, logoff, retval in ((0x004269A0, 0x00, 0x12345678), (0x00426BC0, 0x10, 0x90ABCDEF)):
            for flags in (0, 1, 2):
                h.uc.mem_write(log, bytes(LOG_SIZE))
                diffs = h.compare(addr, args=[flags], regs={UC_X86_REG_ECX: obj + 0x54}, ret='eax')
                if diffs:
                    return ['%08X flags %d: %s' % (addr, flags, d) for d in diffs]
                h.uc.mem_write(log, bytes(LOG_SIZE))
                res = h.call(addr, args=[flags], regs={UC_X86_REG_ECX: obj + 0x54})
                if res['fault']:
                    return ['%08X flags %d: replacement faulted: %s' % (addr, flags, res['fault'])]
                if res['eax'] != retval:
                    return ['%08X flags %d: returned %08X' % (addr, flags, res['eax'])]
                if _u32(h, log + logoff) != 1 or _u32(h, log + logoff + 4) != obj:
                    return ['%08X flags %d: the destructor got %08X' % (addr, flags, _u32(h, log + logoff + 4))]
        return None
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0


def test_004269B0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _hook(h, 0x00426AB0, _inc(log + L_DTOR) + _store_ecx(log + L_DTOR + 4) + b'\xC3')
        _hook(h, 0x005E3E9C, _inc(log + L_FREE) + _store_arg(log + L_FREE + 4, 0) + b'\xC3')
        obj = h.alloc(0xA0, b'\xEE' * 0xA0)
        for flags in (0, 1, 2, 3):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(obj, b'\xEE' * 0xA0)
            diffs = h.compare(0x004269B0, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(obj, b'\xEE' * 0xA0)
            res = h.call(0x004269B0, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['flags %d: returned %08X' % (flags, res['eax'])]
            if _u32(h, obj) != 0x00608078 or _u32(h, obj + 0x54) != 0x00607F8C:
                return ['flags %d: the vtables are %08X / %08X' % (flags, _u32(h, obj), _u32(h, obj + 0x54))]
            if _u32(h, log + L_DTOR) != 1 or _u32(h, log + L_DTOR + 4) != obj:
                return ['flags %d: the destructor got %08X' % (flags, _u32(h, log + L_DTOR + 4))]
            want = 1 if flags & 1 else 0
            if _u32(h, log + L_FREE) != want:
                return ['flags %d: delete ran %d times' % (flags, _u32(h, log + L_FREE))]
            if want and _u32(h, log + L_FREE + 4) != obj:
                return ['flags %d: delete got %08X' % (flags, _u32(h, log + L_FREE + 4))]
        return None
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0


def test_00426BD0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _hook(h, 0x00426AB0, _inc(log + L_DTOR) + _store_ecx(log + L_DTOR + 4) + b'\xC3')
        _hook(h, 0x005E3E9C, _inc(log + L_FREE) + _store_arg(log + L_FREE + 4, 0) + b'\xC3')
        obj = h.alloc(0xA0, b'\xEE' * 0xA0)
        for flags in (0, 1, 2):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            diffs = h.compare(0x00426BD0, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            h.uc.mem_write(log, bytes(LOG_SIZE))
            res = h.call(0x00426BD0, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['flags %d: returned %08X' % (flags, res['eax'])]
            if _u32(h, log + L_DTOR) != 1 or _u32(h, log + L_DTOR + 4) != obj:
                return ['flags %d: the destructor got %08X' % (flags, _u32(h, log + L_DTOR + 4))]
            want = 1 if flags & 1 else 0
            if _u32(h, log + L_FREE) != want:
                return ['flags %d: delete ran %d times' % (flags, _u32(h, log + L_FREE))]
        return None
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0


def test_00426BF0(h):
    obj = h.alloc(0x210, b'\xEE' * 0x210)
    diffs = h.compare(0x00426BF0, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00426BF0, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if res['eax'] != obj + 0x204:
        return ['returned %08X' % res['eax']]
    return None
