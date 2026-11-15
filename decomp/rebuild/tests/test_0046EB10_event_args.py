"""The input events' script conversion in input.cpp: evMoveInfo (0x46EB10, pushes x / y / wheel) and evKeyInfo
(0x46EC30, pushes the DIK code as a number).  Both fill the 0x0C-byte argument list {vtable 0x0060826C, 0, count}
at the caller's out address and return it; the values themselves stay on the game's Lua stack (lua_Number is a
float, a TValue is the value followed by its type)."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C
LUA_TOP = 0x8
LUA_TNUMBER = 3
ARGS_VTABLE = 0x0060826C

MOVE_VF0 = 0x0046EB10
KEY_VF0 = 0x0046EC30
MOVE_VTABLE = 0x0060C798
KEY_VTABLE = 0x0060CA1C


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _fbits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _fake_lua(h):
    """a lua_State whose top is free for three pushed TValues; returns the state and the top slot"""
    state = h.alloc(0x80, bytes(0x80))
    top = state + 0x20
    h.uc.mem_write(state + LUA_TOP, struct.pack('<I', top))
    return state, top


def _check_pushed(h, state, top, expected):
    if _u32(h, state + LUA_TOP) != top + 8 * len(expected):
        return ['top %08X, want %08X' % (_u32(h, state + LUA_TOP), top + 8 * len(expected))]
    for i, value in enumerate(expected):
        entry = top + 8 * i
        if _u32(h, entry + 4) != LUA_TNUMBER:
            return ['pushed %d: type %d, want number' % (i, _u32(h, entry + 4))]
        got = _u32(h, entry)
        if got != _fbits(value):
            return ['pushed %d: %08X, want %08X (%r)' % (i, got, _fbits(value), value)]
    return None


def _run(h, entry, info, expected):
    """compare the original with the rebuilt entry and then run the rebuilt one to observe its writes"""
    state, top = _fake_lua(h)
    arguments = h.alloc(12, bytes(12))

    def setup(h, state=state):
        h.uc.mem_write(LUA_STATE_SLOT, struct.pack('<I', state))

    diffs = h.compare(entry, args=(arguments,), regs={UC_X86_REG_ECX: info}, ret='eax', setup=setup)
    if diffs:
        return diffs

    res = h.call(entry, args=(arguments,), regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if res['eax'] != arguments:
        return ['returned %08X, want the out address %08X' % (res['eax'], arguments)]
    if _u32(h, arguments) != ARGS_VTABLE or _u32(h, arguments + 4) != 0 or _u32(h, arguments + 8) != len(expected):
        return ['argument list %r, want (vtable %08X, 0, %d)'
                % (struct.unpack('<III', h.uc.mem_read(arguments, 12)), ARGS_VTABLE, len(expected))]
    return _check_pushed(h, state, top, expected)


def test_move_event_script_arguments(h):
    for x, y, wheel in ((1.5, -2.25, 0.75), (0.1, 0.2, 0.3), (-0.0, 1e-30, 3.4028235e38)):
        info = h.alloc(16, struct.pack('<Ifff', MOVE_VTABLE, x, y, wheel))
        diffs = _run(h, MOVE_VF0, info, (_f32(x), _f32(y), _f32(wheel)))
        if diffs:
            return ['move (%r, %r, %r): %s' % (x, y, wheel, d) for d in diffs]
    return None


def test_key_event_script_arguments(h):
    for dik in (0, 1, 0x1E, 0xFF, -1, 0x12345678, -0x40000000, 0x7FFFFFFF):
        info = h.alloc(8, struct.pack('<Ii', KEY_VTABLE, dik))
        diffs = _run(h, KEY_VF0, info, (float(dik & 0xFF),))
        if diffs:
            return ['key %d: %s' % (dik, d) for d in diffs]
    return None
