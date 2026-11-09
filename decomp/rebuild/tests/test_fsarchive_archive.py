"""fs::FileSystemArchive: the number formatter, the ctor with its pak chain, the dtors and the creator
(0x576720 / 0x576DD0 / 0x576C90 / 0x576DB0 / 0x44AB70).

The ctor opens Resource.pak for its size and then reads Resource0.pak, Resource1.pak, ... until one fails.  The
stream and the Win32 file calls are imports, so the emulated ones are replaced here: the first open succeeds and
serves the pak image below, the second fails and ends the chain."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

from difftest import STACK, STACK_SIZE

INT_TO_STRING = 0x00576720
ARCHIVE_CTOR = 0x00576DD0
ARCHIVE_DTOR = 0x00576C90
ARCHIVE_DELETE = 0x00576DB0
ARCHIVE_CREATE = 0x0044AB70

VFT_ARCHIVE = 0x0061D828
VFT_ARCHIVE_SINGLETON = 0x0061D7E4

G_GAMEPATH = 0x006C88B4      # nCfg::GamePath*
G_ARCHIVE = 0x006C88D0       # the archive singleton
G_FILE_SYSTEM = 0x006C8C28   # CFileSystem::Instance()'s singleton

IFSTREAM_CTOR = '??0?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAE@XZ'
IFSTREAM_DTOR = '??_D?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ'
IFSTREAM_OPEN = '?open@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXPBDHH@Z'
ISTREAM_READ = '?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z'
IFSTREAM_CLOSE = '?close@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ'
IOS_BASE_NOT = '??7ios_base@std@@QBE_NXZ'

PAK = (b'GRES' + struct.pack('<II', 100, 1)
       + b'data\\maps\\kingdom.map'.ljust(0x80, b'\0') + struct.pack('<II', 0x1234, 0x5678))


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _put_string(h, addr, text=b''):
    """a VC8 string: allocator, inline buffer, size, capacity"""
    assert len(text) < 16
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _read_string(h, addr):
    size = _u32(h, addr + 20)
    cap = _u32(h, addr + 24)
    ptr = (addr + 4) if cap < 16 else _u32(h, addr + 4)
    return bytes(h.uc.mem_read(ptr, size))


def _zero_stack(h):
    """the original hands InitStringMap an uninitialised stack byte (never read); both runs must see the same"""
    h.uc.mem_write(STACK + STACK_SIZE - 0x8000, bytes(0x8000))


def _game_path(h):
    """a GamePath whose exePath is short enough to stay inline"""
    path = h.alloc(0x3C, bytes(0x3C))
    _put_string(h, path + 4, b'C:\\game\\')
    h.uc.mem_write(G_GAMEPATH, struct.pack('<I', path))
    return path


def _archive_object(h):
    """raw archive storage; the stream at +0x64 gets a fake vtable whose ios_base offset is zero"""
    obj = h.alloc(0x11C, bytes(0x11C))
    h.uc.mem_write(obj + 0x64, struct.pack('<I', h.alloc(8, bytes(8))))
    return obj


def _install_imports(h):
    """the pak stream and the Win32 handle calls.  The stream ctor resets the run state: h.compare runs the
    function twice with one setup."""
    state = {'opens': 0, 'pos': 0, 'files': 0, 'closes': 0}

    def ifstream_ctor():
        state['opens'] = 0
        state['pos'] = 0
        h._ret(h._ecx(), 4)

    def ifstream_dtor():
        h._ret(h._ecx(), 0)

    def ifstream_open():
        state['opens'] += 1
        state['pos'] = 0
        h._ret(None, 0xC)

    def istream_read():
        this, buf, n = h._ecx(), h._arg(0), h._arg(1)
        if state['opens'] == 1:
            chunk = PAK[state['pos']:state['pos'] + n]
            h.uc.mem_write(buf, chunk + bytes(n - len(chunk)))
            state['pos'] += n
        h._ret(this, 8)

    def ifstream_close():
        h._ret(None, 0)

    def ios_base_not():
        h._ret(1 if state['opens'] >= 2 else 0, 0)

    def create_file():
        state['files'] += 1
        h._ret(0x1234, 0x1C)

    def get_file_size():
        h._ret(0x1000, 8)

    def close_handle():
        state['closes'] += 1
        h._ret(1, 4)

    stubs = {IFSTREAM_CTOR: ifstream_ctor, IFSTREAM_DTOR: ifstream_dtor, IFSTREAM_OPEN: ifstream_open,
             ISTREAM_READ: istream_read, IFSTREAM_CLOSE: ifstream_close, IOS_BASE_NOT: ios_base_not,
             'CreateFileA': create_file, 'GetFileSize': get_file_size, 'CloseHandle': close_handle}
    saved = {}
    for name, fn in stubs.items():
        attr = 'crt_' + name.lstrip('_')
        saved[attr] = getattr(h, attr, None)
        setattr(h, attr, fn)

    def restore():
        for name, attr in [(name, 'crt_' + name.lstrip('_')) for name in stubs]:
            if saved[attr] is None:
                if hasattr(h, attr):
                    delattr(h, attr)
            else:
                setattr(h, attr, saved[attr])

    return state, restore


def test_int_to_string(h):
    """0x576720 formats the number into the shared buffer and builds the string through the caller's slot."""
    for value in (0, 42, -7, 1234567):
        out = h.alloc(0x1C, bytes(0x1C))
        diffs = h.compare(INT_TO_STRING, args=[out, value], ret='eax')
        if diffs:
            return ['%d: %s' % (value, d) for d in diffs]
        res = h.call(INT_TO_STRING, args=[out, value])
        if res['fault']:
            return ['%d: fault %s' % (value, res['fault'])]
        if res['eax'] != out:
            return ['%d: returned %08X, not the slot' % (value, res['eax'])]
        if _read_string(h, out) != str(value).encode():
            return ['%d: got %r' % (value, _read_string(h, out))]
    return None


def _ctor_setup(h):
    """everything the ctor reads from outside: cleared singletons and the stack byte"""
    _zero_stack(h)
    h.uc.mem_write(G_FILE_SYSTEM, bytes(4))
    h.uc.mem_write(G_ARCHIVE, bytes(4))


def test_archive_ctor(h):
    """0x576DD0 builds the maps and the tree, then reads Resource0.pak into the directory map."""
    obj = _archive_object(h)
    _game_path(h)
    state, restore = _install_imports(h)
    try:
        diffs = h.compare(ARCHIVE_CTOR, regs={UC_X86_REG_ECX: obj}, setup=lambda m: _ctor_setup(m), ret='eax')
        if diffs:
            return diffs
        state['opens'] = state['pos'] = state['files'] = 0
        res = h.call(ARCHIVE_CTOR, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
    finally:
        restore()
    if res['eax'] != obj:
        return ['ctor returned %08X, not this' % res['eax']]
    if _u32(h, obj) != VFT_ARCHIVE:
        return ['vtable %08X' % _u32(h, obj)]
    if _u32(h, obj + 4) != 100 or _u32(h, obj + 8) != 1:
        return ['version %d count %d' % (_u32(h, obj + 4), _u32(h, obj + 8))]
    if _u32(h, obj + 0x60) != 0x1234:
        return ['pak handle %08X' % _u32(h, obj + 0x60)]
    if state['files'] != 1:
        return ['CreateFileA calls %d' % state['files']]
    if state['opens'] != 2:
        return ['opens %d' % state['opens']]
    if _u32(h, obj + 0x44) != 1:
        return ['file map size %d' % _u32(h, obj + 0x44)]
    if _u32(h, obj + 0x1C) != 0:
        return ['index map size %d' % _u32(h, obj + 0x1C)]
    sentinel = _u32(h, obj + 0x40)
    node = _u32(h, sentinel)
    if node == sentinel:
        return ['no entry in the file map']
    if _read_string(h, node + 8) != b'data\\maps\\kingdom.map':
        return ['entry name %r' % _read_string(h, node + 8)]
    if (_u32(h, node + 0x24), _u32(h, node + 0x28), _u32(h, node + 0x2C)) != (0x1234, 0x5678, 0):
        return ['entry %08X/%08X/%d' % (_u32(h, node + 0x24), _u32(h, node + 0x28), _u32(h, node + 0x2C))]
    if _read_string(h, obj + 0xF0) != b'':
        return ['root name %r' % _read_string(h, obj + 0xF0)]
    if _u32(h, obj + 0x114) != 0:
        return ['root children %d' % _u32(h, obj + 0x114)]
    return None


def _live_archive(h, obj, state):
    state['opens'] = state['pos'] = state['files'] = 0
    res = h.call(ARCHIVE_CTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        raise RuntimeError('building the archive failed: %s' % res['fault'])


def test_archive_dtor(h):
    """0x576C90 closes the handle, destroys the tree and frees both maps."""
    obj = _archive_object(h)
    _game_path(h)
    state, restore = _install_imports(h)

    def setup(m):
        _ctor_setup(m)
        _live_archive(m, obj, state)
        state['closes'] = 0

    try:
        diffs = h.compare(ARCHIVE_DTOR, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
        if diffs:
            return diffs
        state['closes'] = 0
        res = h.call(ARCHIVE_DTOR, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
    finally:
        restore()
    if state['closes'] != 1:
        return ['CloseHandle calls %d' % state['closes']]
    if _u32(h, obj) != VFT_ARCHIVE_SINGLETON:
        return ['vtable %08X' % _u32(h, obj)]
    if _u32(h, obj + 0x60) != 0xFFFFFFFF:
        return ['pak handle %08X' % _u32(h, obj + 0x60)]
    for off in (0x24, 0x28, 0x2C):  # nameIndex begin/end/limit
        if _u32(h, obj + off) != 0:
            return ['nameIndex +%02X is %08X' % (off, _u32(h, obj + off))]
    for off in (0x4C, 0x50, 0x54):  # files begin/end/limit
        if _u32(h, obj + off) != 0:
            return ['files +%02X is %08X' % (off, _u32(h, obj + off))]
    if _u32(h, obj + 0x18) != 0 or _u32(h, obj + 0x40) != 0:
        return ['a map sentinel survived']
    return None


def test_archive_delete(h):
    """0x576DB0 deletes the archive only when its flag asks for it."""
    for flags in (0, 1):
        obj = _archive_object(h)
        _game_path(h)
        state, restore = _install_imports(h)

        def setup(m):
            _ctor_setup(m)
            _live_archive(m, obj, state)
            state['closes'] = 0

        try:
            diffs = h.compare(ARCHIVE_DELETE, args=[flags], regs={UC_X86_REG_ECX: obj}, setup=setup, ret='eax')
        finally:
            restore()
        if diffs:
            return ['flags %d: %s' % (flags, d) for d in diffs]
    return None


def test_archive_create(h):
    """0x44AB70 allocates the archive, constructs it and stores it as the singleton."""
    _game_path(h)
    state, restore = _install_imports(h)
    try:
        diffs = h.compare(ARCHIVE_CREATE, setup=lambda m: _ctor_setup(m), ret='eax')
        if diffs:
            return diffs
        state['opens'] = state['pos'] = state['files'] = 0
        res = h.call(ARCHIVE_CREATE)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
    finally:
        restore()
    obj = _u32(h, G_ARCHIVE)
    if obj == 0 or obj != res['eax']:
        return ['singleton %08X, returned %08X' % (obj, res['eax'])]
    if _u32(h, obj) != VFT_ARCHIVE:
        return ['vtable %08X' % _u32(h, obj)]
    if _u32(h, obj + 0x44) != 1:
        return ['file map size %d' % _u32(h, obj + 0x44)]
    return None
