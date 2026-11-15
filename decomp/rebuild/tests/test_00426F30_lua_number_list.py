"""Lua number-list helpers (0x00426F30..0x00426FF0), the class wrapping a counted run of numbers pushed on the
lua_State at 0x008D122C:
0x00426F30 (ECX): when values are pending (+0xC > 0), the +0x14 flag trims the Lua stack by that many
(lua_settop with -1 - count); the count is cleared either way.
0x00426F60 (ECX, ret 4): lua_tonumber of the argument shifted by +0x10, returned as a double.
0x00426F80 (ECX, ret 4): lua_pushnumber then ++[+8]; returns this.
0x00426FB0 (ECX, ret 4): stores the float at +0x2C and calls +0x18 with the (float) double from +0x1C and 1.
0x00426FF0 (ECX): [this + 8] == 5."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C
LUA_SETTOP = 0x00402A70
LUA_TONUMBER = 0x00402DE0
LUA_PUSHNUMBER = 0x004030A0

saved = {}
globals_saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


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


def _save_global(h, address):
    if address not in globals_saved:
        globals_saved[address] = bytes(h.uc.mem_read(address, 4))
    return globals_saved[address]


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()
    for address, code in globals_saved.items():
        h.uc.mem_write(address, code)
    globals_saved.clear()


def test_00426F30(h):
    heap0 = h.heap_ptr
    try:
        old = _save_global(h, LUA_STATE_SLOT)
        log = h.alloc(0x20, bytes(0x20))
        fake_L = h.alloc(0x20, b'\x55' * 0x20)
        h.uc.mem_write(LUA_STATE_SLOT, _dword(fake_L))
        _hook(h, LUA_SETTOP, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)
              + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4)
              + b'\xFF\x05' + _dword(log + 8) + b'\xC3')
        obj = h.alloc(0x20, b'\xEE' * 0x20)

        for count, flag in ((3, 1), (3, 0), (1, 1), (0, 1), (-2, 1)):
            def setup(count=count, flag=flag):
                h.uc.mem_write(log, bytes(0x20))
                h.uc.mem_write(obj, b'\xEE' * 0x20)
                h.uc.mem_write(obj + 0xc, _dword(count & 0xffffffff))
                h.uc.mem_write(obj + 0x14, bytes([flag]))

            setup()
            diffs = h.compare(0x00426F30, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['count %d flag %d: %s' % (count, flag, d) for d in diffs]
            setup()
            res = h.call(0x00426F30, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['count %d flag %d: replacement faulted: %s' % (count, flag, res['fault'])]
            calls = _u32(h, log + 8)
            if count > 0 and flag:
                if calls != 1 or _u32(h, log) != fake_L or _u32(h, log + 4) != (-1 - count) & 0xffffffff:
                    return ['count %d flag %d: lua_settop got (%08X, %08X) %d times'
                            % (count, flag, _u32(h, log), _u32(h, log + 4), calls)]
            elif calls:
                return ['count %d flag %d: lua_settop ran %d times' % (count, flag, calls)]
            if count > 0:
                if _u32(h, obj + 0xc):
                    return ['count %d flag %d: the count is %08X' % (count, flag, _u32(h, obj + 0xc))]
            elif _u32(h, obj + 0xc) != count & 0xffffffff:
                return ['count %d flag %d: the count was touched (%08X)'
                        % (count, flag, _u32(h, obj + 0xc))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00426F60(h):
    heap0 = h.heap_ptr
    try:
        _save_global(h, LUA_STATE_SLOT)
        log = h.alloc(0x20, bytes(0x20))
        fake_L = h.alloc(0x20, b'\x55' * 0x20)
        number = h.alloc(8, struct.pack('<d', 3.25))
        h.uc.mem_write(LUA_STATE_SLOT, _dword(fake_L))
        _hook(h, LUA_TONUMBER, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)
              + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4)
              + b'\xDD\x05' + _dword(number) + b'\xC3')
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        h.uc.mem_write(obj + 0x10, _dword(0x10))

        def setup():
            h.uc.mem_write(log, bytes(0x20))

        for index in (1, -3, 100):
            setup()
            diffs = h.compare(0x00426F60, args=[index], regs={UC_X86_REG_ECX: obj}, ret='st0')
            if diffs:
                return ['index %d: %s' % (index, d) for d in diffs]
            setup()
            res = h.call(0x00426F60, args=[index], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['index %d: replacement faulted: %s' % (index, res['fault'])]
            if res['st0'] != 3.25:
                return ['index %d: returned %r' % (index, res['st0'])]
            if _u32(h, log) != fake_L or _u32(h, log + 4) != (index + 0x10) & 0xffffffff:
                return ['index %d: lua_tonumber got (%08X, %08X)' % (index, _u32(h, log), _u32(h, log + 4))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00426F80(h):
    heap0 = h.heap_ptr
    try:
        _save_global(h, LUA_STATE_SLOT)
        log = h.alloc(0x20, bytes(0x20))
        fake_L = h.alloc(0x20, b'\x55' * 0x20)
        h.uc.mem_write(LUA_STATE_SLOT, _dword(fake_L))
        _hook(h, LUA_PUSHNUMBER, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)
              + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4)
              + b'\xFF\x05' + _dword(log + 8) + b'\xC3')
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        h.uc.mem_write(obj + 8, _dword(4))

        for value in (2.5, -1.0, 0.0):
            def setup(value=value):
                h.uc.mem_write(log, bytes(0x20))
                h.uc.mem_write(obj + 8, _dword(4))

            bits = _f(value)
            setup()
            diffs = h.compare(0x00426F80, args=[bits], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['value %r: %s' % (value, d) for d in diffs]
            setup()
            res = h.call(0x00426F80, args=[bits], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['value %r: replacement faulted: %s' % (value, res['fault'])]
            if res['eax'] != obj:
                return ['value %r: returned %08X' % (value, res['eax'])]
            if _u32(h, log) != fake_L or _u32(h, log + 4) != bits:
                return ['value %r: lua_pushnumber got (%08X, %08X)' % (value, _u32(h, log), _u32(h, log + 4))]
            if _u32(h, obj + 8) != 5 or _u32(h, log + 8) != 1:
                return ['value %r: the count is %d' % (value, _u32(h, obj + 8))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00426FB0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        retval = h.alloc(8, struct.pack('<d', 7.5))
        fn1c = _stub(h, b'\x89\x0D' + _dword(log) + b'\xDD\x05' + _dword(retval) + b'\xC3')
        fn18 = _stub(h, b'\x89\x0D' + _dword(log + 4)
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 8)
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 0xc)
                     + b'\xC2\x08\x00')
        vt = h.alloc(0x20, bytes(0x18) + _dword(fn18) + _dword(fn1c))
        obj = h.alloc(0x40, _dword(vt) + bytes(0x3c))

        for value in (2.5, -0.75):
            def setup():
                h.uc.mem_write(log, bytes(0x20))
                h.uc.mem_write(obj + 0x2c, b'\xEE\xEE\xEE\xEE')

            bits = _f(value)
            setup()
            diffs = h.compare(0x00426FB0, args=[bits], regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['value %r: %s' % (value, d) for d in diffs]
            setup()
            res = h.call(0x00426FB0, args=[bits], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['value %r: replacement faulted: %s' % (value, res['fault'])]
            if _u32(h, obj + 0x2c) != bits:
                return ['value %r: the stored float is %08X' % (value, _u32(h, obj + 0x2c))]
            if _u32(h, log) != obj or _u32(h, log + 4) != obj:
                return ['value %r: the virtuals got (%08X, %08X)' % (value, _u32(h, log), _u32(h, log + 4))]
            if _u32(h, log + 8) != 0x40F00000 or _u32(h, log + 0xc) != 1:
                return ['value %r: +0x18 got (%08X, %08X)' % (value, _u32(h, log + 8), _u32(h, log + 0xc))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00426FF0(h):
    obj = h.alloc(0x20, b'\xEE' * 0x20)
    for counter in (5, 4, 0, -5):
        h.uc.mem_write(obj + 8, _dword(counter & 0xffffffff))
        diffs = h.compare(0x00426FF0, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return ['counter %d: %s' % (counter, d) for d in diffs]
        res = h.call(0x00426FF0, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['counter %d: replacement faulted: %s' % (counter, res['fault'])]
        want = 1 if counter == 5 else 0
        if res['eax'] & 0xffffffff != want:
            return ['counter %d: returned %08X' % (counter, res['eax'])]
    return None
