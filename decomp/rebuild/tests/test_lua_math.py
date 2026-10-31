# Differential tests for the replaced Lua 5.1.2 library (rebuild/src/lua51, lua_Number float).
# The module is compiled wholesale now: luaopen_math is replaced by src/lua51/lmathlib.c, and the original's
# static math functions (math_abs 0x4064D0) are never reached, so there is nothing at those addresses to compare
# against.  What the rebuilt exe does replace are the Lua API functions the game calls (the DECOMP entries of
# src/lua51/decomp_entries.c); these tests drive them over a minimal lua_State: +8 top, +0xC base,
# TValue = {float n; int tt}.

def make_state(h, values):
    stack = h.alloc(8 * 16)
    for i, (n, tt) in enumerate(values):
        h.uc.mem_write(stack + 8 * i, struct.pack('<fi', n, tt))
    L = h.alloc(0x80)
    h.uc.mem_write(L + 8, struct.pack('<II', stack + 8 * len(values), stack))
    return L


def cases():
    # (n, tt): 0 nil, 1 boolean, 3 number (lua_Number is float here)
    return ([], [(0.0, 0)], [(1.5, 3), (-2.25, 3)], [(0.0, 1), (3.0, 3), (7.0, 3), (0.0, 0)])


def indices(h, L, n):
    return [i for i in range(1, n + 2)] + [-i for i in range(1, n + 2)]


def test_lua_type(h):
    diffs = []
    for vals in cases():
        st = {}
        def setup(h, vals=vals):
            st['L'] = make_state(h, vals)
        setup(h)
        for idx in indices(h, st['L'], len(vals)):
            diffs += h.compare(0x00402C20, args=[st['L'], idx], ret='eax')
    return diffs


def test_lua_tonumber(h):
    diffs = []
    for vals in cases():
        st = {}
        def setup(h, vals=vals):
            st['L'] = make_state(h, vals)
        setup(h)
        for idx in indices(h, st['L'], len(vals)):
            diffs += h.compare(0x00402DE0, args=[st['L'], idx], ret='st0')
    return diffs


def test_lua_tointeger(h):
    diffs = []
    for vals in cases():
        st = {}
        def setup(h, vals=vals):
            st['L'] = make_state(h, vals)
        setup(h)
        for idx in indices(h, st['L'], len(vals)):
            diffs += h.compare(0x00402E40, args=[st['L'], idx], ret='eax')
    return diffs


def test_lua_toboolean(h):
    diffs = []
    for vals in cases():
        st = {}
        def setup(h, vals=vals):
            st['L'] = make_state(h, vals)
        setup(h)
        for idx in indices(h, st['L'], len(vals)):
            diffs += h.compare(0x00402EA0, args=[st['L'], idx], ret='eax')
    return diffs


def test_lua_isnumber(h):
    diffs = []
    for vals in cases():
        st = {}
        def setup(h, vals=vals):
            st['L'] = make_state(h, vals)
        setup(h)
        for idx in indices(h, st['L'], len(vals)):
            diffs += h.compare(0x00402C80, args=[st['L'], idx], ret='eax')
    return diffs


def test_lua_isstring(h):
    diffs = []
    for vals in cases():
        st = {}
        def setup(h, vals=vals):
            st['L'] = make_state(h, vals)
        setup(h)
        for idx in indices(h, st['L'], len(vals)):
            diffs += h.compare(0x00402CC0, args=[st['L'], idx], ret='eax')
    return diffs


def test_lua_rawequal(h):
    diffs = []
    for i, a in enumerate(cases()):
        for j, b in enumerate(cases()):
            st = {}
            def setup(h, a=a, b=b):
                # one stack holding both, the second starting at the first's top
                stack = h.alloc(8 * 32)
                for k, (n, tt) in enumerate(a + b):
                    h.uc.mem_write(stack + 8 * k, struct.pack('<fi', n, tt))
                L = h.alloc(0x80)
                h.uc.mem_write(L + 8, struct.pack('<II', stack + 8 * len(a + b), stack + 8 * len(a)))
                st['L'] = L
            setup(h)
            for x in range(1, len(a) + 2):
                for y in [-len(b) - 1 + k for k in range(len(b) + 1)]:
                    diffs += h.compare(0x00402D10, args=[st['L'], x, y], ret='eax')
    return diffs
