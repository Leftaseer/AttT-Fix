"""The four wrapper bindings 0x563CC0/0x563DD0/0x563ED0/0x563FE0 (the closures _G.String, _G.LuaWrapper,
_G.CWorldHero and _G.CBorder hold): with a null collector they push nil; otherwise they build the class's method
table (each method a dispatcher closure carrying the method's index), wrap the collector in a fresh object at
table[0] and return the table.  The tests stub the four constructors (a bare "return this"), compare against the
original in a real Lua state, then check the table the rebuilt code leaves behind."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C
NEWSTATE = 0x00402870
GETTOP = 0x00402A60
SETTOP = 0x00402A70
TYPE = 0x00402C20
GETFIELD = 0x00403300
RAWGETI = 0x00403390

LUA_TNIL = 0
LUA_TLIGHTUSERDATA = 2
LUA_TTABLE = 5
LUA_TFUNCTION = 6

# entry, the collector slot it wraps, method names the table must carry
CASES = [
    (0x00563CC0, 0x006CA98C, ()),
    (0x00563DD0, 0x008D0FC4, (b'MatrixRotationAxis\0', b'Vec3Transform\0')),
    (0x00563ED0, 0x006CAAC8, (b'GetPos\0', b'GetGold\0', b'AddGold\0')),
    (0x00563FE0, 0x008D0FC8, (b'GetMovePoints\0', b'CalcVectorPosToNext\0')),
]
CTORS = (0x004AFEF0, 0x00571130, 0x00465950, 0x00525B50)
CTOR_STUB = b'\x8b\xc1\xc2\x08\x00'  # mov eax, ecx; ret 8


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


def test_binding_without_collector(h):
    state = _state(h)
    for entry, slot, _ in CASES:
        h.uc.mem_write(slot, bytes(4))
        _call(h, SETTOP, args=(state, 0))
        diffs = h.compare(entry, args=(state,))
        if diffs:
            return diffs
        if _call(h, entry, args=(state,))['eax'] != 1:
            return ['%08X did not return one value' % entry]
        if _top(h, state) != 1:
            return ['%08X: top %d, want the one nil' % (entry, _top(h, state))]
        if _stack_type(h, state, -1) != LUA_TNIL:
            return ['%08X pushed %d, want nil' % (entry, _stack_type(h, state, -1))]
        _call(h, SETTOP, args=(state, 0))
    return None


def test_binding_tables(h):
    state = _state(h)
    collector = h.alloc(8, bytes(8))

    saved = []
    for va in CTORS:
        # a translated constructor has its own entry (the rebuilt code calls the compiled body directly)
        for addr in {va, h.to_rebuilt(va), h.symbols.get('_f_%08X' % va)} - {None}:
            saved.append((addr, bytes(h.uc.mem_read(addr, len(CTOR_STUB)))))
            h.uc.mem_write(addr, CTOR_STUB)
            # a previous test may have run the relinked entry: drop its translation or Unicorn replays it
            h.uc.ctl_remove_cache(addr, addr + len(CTOR_STUB))
    try:
        for entry, slot, methods in CASES:
            h.uc.mem_write(slot, struct.pack('<I', collector))
            _call(h, SETTOP, args=(state, 0))
            diffs = h.compare(entry, args=(state,))
            if diffs:
                return diffs
            _call(h, entry, args=(state,))
            if _top(h, state) != 1:
                return ['%08X: top %d, want the one table' % (entry, _top(h, state))]
            if _stack_type(h, state, -1) != LUA_TTABLE:
                return ['%08X pushed a non-table' % entry]
            for name in methods:
                key = h.alloc(len(name), name)
                if _getfield(h, state, -1, key) != LUA_TFUNCTION:
                    return ['%08X: %s is not a function' % (entry, name.split(b'\0')[0].decode())]
                _call(h, SETTOP, args=(state, -2))
            _call(h, RAWGETI, args=(state, -1, 0))
            if _stack_type(h, state, -1) != LUA_TLIGHTUSERDATA:
                return ['%08X: table[0] is not the wrapped object' % entry]
            if _u32(h, _u32(h, state + 8) - 8) == 0:
                return ['%08X: table[0] is null' % entry]
            _call(h, SETTOP, args=(state, 0))
    finally:
        for addr, data in saved:
            h.uc.mem_write(addr, data)
            h.uc.ctl_remove_cache(addr, addr + len(data))
    return None
