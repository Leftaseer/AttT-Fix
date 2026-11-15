"""LuaGlobal_FindSaveFiles (0x57EDE0): <data root>/Saves/game*.sav is enumerated through the Win32 find API; a save
whose <stem>.bmp screenshot exists becomes a {stem, write time} vector entry, the entries are sorted newest first and
their stems are pushed as a 1-based table.  A true top-of-stack value asks for the newest saves only: the automatic
slots game0/game00 are dropped and an empty name heads the table, so the entries start at slot 2.  The directory
functions and PathFileExistsA are stubbed here; the check runs both bodies and then reads the returned table back
through the Lua API."""
import struct

CONFIG_SLOT = 0x006C884C
LUA_STATE_SLOT = 0x008D122C
NEWSTATE = 0x00402870
GETTOP = 0x00402A60
SETTOP = 0x00402A70
PUSHBOOLEAN = 0x00403280
RAWGETI = 0x00403390
TYPE = 0x00402C20
TOLSTRING = 0x00402ED0
FIND_SAVE_FILES = 0x0057EDE0

LUA_TNIL = 0
LUA_TSTRING = 4
LUA_TTABLE = 5

ROOT = b'C:\\game\\'
FOLDER = ROOT + b'Saves/'
PATTERN = FOLDER + b'game*.sav'
HANDLE = 0x1234

FILES = [(b'game3.sav', 300, 0), (b'game0.sav', 100, 0),
         (b'game10.sav', 200, 0), (b'game00.sav', 50, 0)]
EXISTING = set(FOLDER + stem + b'.bmp' for stem in (b'game3', b'game0', b'game00'))


def _call(h, entry, args=()):
    res = h.call(entry, args=args)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _put_string(h, addr, text=b''):
    """a VC8 string: allocator, inline buffer or heap pointer, size, capacity"""
    h.uc.mem_write(addr, bytes(4))
    if len(text) < 16:
        h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))
    else:
        buffer = h.alloc(len(text) + 1, text + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', buffer))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(text), len(text)))


def _install_find_stubs(h, files, log):
    state = {'next': 0}

    def fill(fd, element):
        name, low, high = element
        h.uc.mem_write(fd, bytes(0x140))
        h.uc.mem_write(fd + 0x14, struct.pack('<II', low, high))       # FILETIME last write
        h.uc.mem_write(fd + 0x2C, name + b'\0')

    def find_first():
        log['first'].append(h._cstr(h._arg(0)))
        if not files:
            h._ret(0xFFFFFFFF, 8)
            return
        state['next'] = 0
        fill(h._arg(1), files[0])
        h._ret(HANDLE, 8)

    def find_next():
        state['next'] += 1
        if state['next'] >= len(files):
            h._ret(0, 8)
            return
        fill(h._arg(1), files[state['next']])
        h._ret(1, 8)

    def find_close():
        log['close'].append(h._arg(0))
        h._ret(1, 4)

    def path_exists():
        path = h._cstr(h._arg(0))
        log['exists'].append(path)
        h._ret(1 if path in EXISTING else 0, 4)

    saved = {}
    for attr, fn in (('crt_FindFirstFileA', find_first), ('crt_FindNextFileA', find_next),
                     ('crt_FindClose', find_close), ('crt_PathFileExistsA', path_exists)):
        saved[attr] = getattr(h, attr, None)
        setattr(h, attr, fn)

    def restore():
        for attr, old in saved.items():
            if old is None:
                delattr(h, attr)
            else:
                setattr(h, attr, old)

    return restore


def _state(h):
    state = _call(h, NEWSTATE)['eax']
    h.uc.mem_write(LUA_STATE_SLOT, struct.pack('<I', state))
    return state


def _table_entry(h, state, index):
    """table at the top of the stack: its element `index` as bytes, None for nil or ('type', n) otherwise"""
    _call(h, RAWGETI, (state, -1, index))
    kind = _call(h, TYPE, (state, -1))['eax']
    if kind == LUA_TNIL:
        _call(h, SETTOP, (state, -2))
        return None
    if kind != LUA_TSTRING:
        _call(h, SETTOP, (state, -2))
        return ('type', kind)
    value = h._cstr(_call(h, TOLSTRING, (state, -1, 0))['eax'])
    _call(h, SETTOP, (state, -2))
    return value


def _run(h, state, files, saves_only):
    log = {'first': [], 'exists': [], 'close': []}
    restore = _install_find_stubs(h, files, log)
    try:
        _call(h, SETTOP, (state, 0))
        _call(h, PUSHBOOLEAN, (state, saves_only))
        diffs = h.compare(FIND_SAVE_FILES, args=[state])
        if diffs:
            return ['[%d files, flag %d] %s' % (len(files), saves_only, d) for d in diffs], None
        for entries in log.values():
            entries.clear()

        _call(h, SETTOP, (state, 0))
        _call(h, PUSHBOOLEAN, (state, saves_only))
        res = _call(h, FIND_SAVE_FILES, (state,))
        return None, (log, res)
    finally:
        restore()


def test_find_save_files(h):
    config = h.alloc(0x60, bytes(0x60))
    _put_string(h, config + 0x20, ROOT)
    h.uc.mem_write(CONFIG_SLOT, struct.pack('<I', config))
    state = _state(h)

    for files, saves_only, want in (
        (FILES, 0, [b'game3', b'game0', b'game00']),
        (FILES, 1, [b'', b'game3']),
        ([], 0, []),
        ([], 1, [b'']),
    ):
        tag = '[%d files, flag %d]' % (len(files), saves_only)
        diffs, out = _run(h, state, files, saves_only)
        if diffs:
            return diffs
        log, res = out
        if res['eax'] != 1:
            return ['%s returned %d, want 1' % (tag, res['eax'])]
        top = _call(h, GETTOP, (state,))['eax']
        if top != 2:
            return ['%s left %d values on the stack, want the argument and the table' % (tag, top)]
        if _call(h, TYPE, (state, -1))['eax'] != LUA_TTABLE:
            return ['%s pushed a non-table' % tag]
        if log['first'] != [PATTERN]:
            return ['%s enumerated %r' % (tag, log['first'])]

        checked = []
        for name, _, _ in files:
            stem = name.rsplit(b'.', 1)[0]
            if saves_only and stem in (b'game0', b'game00'):
                continue
            checked.append(FOLDER + stem + b'.bmp')
        if log['exists'] != checked:
            return ['%s asked about %r, want %r' % (tag, log['exists'], checked)]
        if log['close'] != ([HANDLE] if files else []):
            return ['%s closed %r' % (tag, log['close'])]

        for index, name in enumerate(want, 1):
            got = _table_entry(h, state, index)
            if got != name:
                return ['%s entry %d is %r, want %r' % (tag, index, got, name)]
        got = _table_entry(h, state, len(want) + 1)
        if got is not None:
            return ['%s has a %r entry after %d' % (tag, got, len(want))]
    _call(h, SETTOP, (state, 0))
    return None
