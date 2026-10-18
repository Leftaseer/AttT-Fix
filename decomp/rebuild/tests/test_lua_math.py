# Differential tests for rebuild/src/lua/lmathlib.c (run by tools/difftest.py).
# A minimal lua_State: +8 top, +0xC base; TValue = {float n; int tt}.

def make_state(h, values):
    stack = h.alloc(8 * 16)
    for i, v in enumerate(values):
        h.uc.mem_write(stack + 8 * i, struct.pack('<fi', v, 3))
    L = h.alloc(0x80)
    h.uc.mem_write(L + 8, struct.pack('<II', stack + 8 * len(values), stack))
    return L


def test_math_abs(h):
    diffs = []
    for v in [0.0, -0.0, 1.5, -1.5, -3.4e38, 7e-39, float('inf'), float('-inf')] + [random.uniform(-1e6, 1e6) for _ in range(40)]:
        st = {}
        def setup(h, v=v):
            st['L'] = make_state(h, [v])
        h_ = h
        # allocate first so both runs see the same pointer
        setup(h_)
        diffs += h.compare(0x004064D0, args=[st['L']], ret='eax')
    return diffs
