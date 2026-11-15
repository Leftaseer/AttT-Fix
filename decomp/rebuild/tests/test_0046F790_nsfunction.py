"""nScript::Function and nScript::TableGet (nscript.cpp): construction from a Lua stack index (0x46F790),
assignment (0x436FD0), destruction (0x4378D0), calling (0x57A180), the TableGet lifetime (0x4277B0 / 0x427820),
reading a Function out of a read (0x46F810) and the value reference the script handlers use (0x46FA90).

The tests create a real Lua 5.1 state (luaL_newstate 0x402870) and load a chunk with luaL_loadbuffer, so the
registry references and the stack are the engine's own."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C
LUA_REGISTRY = -10000
LUA_TFUNCTION = 6

NEWSTATE = 0x00402870
LOADBUFFER = 0x004026F0
GETTOP = 0x00402A60
PUSHNUMBER = 0x004030A0
RAWEQUAL = 0x00402D10
RAWGETI = 0x00403390
TONUMBER = 0x00402DE0
TOBOOLEAN = 0x00402EA0

FUNCTION_CTOR = 0x0046F790
FUNCTION_ASSIGN = 0x00436FD0
FUNCTION_DTOR = 0x004378D0
FUNCTION_CALL = 0x0057A180
TABLEGET_CTOR = 0x004277B0
TABLEGET_DTOR = 0x00427820
TABLEGET_FUNCTION = 0x0046F810
VALUE_FUNCTION = 0x0046FA90

FUNCTION_VTABLE = 0x006098F0
TABLE_VTABLE = 0x00607CC4
TABLEGET_VTABLE = 0x00608260
OBJECT_VTABLE = 0x00607C88
VM_VTABLE = 0x00607CB8
CALL_TABLE = 0x0061D90C


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _call(h, entry, args=(), regs=None):
    res = h.call(entry, args=args, regs=regs)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _state(h):
    """a fresh Lua state installed in the engine's global"""
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


def _push_number(h, state, value):
    """one TValue (the float, then its type) on top of the state's stack"""
    top = _u32(h, state + 8)
    h.uc.mem_write(top, struct.pack('<fI', value, 3))
    h.uc.mem_write(state + 8, struct.pack('<I', top + 8))


def _fields(h, addr, count):
    return struct.unpack('<%dI' % count, h.uc.mem_read(addr, 4 * count))


def _check_function(h, addr, want_ref=None):
    got = _fields(h, addr, 6)
    diffs = []
    if got[0] != FUNCTION_VTABLE:
        diffs.append('vtable %08X, want %08X' % (got[0], FUNCTION_VTABLE))
    if got[1] != 0:
        diffs.append('owner %08X, want 0' % got[1])
    if got[2] != TABLE_VTABLE or got[3] != 0 or got[4] != 0xFFFFFFFF:
        diffs.append('table (%08X, %08X, %08X), want (%08X, 0, -1)'
                     % (got[2], got[3], got[4], TABLE_VTABLE))
    if got[5] == 0:
        diffs.append('reference 0: the value was not referenced')
    if want_ref is not None and got[5] != want_ref:
        diffs.append('reference %08X, want %08X' % (got[5], want_ref))
    return diffs, got[5]


def test_function_constructor(h):
    for position, index, chunks in ((1, 1, 1), (2, 2, 2), (3, -1, 2)):
        out = h.alloc(0x18, bytes(0x18))

        def setup(h, chunks=chunks):
            state = _state(h)
            for _ in range(chunks):
                _load(h, state, 'return true')

        diffs = h.compare(FUNCTION_CTOR, args=(index,), regs={UC_X86_REG_ECX: out}, ret='eax',
                          setup=setup)
        if diffs:
            return ['index %d: %s' % (index, d) for d in diffs]

        res = _call(h, FUNCTION_CTOR, args=(index,), regs={UC_X86_REG_ECX: out})
        if res['eax'] != out:
            return ['index %d: returned %08X, want %08X' % (index, res['eax'], out)]
        diffs, _ = _check_function(h, out)
        if diffs:
            return ['index %d: %s' % (index, d) for d in diffs]
    return None


def test_function_assignment(h):
    first = h.alloc(0x18, bytes(0x18))
    second = h.alloc(0x18, bytes(0x18))

    def setup(h):
        state = _state(h)
        _load(h, state, 'return true')
        _load(h, state, 'return "b"')
        _call(h, FUNCTION_CTOR, args=(1,), regs={UC_X86_REG_ECX: first})
        _call(h, FUNCTION_CTOR, args=(2,), regs={UC_X86_REG_ECX: second})

    diffs = h.compare(FUNCTION_ASSIGN, args=(second,), regs={UC_X86_REG_ECX: first}, ret='eax',
                      setup=setup)
    if diffs:
        return diffs

    state = _u32(h, LUA_STATE_SLOT)
    res = _call(h, FUNCTION_ASSIGN, args=(second,), regs={UC_X86_REG_ECX: first})
    if res['eax'] != first:
        return ['returned %08X, want %08X' % (res['eax'], first)]
    diffs, first_ref = _check_function(h, first)
    diffs2, second_ref = _check_function(h, second)
    if diffs or diffs2:
        return diffs + diffs2
    _call(h, RAWGETI, args=(state, LUA_REGISTRY, first_ref))
    if _call(h, RAWEQUAL, args=(state, -1, 2))['eax'] != 1:
        return ['the assignment did not take the second function (reference %08X)' % first_ref]
    return None


def test_function_destructor(h):
    function = h.alloc(0x18, bytes(0x18))

    def setup(h):
        state = _state(h)
        _load(h, state, 'return true')
        _call(h, FUNCTION_CTOR, args=(1,), regs={UC_X86_REG_ECX: function})

    diffs = h.compare(FUNCTION_DTOR, regs={UC_X86_REG_ECX: function}, ret=None, setup=setup)
    if diffs:
        return diffs

    reference = _u32(h, function + 0x14)
    _call(h, FUNCTION_DTOR, regs={UC_X86_REG_ECX: function})
    got = _fields(h, function, 6)
    if got[0] != OBJECT_VTABLE or got[1] != 0:
        return ['object (%08X, %08X), want (%08X, 0)' % (got[0], got[1], OBJECT_VTABLE)]
    if got[2] != OBJECT_VTABLE or got[3] != 0 or got[4] != 0xFFFFFFFF:
        return ['table (%08X, %08X, %08X), want (%08X, 0, -1)'
                % (got[2], got[3], got[4], OBJECT_VTABLE)]
    if got[5] != reference:
        return ['reference %08X, want the kept %08X' % (got[5], reference)]
    return None


def test_function_call(h):
    function = h.alloc(0x18, bytes(0x18))
    read = h.alloc(0x18, bytes(0x18))

    def setup(h):
        state = _state(h)
        _load(h, state, 'return true')
        _call(h, FUNCTION_CTOR, args=(1,), regs={UC_X86_REG_ECX: function})

    diffs = h.compare(FUNCTION_CALL, args=(read, 1), regs={UC_X86_REG_ECX: function}, ret='eax',
                      setup=setup)
    if diffs:
        return diffs

    state = _u32(h, LUA_STATE_SLOT)
    res = _call(h, FUNCTION_CALL, args=(read, 1), regs={UC_X86_REG_ECX: function})
    if res['eax'] != read:
        return ['returned %08X, want the out address %08X' % (res['eax'], read)]
    got = _fields(h, read, 6)
    if got[0] != TABLEGET_VTABLE or got[1] != 0 or got[2] != CALL_TABLE:
        return ['read (%08X, %08X, %08X), want (%08X, 0, %08X)'
                % (got[0], got[1], got[2], TABLEGET_VTABLE, CALL_TABLE)]
    if got[3] != 1 or got[4] != 1 or got[5] != 1:
        return ['read (count %d, base %d, owns %d), want (1, 1, 1)' % (got[3], got[4], got[5])]
    if _top(h, state) != 2:
        return ['top %d after the call, want 2' % _top(h, state)]
    if _call(h, TOBOOLEAN, args=(state, 2))['eax'] != 1:
        return ['the call result is not true']
    return None


def test_table_get_lifetime(h):
    read = h.alloc(0x18, bytes(0x18))

    def setup(h):
        state = _state(h)
        _push_number(h, state, 10.0)
        _push_number(h, state, 20.0)

    diffs = h.compare(TABLEGET_CTOR, args=(CALL_TABLE, 2, 1), regs={UC_X86_REG_ECX: read}, ret='eax',
                      setup=setup)
    if diffs:
        return ['ctor: %s' % d for d in diffs]

    state = _u32(h, LUA_STATE_SLOT)
    _call(h, TABLEGET_CTOR, args=(CALL_TABLE, 2, 1), regs={UC_X86_REG_ECX: read})
    got = _fields(h, read, 6)
    if got[0] != TABLEGET_VTABLE or got[1] != 0 or got[2] != CALL_TABLE:
        return ['read (%08X, %08X, %08X), want (%08X, 0, %08X)'
                % (got[0], got[1], got[2], TABLEGET_VTABLE, CALL_TABLE)]
    if got[3] != 2 or got[4] != 0 or (got[5] & 0xFF) != 1:
        return ['read (count %d, base %d, owns %d), want (2, 0, 1)' % (got[3], got[4], got[5] & 0xFF)]

    diffs = h.compare(TABLEGET_DTOR, regs={UC_X86_REG_ECX: read}, ret=None)
    if diffs:
        return ['dtor: %s' % d for d in diffs]
    if _top(h, state) != 2:
        return ['the dtor ran before the pop check']
    _call(h, TABLEGET_DTOR, regs={UC_X86_REG_ECX: read})
    if _top(h, state) != 0:
        return ['top %d after the owned read died, want 0' % _top(h, state)]

    _push_number(h, state, 10.0)
    _push_number(h, state, 20.0)
    _call(h, TABLEGET_CTOR, args=(CALL_TABLE, 2, 0), regs={UC_X86_REG_ECX: read})
    _call(h, TABLEGET_DTOR, regs={UC_X86_REG_ECX: read})
    if _top(h, state) != 2:
        return ['top %d after the borrowed read died, want 2' % _top(h, state)]
    return None


def test_table_get_function_at(h):
    read = h.alloc(0x18, bytes(0x18))
    function = h.alloc(0x18, bytes(0x18))

    def setup(h):
        state = _state(h)
        _push_number(h, state, 10.0)
        _push_number(h, state, 20.0)
        _call(h, TABLEGET_CTOR, args=(CALL_TABLE, 2, 0), regs={UC_X86_REG_ECX: read})

    diffs = h.compare(TABLEGET_FUNCTION, args=(function, 2), regs={UC_X86_REG_ECX: read}, ret='eax',
                      setup=setup)
    if diffs:
        return diffs

    state = _u32(h, LUA_STATE_SLOT)
    res = _call(h, TABLEGET_FUNCTION, args=(function, 2), regs={UC_X86_REG_ECX: read})
    if res['eax'] != function:
        return ['returned %08X, want the out address %08X' % (res['eax'], function)]
    diffs, reference = _check_function(h, function)
    if diffs:
        return diffs
    _call(h, RAWGETI, args=(state, LUA_REGISTRY, reference))
    value = h.call(TONUMBER, args=(state, -1))['st0']
    if value != 20.0:
        return ['the function references %r, want the second value 20' % (value,)]
    return None


def test_value_reference(h):
    read = h.alloc(0x18, bytes(0x18))
    value = h.alloc(8, struct.pack('<II', 0, 1))
    function = h.alloc(0x18, bytes(0x18))

    def setup(h):
        state = _state(h)
        _push_number(h, state, 10.0)
        _push_number(h, state, 20.0)
        _call(h, TABLEGET_CTOR, args=(CALL_TABLE, 2, 0), regs={UC_X86_REG_ECX: read})
        h.uc.mem_write(value, struct.pack('<II', read, 2))

    diffs = h.compare(VALUE_FUNCTION, args=(function,), regs={UC_X86_REG_ECX: value}, ret='eax',
                      setup=setup)
    if diffs:
        return diffs

    state = _u32(h, LUA_STATE_SLOT)
    res = _call(h, VALUE_FUNCTION, args=(function,), regs={UC_X86_REG_ECX: value})
    if res['eax'] != function:
        return ['returned %08X, want the out address %08X' % (res['eax'], function)]
    diffs, reference = _check_function(h, function)
    if diffs:
        return diffs
    _call(h, RAWGETI, args=(state, LUA_REGISTRY, reference))
    value = h.call(TONUMBER, args=(state, -1))['st0']
    if value != 20.0:
        return ['the function references %r, want the second value 20' % (value,)]
    return None
