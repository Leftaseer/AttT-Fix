"""0x00586EC0 (ECX = the new rectangle, one stack argument -- the script-call context, ret 4): builds the base
(0x00582350) and installs the vtables 0x61E864 / +0x214 0x61E85C; the context's int at +0x10 is the Lua stack base,
so the numbers base+1 .. base+4 (0x00402DE0 on the state at 0x8D122C) are x, y, w, h and base+5, truncated to an int
through a long long, is the colour, all passed to the outline 0x00586BA0; the rectangle is returned.  The three
callees are stubs that log what they see; the Lua stub returns the float stored in a table at the requested index."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00586EC0
CTOR = 0x00582350
LUA = 0x00402DE0
REL = 0x00586BA0
STATE = 0x008D122C

N_CTOR = 0x00
CTOR_THIS = 0x04
N_LUA = 0x08
LUA_IDX = 0x0C             # 8 records
N_REL = 0x2C
REL_THIS = 0x30
REL_X = 0x34
REL_Y = 0x38
REL_W = 0x3C
REL_H = 0x40
REL_COLOR = 0x44
LOG_SIZE = 0x50

VTBL = 0x0061E864
VTBL_214 = 0x0061E85C
BASE = 2
XS, YS, WS, HS = 3.75, 4.0, 7.9, 6.5
COLOR_F = 3.0e9                     # (int)(long long)3e9 = 0xB2D05E00
COLOR = 0xB2D05E00

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


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


def _patch_thunk(h, address, code):
    target = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', target - (address + 5)))


def test_00586EC0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        table = h.alloc(0x40, bytes(0x40))
        for idx, val in ((BASE + 1, XS), (BASE + 2, YS), (BASE + 3, WS), (BASE + 4, HS), (BASE + 5, COLOR_F)):
            h.uc.mem_write(table + idx * 4, struct.pack('<f', val))
        _patch_thunk(h, CTOR, b'\x89\x0D' + _dword(log + CTOR_THIS)           # this -> [ctor this]
                     + b'\xFF\x05' + _dword(log + N_CTOR)                      # inc [ctor]
                     + b'\xC3')                                                # ret
        _patch_thunk(h, LUA, b'\x8B\x44\x24\x08'                               # eax = idx
                     + b'\x8B\x15' + _dword(log + N_LUA)                       # edx = count
                     + b'\x89\x04\x95' + _dword(log + LUA_IDX)                 # mov [edx*4+idx], eax
                     + b'\xFF\x05' + _dword(log + N_LUA)                       # inc count
                     + b'\xD9\x04\x85' + _dword(table)                         # flds [eax*4+table]
                     + b'\xC3')                                                # ret
        _patch_thunk(h, REL, b'\x89\x0D' + _dword(log + REL_THIS)
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + REL_X)
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + REL_Y)
                     + b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + REL_W)
                     + b'\x8B\x44\x24\x10' + b'\xA3' + _dword(log + REL_H)
                     + b'\x8B\x44\x24\x14' + b'\xA3' + _dword(log + REL_COLOR)
                     + b'\xFF\x05' + _dword(log + N_REL)
                     + b'\x31\xC0'                                             # xor eax, eax
                     + b'\xC2\x14\x00')                                        # ret 20
        state = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(STATE, _dword(state))
        self = h.alloc(0x300, b'\x55' * 0x300)
        ctx = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(ctx + 0x10, struct.pack('<i', BASE))
        heap_base = h.heap_ptr

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(self, b'\x55' * 0x300)

        h.heap_ptr = heap_base
        setup()
        diffs = h.compare(THIS, args=[ctx], regs={UC_X86_REG_ECX: self}, ret='eax')
        if diffs:
            return diffs
        h.heap_ptr = heap_base
        setup()
        res = h.call(THIS, args=[ctx], regs={UC_X86_REG_ECX: self})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if res['esp'] != 8:
            return ['stack delta %d, not 8' % (res['esp'],)]
        if res['eax'] != self:
            return ['returned %08X, expected %08X' % (res['eax'], self)]
        if _u32(h, self) != VTBL or _u32(h, self + 0x214) != VTBL_214:
            return ['vtables %08X / %08X' % (_u32(h, self), _u32(h, self + 0x214))]
        if _u32(h, log + N_CTOR) != 1 or _u32(h, log + CTOR_THIS) != self:
            return ['base constructor saw %d calls on %08X'
                    % (_u32(h, log + N_CTOR), _u32(h, log + CTOR_THIS))]
        if _u32(h, log + N_LUA) != 5:
            return ['lua_tonumber called %d times' % _u32(h, log + N_LUA)]
        seen = sorted(_u32(h, log + LUA_IDX + i * 4) for i in range(5))
        if seen != [BASE + 1, BASE + 2, BASE + 3, BASE + 4, BASE + 5]:
            return ['lua_tonumber indexes %s' % (seen,)]
        if _u32(h, log + N_REL) != 1 or _u32(h, log + REL_THIS) != self:
            return ['outline saw %d calls on %08X' % (_u32(h, log + N_REL), _u32(h, log + REL_THIS))]
        got = (_f32(h, log + REL_X), _f32(h, log + REL_Y), _f32(h, log + REL_W), _f32(h, log + REL_H),
               _u32(h, log + REL_COLOR))
        want = tuple(struct.unpack('<f', struct.pack('<f', v))[0] for v in (XS, YS, WS, HS)) + (COLOR,)
        if got != want:
            return ['outline got %r, expected %r' % (got, want)]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
