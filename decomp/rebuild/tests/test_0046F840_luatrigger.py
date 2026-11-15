"""The map triggers (luatrigger.cpp): iTrigger construction / destruction (0x46F840 / 0x46F8C0) registers the
trigger with the list at 0x6C905C (slot 1 adds, slot 4 removes), LuaTrigger (0x46FAC0 / 0x46F920) holds the Lua
function the table get gave it, Update (0x46FA00) calls it and deletes the trigger through slot 0 when it returns
true, the userdata push (0x46F9C0 / 0x46F980) hands the trigger to the script with metatable 0x6C0F90, and
0x46FB70 is the deleting destructor.

The trigger list and the metatable are test doubles built in the harness heap: the list's slots are stubs that
count their calls, so registration and the fire-and-delete call are observable.  Everything is prepared before
h.compare, which puts the state back where it started after the two runs (and resets the heap pointer), so the
observations are made by running the replacement once more."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C
TRIGGER_LIST = 0x006C905C
TRIGGER_METATABLE = 0x006C0F90
LUA_REGISTRY = -10000

NEWSTATE = 0x00402870
LOADBUFFER = 0x004026F0
GETTOP = 0x00402A60
CREATETABLE = 0x004033D0
LUA_REF = 0x00402190
RAWGETI = 0x00403390
RAWEQUAL = 0x00402D10
LUA_TYPE = 0x00402C20
TABLEGET_CTOR = 0x004277B0

ITRIGGER_CTOR = 0x0046F840
ITRIGGER_DTOR = 0x0046F8C0
LUATRIGGER_CTOR = 0x0046FAC0
LUATRIGGER_DTOR = 0x0046F920
LUATRIGGER_UPDATE = 0x0046FA00
LUATRIGGER_PUSH = 0x0046F9C0
PUSH_TRIGGER = 0x0046F980
DELETE_LUATRIGGER = 0x0046FB70
TRIGGER_MODULE_NEW = 0x00568300

LUA_TFUNCTION = 6

ITRIGGER_VTABLE = 0x0060CC94
LUATRIGGER_VTABLE = 0x0060CCC0
FUNCTION_VTABLE = 0x006098F0
TABLE_VTABLE = 0x00607CC4
GAMEOBJECT_VTABLE = 0x00607D14
CALL_TABLE = 0x0061D90C


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _call(h, entry, args=(), regs=None):
    res = h.call(entry, args=args, regs=regs)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _state(h):
    res = _call(h, NEWSTATE)
    state = res['eax']
    h.uc.mem_write(LUA_STATE_SLOT, struct.pack('<I', state))
    return state


def _load(h, state, source):
    """loads a chunk; it stays as a function on top of the stack"""
    text = h.alloc(len(source) + 1, source.encode() + b'\0')
    name = h.alloc(8, b'=test\0')
    res = _call(h, LOADBUFFER, args=(state, text, len(source), name))
    if res['eax'] != 0:
        raise AssertionError('loading %r failed with %d' % (source, res['eax']))


def _top(h, state):
    return _call(h, GETTOP, args=(state,))['eax']


def _counter_stub(h, counter):
    """machine code: ++[counter]; ret 4 (a thiscall target taking one stacked argument)"""
    return h.alloc(12, b'\xff\x05' + struct.pack('<I', counter) + b'\xc2\x04\x00')


def _trigger_list(h):
    """a trigger list whose slots 1 and 4 count their calls; returns the two counters"""
    add = h.alloc(4, bytes(4))
    remove = h.alloc(4, bytes(4))
    vtable = h.alloc(0x20, bytes(0x20))
    h.uc.mem_write(vtable + 4, struct.pack('<I', _counter_stub(h, add)))
    h.uc.mem_write(vtable + 0x10, struct.pack('<I', _counter_stub(h, remove)))
    manager = h.alloc(8, bytes(8))
    h.uc.mem_write(manager, struct.pack('<I', vtable))
    h.uc.mem_write(TRIGGER_LIST, struct.pack('<I', manager))
    return add, remove


def _fields(h, addr, count):
    return struct.unpack('<%dI' % count, h.uc.mem_read(addr, 4 * count))


def _check_itrigger(h, trigger, want_vtable):
    got = _fields(h, trigger, 0x38 // 4)
    diffs = []
    if got[0] != want_vtable:
        diffs.append('vtable %08X, want %08X' % (got[0], want_vtable))
    if got[1] != 0:
        diffs.append('owner %08X, want 0' % got[1])
    return diffs


def test_itrigger_constructor(h):
    trigger = h.alloc(0x38, bytes(0x38))
    add, remove = _trigger_list(h)

    diffs = h.compare(ITRIGGER_CTOR, regs={UC_X86_REG_ECX: trigger}, ret='eax')
    if diffs:
        return diffs

    res = _call(h, ITRIGGER_CTOR, regs={UC_X86_REG_ECX: trigger})
    if res['eax'] != trigger:
        return ['returned %08X, want %08X' % (res['eax'], trigger)]
    diffs = _check_itrigger(h, trigger, ITRIGGER_VTABLE)
    if diffs:
        return diffs
    if _u32(h, add) != 1:
        return ['the constructor registered %d times with the trigger list, want 1' % _u32(h, add)]
    if _u32(h, remove) != 0:
        return ['the constructor unregistered %d times, want 0' % _u32(h, remove)]
    return None


def test_itrigger_destructor(h):
    trigger = h.alloc(0x38, bytes(0x38))
    add, remove = _trigger_list(h)
    _call(h, ITRIGGER_CTOR, regs={UC_X86_REG_ECX: trigger})
    if _u32(h, add) != 1:
        return ['setup: the constructor registered %d times, want 1' % _u32(h, add)]

    diffs = h.compare(ITRIGGER_DTOR, regs={UC_X86_REG_ECX: trigger}, ret=None)
    if diffs:
        return diffs

    _call(h, ITRIGGER_DTOR, regs={UC_X86_REG_ECX: trigger})
    diffs = _check_itrigger(h, trigger, GAMEOBJECT_VTABLE)
    if diffs:
        return ['after the destructor: ' + d for d in diffs]
    if _u32(h, remove) != 1:
        return ['the destructor unregistered %d times, want 1' % _u32(h, remove)]
    return None


def _script_trigger(h, source, read, trigger):
    """a Lua state whose stack holds source, a table get over it and a LuaTrigger built from it"""
    state = _state(h)
    _load(h, state, source)
    _call(h, TABLEGET_CTOR, args=(CALL_TABLE, 1, 0), regs={UC_X86_REG_ECX: read})
    _call(h, LUATRIGGER_CTOR, args=(read,), regs={UC_X86_REG_ECX: trigger})
    return state


def test_luatrigger_constructor(h):
    read, trigger = h.alloc(0x18), h.alloc(0x50, bytes(0x50))
    add, remove = _trigger_list(h)
    state = _state(h)
    _load(h, state, 'return true')
    _call(h, TABLEGET_CTOR, args=(CALL_TABLE, 1, 0), regs={UC_X86_REG_ECX: read})

    diffs = h.compare(LUATRIGGER_CTOR, args=(read,), regs={UC_X86_REG_ECX: trigger}, ret='eax')
    if diffs:
        return diffs

    res = _call(h, LUATRIGGER_CTOR, args=(read,), regs={UC_X86_REG_ECX: trigger})
    if res['eax'] != trigger:
        return ['returned %08X, want %08X' % (res['eax'], trigger)]
    got = _fields(h, trigger, 0x50 // 4)
    diffs = []
    if got[0] != LUATRIGGER_VTABLE:
        diffs.append('vtable %08X, want %08X' % (got[0], LUATRIGGER_VTABLE))
    if (got[14], got[15]) != (FUNCTION_VTABLE, 0):
        diffs.append('function (%08X, %08X), want (%08X, 0)' % (got[14], got[15], FUNCTION_VTABLE))
    if (got[16], got[17], got[18]) != (TABLE_VTABLE, 0, 0xFFFFFFFF):
        diffs.append('function table (%08X, %08X, %08X), want (%08X, 0, -1)'
                     % (got[16], got[17], got[18], TABLE_VTABLE))
    if got[19] == 0:
        diffs.append('the function was not referenced')
    if diffs:
        return diffs
    if _u32(h, add) != 1:
        return ['construction registered %d times with the trigger list, want 1' % _u32(h, add)]

    _call(h, RAWGETI, args=(state, LUA_REGISTRY, got[19]))
    if _call(h, RAWEQUAL, args=(state, -1, 1))['eax'] != 1:
        return ['the trigger references another value than the script it was built from']
    return None


def test_luatrigger_destructor(h):
    read, trigger = h.alloc(0x18), h.alloc(0x50, bytes(0x50))
    add, remove = _trigger_list(h)
    _script_trigger(h, 'return true', read, trigger)
    reference = _u32(h, trigger + 0x4C)

    diffs = h.compare(LUATRIGGER_DTOR, regs={UC_X86_REG_ECX: trigger}, ret=None)
    if diffs:
        return diffs

    _call(h, LUATRIGGER_DTOR, regs={UC_X86_REG_ECX: trigger})
    diffs = _check_itrigger(h, trigger, GAMEOBJECT_VTABLE)
    if diffs:
        return ['after the destructor: ' + d for d in diffs]
    if _u32(h, remove) != 1:
        return ['the destructor unregistered %d times, want 1' % _u32(h, remove)]
    if reference and _u32(h, trigger + 0x4C) != reference:
        return ['the function reference %08X was dropped, want the kept %08X'
                % (_u32(h, trigger + 0x4C), reference)]

    # the deleting destructor: with the delete flag clear only the object goes
    second = h.alloc(0x50, bytes(0x50))
    _call(h, LUATRIGGER_CTOR, args=(read,), regs={UC_X86_REG_ECX: second})
    diffs = h.compare(DELETE_LUATRIGGER, args=(0,), regs={UC_X86_REG_ECX: second}, ret='eax')
    if diffs:
        return ['deleting destructor: %s' % d for d in diffs]
    _call(h, DELETE_LUATRIGGER, args=(0,), regs={UC_X86_REG_ECX: second})
    diffs = _check_itrigger(h, second, GAMEOBJECT_VTABLE)
    if diffs:
        return ['after the deleting destructor: ' + d for d in diffs]
    return None


def test_luatrigger_update(h):
    for source, fired in (('return true', 1), ('return false', 0)):
        read, trigger = h.alloc(0x18), h.alloc(0x50, bytes(0x50))
        _trigger_list(h)
        state = _script_trigger(h, source, read, trigger)
        fire = h.alloc(4, bytes(4))
        vtable = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(vtable, struct.pack('<I', _counter_stub(h, fire)))
        h.uc.mem_write(trigger, struct.pack('<I', vtable))

        diffs = h.compare(LUATRIGGER_UPDATE, args=(0,), regs={UC_X86_REG_ECX: trigger}, ret='eax')
        if diffs:
            return ['%s: %s' % (source, d) for d in diffs]

        _call(h, LUATRIGGER_UPDATE, args=(0,), regs={UC_X86_REG_ECX: trigger})
        if _u32(h, fire) != fired:
            return ['%s: the trigger self-destructed %d times, want %d' % (source, _u32(h, fire), fired)]
        if _top(h, state) != 1:
            return ['%s: top %d after the update, want 1' % (source, _top(h, state))]
    return None


def test_trigger_userdata_push(h):
    trigger = h.alloc(0x50, bytes(0x50))
    state = _state(h)
    _call(h, CREATETABLE, args=(state, 0, 0))
    top = _u32(h, state + 8)
    metatable = _u32(h, top - 8)
    reference = _call(h, LUA_REF, args=(state, LUA_REGISTRY))['eax']
    h.uc.mem_write(TRIGGER_METATABLE, struct.pack('<i', reference))

    diffs = h.compare(LUATRIGGER_PUSH, regs={UC_X86_REG_ECX: trigger}, ret='eax')
    if diffs:
        return diffs

    res = _call(h, LUATRIGGER_PUSH, regs={UC_X86_REG_ECX: trigger})
    if res['eax'] != 1:
        return ['lua_setmetatable returned %d, want 1 (the metatable was not applied)' % res['eax']]
    if _top(h, state) != 1:
        return ['top %d after the push, want 1' % _top(h, state)]
    userdata = _u32(h, _u32(h, state + 8) - 8)      # the Udata block; its payload (u + 1) starts at +0x18
    if _u32(h, userdata + 0x18) != trigger:
        return ['the userdata holds %08X, want the trigger %08X' % (_u32(h, userdata + 0x18), trigger)]
    if _u32(h, userdata + 8) != metatable:
        return ['the userdata metatable is %08X, want the registry table %08X'
                % (_u32(h, userdata + 8), metatable)]

    diffs = h.compare(PUSH_TRIGGER, args=(trigger,), ret=None)
    if diffs:
        return ['free push: %s' % d for d in diffs]
    _call(h, PUSH_TRIGGER, args=(trigger,))
    if _top(h, state) != 2:
        return ['top %d after the free push, want 2' % _top(h, state)]
    userdata = _u32(h, _u32(h, state + 8) - 8)
    if _u32(h, userdata + 0x18) != trigger:
        return ['the free push holds %08X, want the trigger %08X' % (_u32(h, userdata + 0x18), trigger)]
    return None


def test_trigger_module_new(h):
    """0x568300, the trigger module's "new": the script at stack index 2 becomes a LuaTrigger, which is returned
    as userdata with the module's metatable."""
    state = _state(h)
    _call(h, CREATETABLE, args=(state, 0, 0))          # the receiver, index 1
    receiver = _u32(h, _u32(h, state + 8) - 8)
    _load(h, state, 'return true')                     # the script, index 2
    h.uc.mem_write(0x008D0990, struct.pack('<I', receiver))
    _call(h, CREATETABLE, args=(state, 0, 0))
    metatable = _u32(h, _u32(h, state + 8) - 8)
    reference = _call(h, LUA_REF, args=(state, LUA_REGISTRY))['eax']
    h.uc.mem_write(TRIGGER_METATABLE, struct.pack('<i', reference))
    add, remove = _trigger_list(h)

    diffs = h.compare(TRIGGER_MODULE_NEW, ret='eax')
    if diffs:
        return diffs

    res = _call(h, TRIGGER_MODULE_NEW)
    if res['eax'] != 1:
        return ['returned %d, want 1' % res['eax']]
    if _top(h, state) != 2:
        return ['top %d after the call, want 2 (the receiver and the userdata)' % _top(h, state)]
    userdata = _u32(h, _u32(h, state + 8) - 8)
    trigger = _u32(h, userdata + 0x18)
    if not trigger:
        return ['the userdata holds no trigger']
    got = _fields(h, trigger, 0x50 // 4)
    if got[0] != LUATRIGGER_VTABLE or got[14] != FUNCTION_VTABLE or got[19] == 0:
        return ['the trigger (%08X, function %08X, reference %08X) is not a built LuaTrigger'
                % (got[0], got[14], got[19])]
    if _u32(h, userdata + 8) != metatable:
        return ['the userdata metatable is %08X, want the module table %08X'
                % (_u32(h, userdata + 8), metatable)]
    if _u32(h, add) != 1:
        return ['the trigger registered %d times with the trigger list, want 1' % _u32(h, add)]
    _call(h, RAWGETI, args=(state, LUA_REGISTRY, got[19]))
    if _call(h, LUA_TYPE, args=(state, -1))['eax'] != LUA_TFUNCTION:
        return ['the trigger does not reference the script function']
    return None
