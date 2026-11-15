"""The class script modules (luaclass.cpp): every registrar stores the module name, puts the module table in _G
with its "new", refs the metatable in the registry ("delete", "__tostring", "__eq", "__gc", "__index" -> the
methods table) and fills the methods through its class-specific fillers.  Every registrar is checked against a
real Lua state: the name slot, the _G table with its "new", the registry metatable and its __index methods, and
the stack back to zero."""
import struct

LUA_STATE_SLOT = 0x008D122C
NEWSTATE = 0x00402870
GETTOP = 0x00402A60
SETTOP = 0x00402A70
TYPE = 0x00402C20
GETFIELD = 0x00403300
RAWGETI = 0x00403390

LUA_REGISTRY = -10000
LUA_GLOBALS = -10002
LUA_TTABLE = 5
LUA_TFUNCTION = 6

# entry, name slot, metatable ref slot, module name
CASES = [
    (0x0056BC40, 0x008CF1D8, 0x006C50C4, b'ParticleSystem'),
    (0x0056BE20, 0x008CF2E0, 0x006C6898, b'RenderObject'),
    (0x0056C000, 0x008CF3E8, 0x006C3410, b'TacticCreature'),
    (0x0056C1E0, 0x006CA838, 0x006C2A2C, b'UnitSoundManager'),
    (0x0056C3C0, 0x008CF4F0, 0x006C5030, b'WorldUnit'),
    (0x0056C5A0, 0x008CF5F8, 0x006C16FC, b'ParticleSystemMesh'),
    (0x0056C780, 0x008CF700, 0x006BF9A8, b'GUIElement'),
    (0x0056C960, 0x008CF808, 0x006C689C, b'Image'),
    (0x0056CB40, 0x008CF910, 0x006C68A0, b'ButtonContour'),
    (0x0056CD30, 0x008CFA18, 0x006C68A4, b'Text'),
    (0x0056CF10, 0x008CFB20, 0x006C0E48, b'ButtonAlpha'),
    (0x0056D110, 0x008CFC28, 0x006C68A8, b'Viewport'),
    (0x0056D2F0, 0x008CFD30, 0x006C68AC, b'Rect'),
    (0x0056D4E0, 0x008CFF40, 0x006C68B4, b'GUISceneClass'),
    (0x0056D6C0, 0x008D0048, 0x006C68B8, b'UnitIcon'),
    (0x0056D8A0, 0x008D0150, 0x006C68BC, b'TroopIcon'),
    (0x0056DA80, 0x008D0258, 0x006C68C0, b'Button'),
    (0x0056DC60, 0x008D0360, 0x006C32C8, b'GUISceneClass'),
    (0x0056DE40, 0x008D0468, 0x006C3504, b'GUISceneClass'),
    (0x0056E020, 0x008D0570, 0x006C1EA8, b'CNpc'),
    (0x0056E200, 0x008D0678, 0x006C4FD8, b'GUISceneClassWorld'),
    (0x0056E3E0, 0x008D0780, 0x006C1008, b'MainMenuSceneClass'),
    (0x0056E5D0, 0x008D0888, 0x006C68C4, b'ItemIcon'),
    (0x0056E9A0, 0x008D0A98, 0x006C3944, b'AttackSphere'),
    (0x0056EB80, 0x008D0BA0, 0x006C68C8, b'EditorArmy'),
    (0x0056ED70, 0x008D0CA8, 0x006C68CC, b'ToolTip'),
    (0x0056EF60, 0x008D0DB0, 0x006C1390, b'Message'),
    (0x0056F150, 0x006CA210, 0x006C146C, b'MusicManager'),
    (0x0056F330, 0x008D0FC0, 0x006C0268, b'EnemyArmy'),
    (0x0056F7D0, 0x008CFE38, 0x006C68B0, b'ChooseHeroRotator'),
    (0x0056FB20, 0x008D0EB8, 0x006C1600, b'NPCList'),
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


def _type(h, state, index):
    return _call(h, TYPE, args=(state, index))['eax']


def _getfield(h, state, index, name):
    _call(h, GETFIELD, args=(state, index, name))
    return _type(h, state, -1)


def _check_after_registration(h, state, entry, slot, ref_slot, raw_name):
    name = h.alloc(len(raw_name) + 1, raw_name + b'\0')
    new_key = h.alloc(4, b'new\0')
    delete_key = h.alloc(7, b'delete\0')
    tostring_key = h.alloc(11, b'__tostring\0')
    eq_key = h.alloc(5, b'__eq\0')
    gc_key = h.alloc(5, b'__gc\0')
    index_key = h.alloc(8, b'__index\0')

    diffs = h.compare(entry, args=(name,), ret=None)
    if diffs:
        return diffs

    _call(h, entry, args=(name,))
    if _u32(h, slot) != name:
        return ['the name slot is %08X, want %08X' % (_u32(h, slot), name)]
    if _top(h, state) != 0:
        return ['top %d after the registration, want 0' % _top(h, state)]
    if _getfield(h, state, LUA_GLOBALS, name) != LUA_TTABLE:
        return ['_G[name] is not a table']
    if _getfield(h, state, -1, new_key) != LUA_TFUNCTION:
        return ['the module has no "new"']
    _call(h, SETTOP, args=(state, -2))

    reference = _u32(h, ref_slot)
    if reference == 0:
        return ['the metatable was not referenced']
    _call(h, RAWGETI, args=(state, LUA_REGISTRY, reference))
    if _type(h, state, -1) != LUA_TTABLE:
        return ['the registry entry is not a table']
    if _getfield(h, state, -1, index_key) != LUA_TTABLE:
        return ['the metatable has no __index table']
    if _getfield(h, state, -1, delete_key) != LUA_TFUNCTION:
        return ['the methods have no "delete"']
    _call(h, SETTOP, args=(state, -2))
    _call(h, SETTOP, args=(state, -2))
    for key in (tostring_key, eq_key, gc_key):
        if _getfield(h, state, -1, key) != LUA_TFUNCTION:
            return ['the metatable lost one of __tostring/__eq/__gc']
        _call(h, SETTOP, args=(state, -2))
    _call(h, SETTOP, args=(state, 0))
    return None



def _case(index):
    entry, slot, ref_slot, raw_name = CASES[index]

    def test(h):
        state = _state(h)
        return _check_after_registration(h, state, entry, slot, ref_slot, raw_name)

    return test


for _index, _case_data in enumerate(CASES):
    globals()['test_%08X' % _case_data[0]] = _case(_index)
