"""The engine's script functions in engine.cpp: ExitGame (0x44B1F0, the game goes back to the main menu, optionally
through the Credits level) and IsShiftDown (0x44B6A0, a Lua boolean of the keyboard state).  The Lua stack is a
fake state whose top points at one TValue of the heap: the game's lua_Number is a float and a TValue is the value
followed by its type.  The engine and the input are preset in their singleton slots."""
import struct

EXIT_GAME = 0x0044B1F0
IS_SHIFT_DOWN = 0x0044B6A0
ENGINE_SLOT = 0x006C88B8
INPUT_SLOT = 0x006C8684
ENGINE_SIZE = 0xD8
STATE = 0xAC
UNKNOWN_B0 = 0xB0
CREDITS = 0xB1
INPUT_SIZE = 0x7CC
KEY_STATE = 0x48
LUA_TOP = 0x8

LUA_TNIL, LUA_TBOOLEAN, LUA_TNUMBER = 0, 1, 3


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _fake_lua(h, tt, value):
    """a lua_State whose last pushed value (one TValue, type tt, value value) is at top - 8; returns the state and
    the TValue"""
    state = h.alloc(0x40, bytes(0x40))
    top = state + 0x20
    h.uc.mem_write(state + LUA_TOP, struct.pack('<I', top + 8))
    h.uc.mem_write(top, struct.pack('<II', value, tt))
    return state, top


def test_engine_exit_game(h):
    expected = [((LUA_TBOOLEAN, 1), 1), ((LUA_TBOOLEAN, 0), 0), ((LUA_TNUMBER, 0x40000000), 0), ((LUA_TNIL, 0), 0)]
    for (tt, value), credits in expected:
        engine = h.alloc(ENGINE_SIZE, b'\x5a' * ENGINE_SIZE)
        h.uc.mem_write(engine + STATE, struct.pack('<I', 0x11223344))
        state, top = _fake_lua(h, tt, value)

        def setup(h, engine=engine):
            h.uc.mem_write(ENGINE_SLOT, struct.pack('<I', engine))

        diffs = h.compare(EXIT_GAME, args=[state], ret='eax', setup=setup)
        if diffs:
            return ['type %d: %s' % (tt, d) for d in diffs]

        res = h.call(EXIT_GAME, [state])
        if res['fault']:
            return ['type %d: replacement faulted: %s' % (tt, res['fault'])]
        if res['eax'] != 0:
            return ['type %d: returned %08X' % (tt, res['eax'])]
        if h.uc.mem_read(engine + UNKNOWN_B0, 1) != b'\0' or h.uc.mem_read(engine + CREDITS, 1) != bytes([credits]):
            return ['type %d: +B0 %02X +B1 %02X, want 00 %02X' % (tt, h.uc.mem_read(engine + UNKNOWN_B0, 1)[0],
                                                                  h.uc.mem_read(engine + CREDITS, 1)[0], credits)]
        if _u32(h, engine + STATE) != 3:
            return ['type %d: state %08X, want 3' % (tt, _u32(h, engine + STATE))]
        if _u32(h, top + 4) != tt or _u32(h, top) != value:
            return ['type %d: the stack value changed' % tt]
    return None


def test_engine_is_shift_down(h):
    for held in ([], [0x2A], [0x36], [0x2A, 0x36]):
        want = 1 if held else 0
        input_ = h.alloc(INPUT_SIZE, bytes(INPUT_SIZE))
        for dik in (0x2A, 0x36):
            h.uc.mem_write(input_ + KEY_STATE + dik, b'\x80' if dik in held else b'\x7f')
        state, top = _fake_lua(h, LUA_TNIL, 0)

        def setup(h, input_=input_):
            h.uc.mem_write(INPUT_SLOT, struct.pack('<I', input_))

        diffs = h.compare(IS_SHIFT_DOWN, args=[state], ret='eax', setup=setup)
        if diffs:
            return ['keys %r: %s' % (held, d) for d in diffs]

        res = h.call(IS_SHIFT_DOWN, [state])
        if res['fault']:
            return ['keys %r: replacement faulted: %s' % (held, res['fault'])]
        if res['eax'] != 1:
            return ['keys %r: returned %08X, want 1' % (held, res['eax'])]
        if _u32(h, state + LUA_TOP) != top + 16:
            return ['keys %r: top %08X, want %08X' % (held, _u32(h, state + LUA_TOP), top + 16)]
        if _u32(h, top + 8) != want or _u32(h, top + 12) != LUA_TBOOLEAN:
            return ['keys %r: pushed %d/%d, want %d/boolean' % (held, _u32(h, top + 8),
                                                                _u32(h, top + 12), want)]
    return None
