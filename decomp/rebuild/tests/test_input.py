# Differential tests for rebuild/src/engine/input.cpp: CInput state resets on random objects.

def make_input(h):
    obj = h.alloc(0x7CC, bytes(random.getrandbits(8) for _ in range(0x7CC)))
    nkeys, nbtn = random.randint(0, 40), random.randint(0, 8)
    keys = h.alloc(2 * nkeys + 2, bytes(random.getrandbits(8) for _ in range(2 * nkeys + 2)))
    btns = h.alloc(4 * nbtn + 4, bytes(random.getrandbits(8) for _ in range(4 * nbtn + 4)))
    h.uc.mem_write(obj + 0x660, struct.pack('<II', keys, nkeys))
    h.uc.mem_write(obj + 0x66C, struct.pack('<II', btns, nbtn))
    return obj

def run(h, addr):
    from unicorn.x86_const import UC_X86_REG_ECX
    diffs = []
    for _ in range(30):
        obj = make_input(h)
        diffs += h.compare(addr, args=[], regs={UC_X86_REG_ECX: obj}, ret=None)
    return diffs

def test_reset_mouse(h): return run(h, 0x0046CEB0)
def test_reset_keys(h): return run(h, 0x0046CEF0)
def test_reset(h): return run(h, 0x0046CF30)
