"""The engine's script getters in engine.cpp: GetGammaCoef (0x44B3E0, pushes 3 - the engine's gamma), GetTexQuality
(0x44B510, the texture-quality option) and SaveTreeDist (0x44B610, copies the tree range the scripts set into the
engine's saved copy).  The engine and the Lua state are preset in their singleton slots; the game's lua_Number is a
float and a TValue is the value followed by its type."""
import struct

ENGINE_SLOT = 0x006C88B8
LUA_STATE_SLOT = 0x008D122C
ENGINE_SIZE = 0xD8
GAMMA = 0x40
TEX_QUALITY = 0x50
WORLD_LEVEL = 0x70
SAVED = 0x1C
TREE = 0x2C
LUA_TOP = 0x8
LUA_TNUMBER = 3

GET_GAMMA_COEF = 0x0044B3E0
GET_TEX_QUALITY = 0x0044B510
SAVE_TREE_DIST = 0x0044B610


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _fake_lua(h):
    """a lua_State whose top is free for one pushed TValue; returns the state and the top slot"""
    state = h.alloc(0x40, bytes(0x40))
    top = state + 0x20
    h.uc.mem_write(state + LUA_TOP, struct.pack('<I', top))
    return state, top


def _check_pushed(h, state, top, expected):
    if _u32(h, state + LUA_TOP) != top + 8:
        return ['top %08X, want %08X' % (_u32(h, state + LUA_TOP), top + 8)]
    if _u32(h, top + 4) != LUA_TNUMBER:
        return ['pushed type %d, want number' % _u32(h, top + 4)]
    got = _u32(h, top)
    want = struct.unpack('<I', struct.pack('<f', expected))[0]
    if got != want:
        return ['pushed %08X, want %08X' % (got, want)]
    return None


def test_engine_get_gamma_coef(h):
    for gamma in (1.0, 0.5, 0.75, 2.0, 2.999999, 3.5, -0.25, 1.0000000001):
        engine = h.alloc(ENGINE_SIZE, bytes(ENGINE_SIZE))
        h.uc.mem_write(engine + GAMMA, struct.pack('<d', gamma))
        state, top = _fake_lua(h)

        def setup(h, engine=engine, state=state):
            h.uc.mem_write(ENGINE_SLOT, struct.pack('<I', engine))
            h.uc.mem_write(LUA_STATE_SLOT, struct.pack('<I', state))

        diffs = h.compare(GET_GAMMA_COEF, ret='eax', setup=setup)
        if diffs:
            return ['gamma %r: %s' % (gamma, d) for d in diffs]

        res = h.call(GET_GAMMA_COEF)
        if res['fault']:
            return ['gamma %r: replacement faulted: %s' % (gamma, res['fault'])]
        if res['eax'] != 1:
            return ['gamma %r: returned %08X, want 1' % (gamma, res['eax'])]
        diffs = _check_pushed(h, state, top, _f32(3.0 - _f32(gamma)))
        if diffs:
            return ['gamma %r: %s' % (gamma, d) for d in diffs]
    return None


def test_engine_get_tex_quality(h):
    for quality in (0, 1, 2, -1, 1000):
        engine = h.alloc(ENGINE_SIZE, bytes(ENGINE_SIZE))
        h.uc.mem_write(engine + TEX_QUALITY, struct.pack('<i', quality))
        state, top = _fake_lua(h)

        def setup(h, engine=engine, state=state):
            h.uc.mem_write(ENGINE_SLOT, struct.pack('<I', engine))
            h.uc.mem_write(LUA_STATE_SLOT, struct.pack('<I', state))

        diffs = h.compare(GET_TEX_QUALITY, ret='eax', setup=setup)
        if diffs:
            return ['quality %d: %s' % (quality, d) for d in diffs]

        res = h.call(GET_TEX_QUALITY)
        if res['fault']:
            return ['quality %d: replacement faulted: %s' % (quality, res['fault'])]
        if res['eax'] != 1:
            return ['quality %d: returned %08X, want 1' % (quality, res['eax'])]
        diffs = _check_pushed(h, state, top, _f32(quality))
        if diffs:
            return ['quality %d: %s' % (quality, d) for d in diffs]
    return None


def test_engine_save_tree_dist(h):
    def make_engine(h, world, near, shift, far, step):
        engine = h.alloc(ENGINE_SIZE, bytes(ENGINE_SIZE))
        h.uc.mem_write(engine + WORLD_LEVEL, struct.pack('<I', world))
        for offset, value in ((SAVED, 1.0), (SAVED + 4, 2.0), (SAVED + 8, 3.0), (SAVED + 12, 4.0),
                              (TREE, near), (TREE + 4, shift), (TREE + 8, far), (TREE + 12, step)):
            h.uc.mem_write(engine + offset, struct.pack('<f', value))
        return engine

    for name, distances in (('no world', None), ('no distances', False), ('with distances', True)):
        world = 0
        if distances is not None:
            level = h.alloc(0x80, bytes(0x80))
            world = level
            if distances:
                holder = h.alloc(0x70, bytes(0x70))
                first = h.alloc(0x80, bytes(0x80))
                entry = h.alloc(4, struct.pack('<I', first))
                h.uc.mem_write(level + 0x78, struct.pack('<I', holder))
                h.uc.mem_write(holder + 0x68, struct.pack('<I', entry))
                for offset, value in ((0x58, 10.0), (0x5C, 11.0), (0x60, 12.0), (0x64, 13.0)):
                    h.uc.mem_write(first + offset, struct.pack('<f', value))
        engine = make_engine(h, world, 20.0, 21.0, 22.0, 23.0)

        def setup(h, engine=engine):
            h.uc.mem_write(ENGINE_SLOT, struct.pack('<I', engine))

        diffs = h.compare(SAVE_TREE_DIST, ret='eax', setup=setup)
        if diffs:
            return ['%s: %s' % (name, d) for d in diffs]

        res = h.call(SAVE_TREE_DIST)
        if res['fault']:
            return ['%s: replacement faulted: %s' % (name, res['fault'])]
        if res['eax'] != 0:
            return ['%s: returned %08X, want 0' % (name, res['eax'])]
        saved = struct.unpack('<4f', h.uc.mem_read(engine + SAVED, 16))
        if saved != (20.0, 21.0, 22.0, 23.0):
            return ['%s: saved %r, want the tree range' % (name, saved)]
    return None
