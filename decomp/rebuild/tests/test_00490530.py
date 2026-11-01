# Differential tests for decomp/rebuild/src/fixed/f_00490530.c: a bitset resized to a new bit count.
# The object is {bit count, capacity in words, word pointer}; both branch directions (grow/shrink) advance a
# {word pointer, bit offset} iterator past the old and the new count.

import random


def run(h):
    from unicorn.x86_const import UC_X86_REG_ECX
    diffs = []
    for old in (0, 1, 5, 31, 32, 33, 64, 100):
        for new in (0, 1, 5, 31, 32, 33, 64, 100, 130):
            data = h.alloc(64 * 4, bytes(random.getrandbits(8) for _ in range(64 * 4)))
            obj = h.alloc(12, struct.pack('<III', old, 64, data))
            diffs += h.compare(0x00490530, args=[new, 0x12345678], regs={UC_X86_REG_ECX: obj}, ret=None)
    return diffs


def test_490530(h): return run(h)
