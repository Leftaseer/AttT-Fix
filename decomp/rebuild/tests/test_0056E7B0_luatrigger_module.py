"""The LuaTrigger module's registration (luatrigger.cpp): 0x569F10 puts the named functions of a {name; data}
table into the table on top of the Lua stack (the closure gets the entry as its upvalue), and 0x56E7B0 registers
the module table in _G (its "new" is 0x568300), its metatable in the registry (0x6C0F90: "delete", "__tostring",
"__eq", "__gc", "__index") and then the named functions of 0x8D105C.  The tests run against a real Lua state."""
import struct

LUA_STATE_SLOT = 0x008D122C
MODULE_TABLE = 0x008D0990
METATABLE_REF = 0x006C0F90

FILL = 0x00569F10
REGISTER = 0x0056E7B0

NEWSTATE = 0x00402870
GETTOP = 0x00402A60
SETTOP = 0x00402A70
TYPE = 0x00402C20
GETFIELD = 0x00403300
CREATETABLE = 0x004033D0
RAWGETI = 0x00403390

LUA_REGISTRY = -10000
LUA_GLOBALS = -10002
LUA_TNIL = 0
LUA_TTABLE = 5
LUA_TFUNCTION = 6


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _call(h, entry, args=()):
    res = h.call(entry, args=args)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _state(h):
    state = _call(h, NEWSTATE)['eax']
    h.uc.mem_write(LUA_STATE_SLOT, struct.pack('<I', state))
    return state


def _top(h, state):
    return _call(h, GETTOP, args=(state,))['eax']


def _stack_type(h, state, index):
    return _call(h, TYPE, args=(state, index))['eax']


def _getfield(h, state, index, name):
    _call(h, GETFIELD, args=(state, index, name))
    return _stack_type(h, state, -1)


def test_fill_named_functions(h):
    state = _state(h)
    _call(h, CREATETABLE, args=(state, 0, 0))          # the table the functions enter, index 1
    alpha = h.alloc(6, b'Alpha\0')
    beta = h.alloc(5, b'Beta\0')
    entries = h.alloc(24, bytes(24))
    h.uc.mem_write(entries, struct.pack('<II', alpha, 0x1111))
    h.uc.mem_write(entries + 8, struct.pack('<II', beta, 0x2222))

    diffs = h.compare(FILL, args=(entries,), ret=None)
    if diffs:
        return diffs
    _call(h, FILL, args=(entries,))
    if _top(h, state) != 1:
        return ['top %d after the fill, want 1' % _top(h, state)]
    if _getfield(h, state, -1, alpha) != LUA_TFUNCTION:
        return ['Alpha is not a function']
    _call(h, SETTOP, args=(state, -2))
    if _getfield(h, state, -1, beta) != LUA_TFUNCTION:
        return ['Beta is not a function']
    _call(h, SETTOP, args=(state, -2))
    missing = h.alloc(8, b'Missing\0')
    if _getfield(h, state, -1, missing) != LUA_TNIL:
        return ['Missing was set']
    _call(h, SETTOP, args=(state, -2))

    empty = h.alloc(8, bytes(8))

    def setup_empty(h):
        _call(h, SETTOP, args=(state, 0))
        _call(h, CREATETABLE, args=(state, 0, 0))

    diffs = h.compare(FILL, args=(empty,), setup=setup_empty, ret=None)
    if diffs:
        return ['no entries: %s' % d for d in diffs]
    setup_empty(h)
    _call(h, FILL, args=(empty,))
    if _top(h, state) != 1:
        return ['no entries: top %d, want 1' % _top(h, state)]
    return None


def test_register_module(h):
    state = _state(h)
    name = h.alloc(11, b'LuaTrigger\0')
    new_key = h.alloc(4, b'new\0')
    delete_key = h.alloc(7, b'delete\0')
    tostring_key = h.alloc(11, b'__tostring\0')
    eq_key = h.alloc(5, b'__eq\0')
    gc_key = h.alloc(5, b'__gc\0')
    index_key = h.alloc(8, b'__index\0')

    diffs = h.compare(REGISTER, args=(name,), ret=None)
    if diffs:
        return diffs
    _call(h, REGISTER, args=(name,))
    if _u32(h, MODULE_TABLE) != name:
        return ['the module table global is %08X, want the name %08X' % (_u32(h, MODULE_TABLE), name)]
    if _top(h, state) != 0:
        return ['top %d after the registration, want 0' % _top(h, state)]
    if _getfield(h, state, LUA_GLOBALS, name) != LUA_TTABLE:
        return ['_G[name] is not a table']
    if _getfield(h, state, -1, new_key) != LUA_TFUNCTION:
        return ['the module has no "new"']
    _call(h, SETTOP, args=(state, -2))

    reference = _u32(h, METATABLE_REF)
    if reference == 0:
        return ['the metatable was not referenced']
    _call(h, RAWGETI, args=(state, LUA_REGISTRY, reference))
    if _stack_type(h, state, -1) != LUA_TTABLE:
        return ['the registry entry is not the metatable table']
    if _getfield(h, state, -1, index_key) != LUA_TTABLE:
        return ['the metatable has no __index table']
    if _getfield(h, state, -1, delete_key) != LUA_TFUNCTION:
        return ['the methods have no "delete"']
    _call(h, SETTOP, args=(state, -2))
    _call(h, SETTOP, args=(state, -2))
    for key, field in ((tostring_key, '__tostring'), (eq_key, '__eq'), (gc_key, '__gc')):
        if _getfield(h, state, -1, key) != LUA_TFUNCTION:
            return ['the metatable has no %s' % field]
        _call(h, SETTOP, args=(state, -2))
    _call(h, SETTOP, args=(state, 0))
    return None
