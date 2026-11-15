"""The class method tables (luamethods.cpp): each init fills its table once behind a flag (0x8D0FCC..) and then
runs the class's walker, which pushes every named entry into the Lua table on top of the stack as a closure
taking the entry as its upvalue; the derived classes run their base class's init first and the GUI classes add
the shared tables.  The tests reset the table and flag, compare the init against the original in a real Lua
state, then check the table the walker made.  The walkers themselves are compared over a synthetic table."""
import struct

LUA_STATE_SLOT = 0x008D122C
NEWSTATE = 0x00402870
GETTOP = 0x00402A60
SETTOP = 0x00402A70
TYPE = 0x00402C20
GETFIELD = 0x00403300
CREATETABLE = 0x004033D0

LUA_TNIL = 0
LUA_TTABLE = 5
LUA_TFUNCTION = 6

INIT_CASES = [
    (0x0056A1B0, 0x006C6910, 0x008D0FCC, 192),  # ParticleSystem
    (0x0056A300, 0x006C69D0, 0x008D0FD0, 64),  # RenderObject
    (0x0056A380, 0x006C6A10, 0x008D0FD4, 256),  # TacticCreature
    (0x0056A540, 0x006C6B10, 0x008D0FD8, 496),  # WorldUnit
    (0x0056A880, 0x006C6D00, 0x008D0FDC, 320),  # ParticleSystemMesh
    (0x0056AAA0, 0x006C6E40, 0x008D0FE0, 208),  # GuiElement
    (0x0056AC10, 0x006C6F10, 0x008D0FE4, 112),  # Image
    (0x0056AD00, 0x006C6F80, 0x008D0FF8, 240),  # Text
    (0x0056AEC0, 0x006C7070, 0x008D1010, 48),  # Viewport
    (0x0056AFF0, 0x006C70A0, 0x008D1028, 112),  # GuiSceneClass
    (0x0056B0C0, 0x006C7110, 0x008D102C, 144),  # UnitIcon
    (0x0056B1E0, 0x006C71A0, 0x008D1030, 208),  # TroopIcon
    (0x0056B350, 0x006C7270, 0x008D1034, 80),  # Button
    (0x0056B3F0, 0x006C72C0, 0x008D1038, 240),  # GuiSceneClass2
    (0x0056B590, 0x006C73B0, 0x008D103C, 160),  # GuiSceneClass3
    (0x0056B6B0, 0x006C7450, 0x008D1040, 176),  # Npc
    (0x0056B7F0, 0x006C7500, 0x008D1044, 96),  # GuiSceneClassWorld
    (0x0056B8C0, 0x006C7560, 0x008D1058, 96),  # ItemIcon
    (0x0056B9A0, 0x006C75C0, 0x008D1064, 80),  # AttackSphere
    (0x0056BB50, 0x006C7610, 0x008D1098, 128),  # EnemyArmy
    (0x0056F5E0, 0x006C7690, 0x008D109C, 80),  # ChooseHeroRotator
    (0x004EE1C0, 0x006C2A30, 0x006CA83C, 64),  # UnitSoundManager
    (0x0047DB60, 0x006C1470, 0x006CA214, 96),  # MusicManager
]

WALKER_CASES = [
    (0x00569670, 16),
    (0x005696D0, 16),
    (0x00569730, 16),
    (0x00569790, 16),
    (0x005697F0, 16),
    (0x00569850, 16),
    (0x005698B0, 16),
    (0x00569910, 16),
    (0x00569970, 16),
    (0x005699D0, 16),
    (0x00569A30, 16),
    (0x00569A90, 16),
    (0x00569AF0, 16),
    (0x00569B50, 16),
    (0x00569BB0, 16),
    (0x00569C10, 16),
    (0x00569C70, 16),
    (0x00569CD0, 16),
    (0x00569D30, 16),
    (0x00569D90, 16),
    (0x00569DF0, 16),
    (0x00569E50, 16),
    (0x00569EB0, 16),
    (0x00569F70, 16),
    (0x00569FD0, 16),
    (0x0056A030, 16),
    (0x0056A090, 16),
    (0x0056A0F0, 8),
    (0x0056A150, 16),
    (0x004EDEF0, 16),
    (0x0047D470, 16),
]


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


def _table_top(h, state):
    """the empty table the init's walker fills, on top of the stack"""
    if _top(h, state) != 0:
        _call(h, SETTOP, args=(state, 0))
    _call(h, CREATETABLE, args=(state, 0, 0))
    return _stack_type(h, state, -1) == LUA_TTABLE


def _reset_class_table(h, base, guard, size):
    """back to the state before the init's first run: the first entry's name comes from the exe's data"""
    name = _u32(h, base)
    h.uc.mem_write(base, bytes(size))
    h.uc.mem_write(base, struct.pack('<I', name))
    h.uc.mem_write(guard, bytes(4))


def _check_fields(h, state, base, stride):
    entries = 0
    while True:
        name = _u32(h, base + entries * stride)
        if not name:
            break
        if _getfield(h, state, -1, name) != LUA_TFUNCTION:
            return ['%08X: entry %d is not a function' % (base, entries)]
        _call(h, SETTOP, args=(state, -2))
        entries += 1
    if _top(h, state) != 1:
        return ['top %d after the walker, want 1' % _top(h, state)]
    missing = h.alloc(8, b'NoSuch\0')
    if _getfield(h, state, -1, missing) != LUA_TNIL:
        return ['a missing name was set']
    _call(h, SETTOP, args=(state, 0))
    return None


def test_walker_00569670(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569670, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569670, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_005696D0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x005696D0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x005696D0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569730(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569730, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569730, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569790(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569790, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569790, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_005697F0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x005697F0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x005697F0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569850(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569850, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569850, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_005698B0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x005698B0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x005698B0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569910(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569910, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569910, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569970(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569970, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569970, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_005699D0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x005699D0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x005699D0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569A30(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569A30, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569A30, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569A90(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569A90, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569A90, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569AF0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569AF0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569AF0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569B50(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569B50, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569B50, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569BB0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569BB0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569BB0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569C10(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569C10, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569C10, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569C70(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569C70, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569C70, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569CD0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569CD0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569CD0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569D30(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569D30, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569D30, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569D90(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569D90, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569D90, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569DF0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569DF0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569DF0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569E50(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569E50, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569E50, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569EB0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569EB0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569EB0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569F70(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569F70, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569F70, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_00569FD0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x00569FD0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x00569FD0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_0056A030(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x0056A030, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A030, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_0056A090(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x0056A090, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A090, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_0056A0F0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 8
    methods = h.alloc(size, bytes(size))
    if 8 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x0056A0F0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A0F0, args=(methods,))
    return _check_fields(h, state, methods, 8)


def test_walker_0056A150(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x0056A150, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A150, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_004EDEF0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x004EDEF0, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x004EDEF0, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_walker_0047D470(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    name1 = h.alloc(6, b'Alpha\0')
    name2 = h.alloc(5, b'Beta\0')
    size = 3 * 16
    methods = h.alloc(size, bytes(size))
    if 16 == 16:
        h.uc.mem_write(methods, struct.pack('<IIII', name1, 0, 0x0054A680, 0))
        h.uc.mem_write(methods + 16, struct.pack('<IIII', name2, 0, 0x00562DA0, 0))
    else:
        h.uc.mem_write(methods, struct.pack('<II', name1, 0x0054A680))
        h.uc.mem_write(methods + 8, struct.pack('<II', name2, 0x00562DA0))
    diffs = h.compare(0x0047D470, args=(methods,), ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0047D470, args=(methods,))
    return _check_fields(h, state, methods, 16)


def test_init_0056A1B0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C6910, 0x008D0FCC, 192)
    diffs = h.compare(0x0056A1B0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A1B0)
    return _check_fields(h, state, 0x006C6910, 16)


def test_init_0056A300(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C69D0, 0x008D0FD0, 64)
    diffs = h.compare(0x0056A300, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A300)
    return _check_fields(h, state, 0x006C69D0, 16)


def test_init_0056A380(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C6A10, 0x008D0FD4, 256)
    diffs = h.compare(0x0056A380, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A380)
    return _check_fields(h, state, 0x006C6A10, 16)


def test_init_0056A540(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C6B10, 0x008D0FD8, 496)
    diffs = h.compare(0x0056A540, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A540)
    return _check_fields(h, state, 0x006C6B10, 16)


def test_init_0056A880(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C6D00, 0x008D0FDC, 320)
    diffs = h.compare(0x0056A880, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056A880)
    return _check_fields(h, state, 0x006C6D00, 16)


def test_init_0056AAA0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C6E40, 0x008D0FE0, 208)
    diffs = h.compare(0x0056AAA0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056AAA0)
    return _check_fields(h, state, 0x006C6E40, 16)


def test_init_0056AC10(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C6F10, 0x008D0FE4, 112)
    diffs = h.compare(0x0056AC10, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056AC10)
    return _check_fields(h, state, 0x006C6F10, 16)


def test_init_0056AD00(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C6F80, 0x008D0FF8, 240)
    diffs = h.compare(0x0056AD00, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056AD00)
    return _check_fields(h, state, 0x006C6F80, 16)


def test_init_0056AEC0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C7070, 0x008D1010, 48)
    diffs = h.compare(0x0056AEC0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056AEC0)
    return _check_fields(h, state, 0x006C7070, 16)


def test_init_0056AFF0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C70A0, 0x008D1028, 112)
    diffs = h.compare(0x0056AFF0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056AFF0)
    return _check_fields(h, state, 0x006C70A0, 16)


def test_init_0056B0C0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C7110, 0x008D102C, 144)
    diffs = h.compare(0x0056B0C0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B0C0)
    return _check_fields(h, state, 0x006C7110, 16)


def test_init_0056B1E0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C71A0, 0x008D1030, 208)
    diffs = h.compare(0x0056B1E0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B1E0)
    return _check_fields(h, state, 0x006C71A0, 16)


def test_init_0056B350(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C7270, 0x008D1034, 80)
    diffs = h.compare(0x0056B350, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B350)
    return _check_fields(h, state, 0x006C7270, 16)


def test_init_0056B3F0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C72C0, 0x008D1038, 240)
    diffs = h.compare(0x0056B3F0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B3F0)
    return _check_fields(h, state, 0x006C72C0, 16)


def test_init_0056B590(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C73B0, 0x008D103C, 160)
    diffs = h.compare(0x0056B590, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B590)
    return _check_fields(h, state, 0x006C73B0, 16)


def test_init_0056B6B0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C7450, 0x008D1040, 176)
    diffs = h.compare(0x0056B6B0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B6B0)
    return _check_fields(h, state, 0x006C7450, 16)


def test_init_0056B7F0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C7500, 0x008D1044, 96)
    diffs = h.compare(0x0056B7F0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B7F0)
    return _check_fields(h, state, 0x006C7500, 16)


def test_init_0056B8C0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C7560, 0x008D1058, 96)
    diffs = h.compare(0x0056B8C0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B8C0)
    return _check_fields(h, state, 0x006C7560, 16)


def test_init_0056B9A0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C75C0, 0x008D1064, 80)
    diffs = h.compare(0x0056B9A0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056B9A0)
    return _check_fields(h, state, 0x006C75C0, 16)


def test_init_0056BB50(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C7610, 0x008D1098, 128)
    diffs = h.compare(0x0056BB50, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056BB50)
    return _check_fields(h, state, 0x006C7610, 16)


def test_init_0056F5E0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C7690, 0x008D109C, 80)
    diffs = h.compare(0x0056F5E0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0056F5E0)
    return _check_fields(h, state, 0x006C7690, 16)


def test_init_004EE1C0(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C2A30, 0x006CA83C, 64)
    diffs = h.compare(0x004EE1C0, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x004EE1C0)
    return _check_fields(h, state, 0x006C2A30, 16)


def test_init_0047DB60(h):
    state = _state(h)
    if not _table_top(h, state):
        return ['no table']
    _reset_class_table(h, 0x006C1470, 0x006CA214, 96)
    diffs = h.compare(0x0047DB60, ret=None)
    if diffs:
        return diffs
    _table_top(h, state)
    _call(h, 0x0047DB60)
    return _check_fields(h, state, 0x006C1470, 16)


