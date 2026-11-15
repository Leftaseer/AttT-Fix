"""Lua_006C6A20::GetPos (0x513540): the wrapper's position (+0x64 x, +0x68 y, +0x6C z) goes into a fresh
nScript::Table, whose registry ref is pushed for the script to take: the test runs both halves, then reads the
returned table's x, y and z back through the Lua API."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C
NEWSTATE = 0x00402870
GETTOP = 0x00402A60
SETTOP = 0x00402A70
TONUMBER = 0x00402DE0
TYPE = 0x00402C20
GETFIELD = 0x00403300

GETPOS = 0x00513540
LUA_TTABLE = 5
LUA_TNUMBER = 3


def _call(h, entry, args=(), regs=None):
    res = h.call(entry, args=args, regs=regs)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _state(h):
    state = _call(h, NEWSTATE)['eax']
    h.uc.mem_write(LUA_STATE_SLOT, struct.pack('<I', state))
    return state


def _field(h, state, name):
    key = h.alloc(len(name), name)
    _call(h, GETFIELD, (state, -1, key))
    if _call(h, TYPE, (state, -1))['eax'] != LUA_TNUMBER:
        return None
    value = _call(h, TONUMBER, (state, -1))['st0']
    _call(h, SETTOP, (state, -2))
    return value


def test_get_pos(h):
    state = _state(h)
    wrapper = h.alloc(0x80, bytes(0x80))
    h.uc.mem_write(wrapper + 0x64, struct.pack('<fff', 1.5, -2.25, 3.75))

    diffs = h.compare(GETPOS, args=(0,), regs={UC_X86_REG_ECX: wrapper})
    if diffs:
        return diffs

    res = _call(h, h.to_rebuilt(GETPOS), args=(0,), regs={UC_X86_REG_ECX: wrapper})
    if res['eax'] != 1:
        return ['returns %d, want 1' % res['eax']]
    if _call(h, GETTOP, (state,))['eax'] != 1:
        return ['left %d values on the stack, want 1' % _call(h, GETTOP, (state,))['eax']]
    if _call(h, TYPE, (state, -1))['eax'] != LUA_TTABLE:
        return ['the pushed value is not a table']
    for name, want in ((b'x\0', 1.5), (b'y\0', -2.25), (b'z\0', 3.75)):
        got = _field(h, state, name)
        if got != want:
            return ['%s is %r, want %r' % (name.split(b'\0')[0].decode(), got, want)]
    _call(h, SETTOP, (state, 0))
    return None
