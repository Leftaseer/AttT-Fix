# Differential test for decomp/rebuild/src/fixed/f_0050B9A0.c: the battle "next move" that also realizes "wait".
# The turn order is the array at +0x270 of {troop, state}: 0 = not acted, 1 = waited (set by 0x0050C280), 2 = acted.
# The original searches it twice (state 0, then state 1) and selects the first living troop; only when both passes
# find nothing does it start a new round (+0x1C4) and reset every state to 0.  The second pass marks the move with
# _IsWaitMove = 1, which keeps the Lua wait button disabled until the next round.
#
# The callees are replaced by stubs so the test observes only the search: the selected entry, the states, the round
# counter and the _IsWaitMove table write.  Scenario 1 is the regression: with a waited troop (state 1) and no
# troop left to act (state 0), the buggy translation found nothing, started a new round and picked the first troop
# again - the waited troop never moved, exactly like "skip turn".

import struct

# original-exe addresses (the .text section keeps its layout in the rebuilt image); (address, stub bytes)
STUBS = [
    (0x005083E0, b'\xc3'),                          # no-arg helper
    (0x00503B80, b'\xc3'),
    (0x00503B40, b'\xc3'),
    (0x00511E00, b'\xb8\x01\x00\x00\x00\xc3'),      # a creature is alive
    (0x0051DAA0, b'\xb8\x01\x00\x00\x00\xc3'),      # the troop has living creatures
    (0x0051DB90, b'\xc3'),
    (0x0051F950, b'\xc3'),
    (0x004030A0, b'\xc3'),                          # lua_pushnumber (cdecl)
    (0x00403120, b'\xc3'),                          # lua_pushstring (cdecl)
    (0x00427820, b'\xc3'),
    (0x004378D0, b'\xc3'),
    (0x0057B770, b'\x33\xc0\xc2\x08\x00'),          # ScriptTable::operator[] -> 0, pops 8
    (0x0057A230, b'\x33\xc0\xc2\x0c\x00'),          # call a script function -> 0, pops 12
    (0x0057BB20, b'\xc2\x08\x00'),                  # table[key] = value, pops 8 (observed by the hook)
]
WAIT_KEY = 0x00613914          # "_IsWaitMove"


def _w(h, p, v):
    h.uc.mem_write(p, struct.pack('<I', v))


def _r(h, p):
    return struct.unpack('<I', h.uc.mem_read(p, 4))[0]


def _fixture(h):
    def alloc(n):
        return h.alloc(n, bytes(n))
    this = alloc(0x300)
    friend = alloc(0x120)
    enemy = alloc(0x120)
    ta = alloc(0x120)
    tb = alloc(0x120)
    entries = alloc(16)
    return this, friend, enemy, ta, tb, entries


def _scenario(h, f, sa, sb, rnd=1):
    this, friend, enemy, ta, tb, entries = f
    h.uc.mem_write(entries, struct.pack('<IIII', ta, sa, tb, sb))
    _w(h, this + 0x270, entries)
    _w(h, this + 0x274, entries + 16)
    _w(h, this + 0x1c4, rnd)
    _w(h, this + 0x27c, 0)
    _w(h, this + 0x64, ta)
    _w(h, this + 0x98, 0)
    _w(h, 0x006CA8E0, 0)        # round listeners: no head
    _w(h, 0x006CA8E4, 0)


def run(h):
    import os
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP

    diffs = []
    saved = []
    for a, code in STUBS:
        saved.append((a, bytes(h.uc.mem_read(a, len(code)))))
        h.uc.mem_write(a, code)
        h.uc.ctl_remove_cache(a, a + len(code))
    lis = bytes(h.uc.mem_read(0x006CA8E0, 8))
    try:
        this, friend, enemy, ta, tb, entries = _fixture(h)
        f = (this, friend, enemy, ta, tb, entries)
        _w(h, this + 0x50, friend)
        _w(h, this + 0x54, 1)
        _w(h, this + 0x5c, enemy)
        _w(h, this + 0x60, 1)
        _w(h, this + 0xd8, 0)
        _w(h, friend + 0x58, h.alloc(4, struct.pack('<I', 0x1111)))
        _w(h, friend + 0x5c, 1)
        _w(h, enemy + 0x58, h.alloc(4, struct.pack('<I', 0x2222)))
        _w(h, enemy + 0x5c, 1)
        for t in (ta, tb):
            _w(h, t + 0x44, 15)     # empty std::string name at +0x2C (size 0, inline capacity 15)
            _w(h, t + 0x94, 2)      # a third side: neither caption nor the reach marking
            _w(h, t + 0xb4, 0)

        # original vs rebuilt: state 0 first, state 1 second, new round last
        for sa, sb in ((2, 1), (0, 1), (2, 2)):
            _scenario(h, f, sa, sb)
            diffs += h.compare(0x0050B9A0, regs={UC_X86_REG_ECX: this}, ret=None)

        # and the fixed behaviour itself: a waited troop moves after the troops that have not acted
        recs = []
        def on_wait(uc, addr, size, user):
            sp = uc.reg_read(UC_X86_REG_ESP)
            recs.append((struct.unpack('<I', uc.mem_read(sp + 4, 4))[0],
                         struct.unpack('<I', uc.mem_read(sp + 8, 4))[0]))
        hk = h.uc.hook_add(UC_HOOK_CODE, on_wait, begin=0x0057BB20, end=0x0057BB20)
        try:
            _scenario(h, f, 2, 1)
            h.call(0x0050B9A0, regs={UC_X86_REG_ECX: this})
            st = struct.unpack('<IIII', h.uc.mem_read(entries, 16))
            if st != (ta, 2, tb, 2):
                diffs.append('wait: states %r, want (A 2, B 2)' % (st,))
            if _r(h, this + 0x64) != tb:
                diffs.append('wait: current troop %08X, want the waited B %08X' % (_r(h, this + 0x64), tb))
            if _r(h, this + 0x27c) != entries + 8:
                diffs.append('wait: +0x27C %08X, want the B entry %08X' % (_r(h, this + 0x27c), entries + 8))
            if _r(h, this + 0x1c4) != 1:
                diffs.append('wait: round %d, want 1 (no new round before the waited troop moves)' % _r(h, this + 0x1c4))
            if recs != [(WAIT_KEY, 1)]:
                diffs.append('wait: _IsWaitMove write %r, want [(%08X, 1)]' % (recs, WAIT_KEY))

            _scenario(h, f, 0, 1)
            recs[:] = []
            h.call(0x0050B9A0, regs={UC_X86_REG_ECX: this})
            if _r(h, this + 0x64) != ta or _r(h, this + 0x1c4) != 1 or recs != [(WAIT_KEY, 0)]:
                diffs.append('next: troop %08X round %d write %r, want A %08X, 1, [(%08X, 0)]'
                             % (_r(h, this + 0x64), _r(h, this + 0x1c4), recs, ta, WAIT_KEY))

            _scenario(h, f, 2, 2)
            recs[:] = []
            h.call(0x0050B9A0, regs={UC_X86_REG_ECX: this})
            st = struct.unpack('<IIII', h.uc.mem_read(entries, 16))
            if st != (ta, 2, tb, 0) or _r(h, this + 0x64) != ta or _r(h, this + 0x1c4) != 2:
                diffs.append('round: states %r troop %08X round %d, want (A 2, B 0), A, 2'
                             % (st, _r(h, this + 0x64), _r(h, this + 0x1c4)))
        finally:
            h.uc.hook_del(hk)
    finally:
        for a, old in saved:
            h.uc.mem_write(a, old)
        h.uc.mem_write(0x006CA8E0, lis)
    return diffs


def test_0050B9A0_wait(h): return run(h)
