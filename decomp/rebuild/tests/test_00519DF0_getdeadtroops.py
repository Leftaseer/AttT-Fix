"""Lua_006C6A20::GetDeadTroops (0x519DF0): the wrapper's level (+0xBC) troop list (+0x50 array, +0x54 count,
0xC8-byte elements) becomes a table of {liter, name, qn} tables for the elements whose bit vector (+0x88/+0x8C)
is non-empty; elements are skipped but keep counting their index.  Both halves run, then the test reads the
returned table back through the Lua API (the differential run already compares the interned strings)."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C
NEWSTATE = 0x00402870
GETTOP = 0x00402A60
SETTOP = 0x00402A70
TONUMBER = 0x00402DE0
TYPE = 0x00402C20
GETFIELD = 0x00403300
RAWGETI = 0x00403390

GETDEADTROOPS = 0x00519DF0
LUA_TTABLE = 5
LUA_TNUMBER = 3
LUA_TSTRING = 4
ELEMENT_STRIDE = 0xC8


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
    kind = _call(h, TYPE, (state, -1))['eax']
    value = _call(h, TONUMBER, (state, -1))['st0'] if kind == LUA_TNUMBER else None
    _call(h, SETTOP, (state, -2))
    return kind, value


def _troop(h, state, index):
    _call(h, RAWGETI, (state, -1, index))
    if _call(h, TYPE, (state, -1))['eax'] != LUA_TTABLE:
        raise AssertionError('entry %d is not a table' % index)
    return {name: _field(h, state, name.encode() + b'\0')
            for name in ('liter', 'name', 'qn')}


def _element(h, array, index, name, qn):
    element = array + index * ELEMENT_STRIDE
    owner = h.alloc(0x40, bytes(0x40))
    text = owner + 8
    h.uc.mem_write(text + 4, name + b'\0')
    h.uc.mem_write(text + 0x14, struct.pack('<II', len(name), 15))
    reference = h.alloc(4, struct.pack('<I', owner))
    h.uc.mem_write(element + 0x58, struct.pack('<I', reference))
    h.uc.mem_write(element + 0x88, struct.pack('<II', 0x30000000, 0x30000000 + 4 * qn))


def test_get_dead_troops(h):
    state = _state(h)
    array = h.alloc(3 * ELEMENT_STRIDE, bytes(3 * ELEMENT_STRIDE))
    _element(h, array, 0, b'Boris', 4)
    _element(h, array, 2, b'Ivan', 1)
    level = h.alloc(0x100, bytes(0x100))
    h.uc.mem_write(level + 0x50, struct.pack('<II', array, 3))
    wrapper = h.alloc(0x100, bytes(0x100))
    h.uc.mem_write(wrapper + 0xbc, struct.pack('<I', level))

    diffs = h.compare(GETDEADTROOPS, args=(0,), regs={UC_X86_REG_ECX: wrapper})
    if diffs:
        return diffs

    res = _call(h, h.to_rebuilt(GETDEADTROOPS), args=(0,), regs={UC_X86_REG_ECX: wrapper})
    if res['eax'] != 1:
        return ['returns %d, want 1' % res['eax']]
    top = _call(h, GETTOP, (state,))['eax']
    if top != 1:
        return ['left %d values on the stack, want 1' % top]
    if _call(h, TYPE, (state, -1))['eax'] != LUA_TTABLE:
        return ['the pushed value is not a table']

    first = _troop(h, state, 1)
    _call(h, SETTOP, (state, -2))
    second = _troop(h, state, 2)
    _call(h, SETTOP, (state, -2))
    if first['liter'] != (LUA_TNUMBER, 0.0) or first['qn'] != (LUA_TNUMBER, 4.0):
        return ['entry 1 is liter/qn %r/%r, want 0/4' % first['liter'], first['qn']]
    if first['name'][0] != LUA_TSTRING:
        return ['entry 1 name is type %d, want string' % first['name'][0]]
    if second['liter'] != (LUA_TNUMBER, 2.0) or second['qn'] != (LUA_TNUMBER, 1.0):
        return ['entry 2 is liter/qn %r/%r, want 2/1' % (second['liter'], second['qn'])]
    if second['name'][0] != LUA_TSTRING:
        return ['entry 2 name is type %d, want string' % second['name'][0]]
    _call(h, SETTOP, (state, 0))
    return None
