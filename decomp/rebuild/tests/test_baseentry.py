"""The base entry family: nStd::BaseEntry (0x4324E0 ctor / 0x432500 destructor) and FsBaseFileEntry
(0x432540 / 0x54F740 constructors, 0x432310 / 0x4321C0 loads, 0x4325A0 destructor, 0x4325D0 scalar deleting
destructor), plus FsFileEntry::HasName (0x432070).

The destructors walk the vptr down FsBaseFileEntry -> BaseEntry -> Object and free the whole-file buffer before
Object checks that the child is detached.  Load refuses a name the archive doesn't know (the throwing path is not
exercised: _CxxThrowException does not return) and otherwise reads the file through FsFileEntry."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

HAS_NAME = 0x00432070
LOAD_NAME = 0x00432310
LOAD_FROM = 0x004321C0
BASE_CTOR = 0x004324E0
BASE_DESTROY = 0x00432500
INIT_NAME = 0x00432540
DESTROY = 0x004325A0
RELEASE = 0x004325D0
INIT_FROM = 0x0054F740

OBJECT_VTABLE = 0x00607C88
BASE_VTABLE = 0x00609288
FILE_VTABLE = 0x006092C8

IFSTREAM_CTOR = '??0?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z'
IFSTREAM_DTOR = '??_D?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ'
ISTREAM_SEEKG_FPOS = '?seekg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@V?$fpos@H@2@@Z'
ISTREAM_SEEKG = '?seekg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@JH@Z'
ISTREAM_TELLG = '?tellg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAE?AV?$fpos@H@2@XZ'
ISTREAM_READ = '?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z'
IFSTREAM_CLOSE = '?close@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ'

GAME_PATH = 0x006C88B4   # nCfg::GamePath*, its exePath string at +4
SINGLETON = 0x006C88D0   # fs::FileSystemArchive*


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


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


def _ldiv(a, b):
    q = abs(a) // b
    if a < 0:
        q = -q
    return q, a - q * b


def _name_hash(key):
    v = 0x811c9dc5
    for b in key:
        v = (v * 0x1000193 ^ (b - 256 if b >= 128 else b)) & 0xFFFFFFFF
    if v >= 0x80000000:
        v -= 0x100000000
    quot, rem = _ldiv(v, 0x1f31d)
    h = (rem * 0x41a7 + quot * -0xb14) & 0xFFFFFFFF
    if h >= 0x80000000:
        h = (h + 0x7fffffff) & 0xFFFFFFFF
    return h


def _name_bucket(key, mask, count):
    bucket = _name_hash(key) & mask
    if count <= bucket:
        bucket = (bucket - 1 - (mask >> 1)) & 0xFFFFFFFF
    return bucket


def _file_map(h, addr, entries, mask, count):
    """map<string, PakEntry> at addr; entries are (name, offset, size, pak) and the value sits at node+24"""
    entries = sorted(entries, key=lambda e: (_name_bucket(e[0], mask, count), e[0]))
    sentinel = h.alloc(0x10, bytes(0x10))
    nodes = []
    for name, offset, size, pak in entries:
        node = h.alloc(0x30, bytes(0x30))
        _put_string(h, node + 8, name)
        h.uc.mem_write(node + 0x24, struct.pack('<III', offset, size, pak))
        nodes.append(node)
    ring = [sentinel] + nodes + [sentinel]
    for here, following in zip(ring, ring[1:]):
        h.uc.mem_write(here, struct.pack('<I', following))
    for here, previous in zip(ring[1:], ring):
        h.uc.mem_write(here + 4, struct.pack('<I', previous))
    buckets = h.alloc((count + 1) * 4, bytes((count + 1) * 4))
    for i in range(count + 1):
        first = sentinel
        for node, (name, _, _, _) in zip(nodes, entries):
            if _name_bucket(name, mask, count) >= i:
                first = node
                break
        h.uc.mem_write(buckets + 4 * i, struct.pack('<I', first))
    h.uc.mem_write(addr, struct.pack('<IIIIIIIII', 0, 0, sentinel, len(entries), 0,
                                     buckets, buckets + 4 * (count + 1), buckets + 4 * (count + 1), mask))
    h.uc.mem_write(addr + 0x24, struct.pack('<I', count))
    return sentinel, nodes


def _install_stream_stubs(h, file_size=0x2000, content=b''):
    state = {'opens': [], 'seek': [], 'reads': []}

    def ifstream_ctor():
        state['opens'].append(h._cstr(h._arg(0)))
        h._ret(h._ecx(), 0x10)

    def ifstream_dtor():
        h._ret(h._ecx(), 0)

    def seekg_fpos():
        state['seek'].append(h._arg(0))
        h._ret(h._ecx(), 0x18)

    def seekg():
        h._ret(h._ecx(), 8)

    def tellg():
        out = h._arg(0)
        h.uc.mem_write(out, struct.pack('<qi', file_size, 0))
        h._ret(out, 4)

    def read():
        buf, n = h._arg(0), h._arg(1)
        state['reads'].append(n)
        h.uc.mem_write(buf, content[:n])
        h._ret(h._ecx(), 8)

    def close():
        h._ret(h._ecx(), 0)

    def char_lower():
        p = h._arg(0)
        h.uc.mem_write(p, h._cstr(p).lower() + b'\0')
        h._ret(p, 4)

    stubs = {IFSTREAM_CTOR: ifstream_ctor, IFSTREAM_DTOR: ifstream_dtor,
             ISTREAM_SEEKG_FPOS: seekg_fpos, ISTREAM_SEEKG: seekg,
             ISTREAM_TELLG: tellg, ISTREAM_READ: read, IFSTREAM_CLOSE: close,
             'CharLowerA': char_lower}
    saved = {}
    for name, fn in stubs.items():
        attr = 'crt_' + name.lstrip('_')
        saved[attr] = getattr(h, attr, None)
        setattr(h, attr, fn)

    def restore():
        for attr, old in saved.items():
            if old is None:
                if hasattr(h, attr):
                    delattr(h, attr)
            else:
                setattr(h, attr, old)

    return state, restore


def _fs_entry(h, name=b'', size=0, offset=0, pak=0):
    entry = h.alloc(0x28, bytes(0x28))
    _put_string(h, entry + 8, name)
    h.uc.mem_write(entry, struct.pack('<II', size, offset))
    h.uc.mem_write(entry + 0x24, struct.pack('<i', pak))
    return entry


def _archive(h, entries):
    archive = h.alloc(0x11C, bytes(0x11C))
    _file_map(h, archive + 0x38, entries, 1, 1)
    h.uc.mem_write(SINGLETON, struct.pack('<I', archive))
    return archive


def _game_path(h, exe=b'C:\\game\\'):
    path = h.alloc(0x20, bytes(0x20))
    _put_string(h, path + 4, exe)
    h.uc.mem_write(GAME_PATH, struct.pack('<I', path))


def _base_entry(h, vtable=FILE_VTABLE, data=0):
    entry = h.alloc(0x18, b'\xA5' * 0x18)
    h.uc.mem_write(entry, struct.pack('<III', vtable, 0, data))
    return entry


def test_has_name(h):
    for name, want in ((b'data\\maps\\kingdom.map', 1), (b'', 0)):
        entry = _fs_entry(h, name)
        diffs = h.compare(HAS_NAME, regs={UC_X86_REG_ECX: entry}, ret='eax')
        if diffs:
            return ['%r: %s' % (name, d) for d in diffs]
        res = h.call(HAS_NAME, regs={UC_X86_REG_ECX: entry})
        if res['fault']:
            return ['%r: replacement faulted: %s' % (name, res['fault'])]
        if res['eax'] != want:
            return ['%r: returned %d, want %d' % (name, res['eax'], want)]
    return None


def test_base_entry_ctor(h):
    entry = h.alloc(0x18, b'\xA5' * 0x18)
    diffs = h.compare(BASE_CTOR, regs={UC_X86_REG_ECX: entry}, ret='eax')
    if diffs:
        return diffs
    res = h.call(BASE_CTOR, regs={UC_X86_REG_ECX: entry})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != entry:
        return ['returned %08X, not the object' % res['eax']]
    got = struct.unpack('<6I', h.uc.mem_read(entry, 0x18))
    if got != (BASE_VTABLE, 0, 0, 0, 0xA5A5A5A5, 0):
        return ['fields %r, want vtable/child/data/begin/end/size' % (got,)]
    return None


def test_base_entry_destroy(h):
    entry = _base_entry(h, vtable=BASE_VTABLE)
    diffs = h.compare(BASE_DESTROY, regs={UC_X86_REG_ECX: entry}, ret=None)
    if diffs:
        return diffs
    res = h.call(BASE_DESTROY, regs={UC_X86_REG_ECX: entry})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, entry) != OBJECT_VTABLE:
        return ['vtable %08X, want %08X' % (_u32(h, entry), OBJECT_VTABLE)]
    if _u32(h, entry + 4) != 0:
        return ['child %08X, want 0' % _u32(h, entry + 4)]
    return None


def test_file_entry_load(h):
    content = bytes(range(0x10))
    _archive(h, [(b'data\\maps\\kingdom.map', 0x1234, 0x10, 3)])
    _game_path(h)
    state, restore = _install_stream_stubs(h, content=content)
    try:
        name = h.alloc(28, bytes(28))
        _put_string(h, name, b'data\\maps\\kingdom.map')
        entry = _base_entry(h)
        diffs = h.compare(LOAD_NAME, args=[name], regs={UC_X86_REG_ECX: entry}, ret=None)
        if diffs:
            return diffs
        state['opens'].clear()
        state['seek'].clear()
        state['reads'].clear()
        res = h.call(LOAD_NAME, args=[name], regs={UC_X86_REG_ECX: entry})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        data, begin, end, size = struct.unpack('<4I', h.uc.mem_read(entry + 8, 0x10))
        if not (data == begin and size == 0x10 and end == data + 0x10):
            return ['data %08X begin %08X end %08X size %d' % (data, begin, end, size)]
        got = bytes(h.uc.mem_read(data, 0x11))
        if got != content + b'\0':
            return ['buffer %r, want %r plus a zero' % (got, content)]
        if state['opens'] != [b'C:\\game\\Resource3.pak']:
            return ['opened %r' % (state['opens'],)]
        if state['seek'] != [0x1234]:
            return ['sought %r, want [0x1234]' % (state['seek'],)]
        if state['reads'] != [0x10]:
            return ['read %r bytes' % (state['reads'],)]
    finally:
        restore()
    return None


def test_file_entry_load_from(h):
    content = bytes(range(0x10))
    _archive(h, [(b'data\\maps\\kingdom.map', 0x1234, 0x10, 3)])
    _game_path(h)
    state, restore = _install_stream_stubs(h, content=content)
    try:
        source = _fs_entry(h, b'data\\maps\\kingdom.map', size=0x10, offset=0x1234, pak=3)
        entry = _base_entry(h)
        diffs = h.compare(LOAD_FROM, args=[source], regs={UC_X86_REG_ECX: entry}, ret='eax')
        if diffs:
            return diffs
        state['opens'].clear()
        res = h.call(LOAD_FROM, args=[source], regs={UC_X86_REG_ECX: entry})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        data, begin, end, size = struct.unpack('<4I', h.uc.mem_read(entry + 8, 0x10))
        if res['eax'] != data:
            return ['returned %08X, buffer at %08X' % (res['eax'], data)]
        if not (data == begin and size == 0x10 and end == data + 0x10):
            return ['data %08X begin %08X end %08X size %d' % (data, begin, end, size)]
        if bytes(h.uc.mem_read(data, 0x11)) != content + b'\0':
            return ['buffer %r' % (bytes(h.uc.mem_read(data, 0x11)),)]
        if state['opens'] != [b'C:\\game\\Resource3.pak']:
            return ['opened %r' % (state['opens'],)]
    finally:
        restore()
    return None


def test_file_entry_ctor(h):
    content = bytes(range(0x10))
    _archive(h, [(b'data\\maps\\kingdom.map', 0x1234, 0x10, 3)])
    _game_path(h)
    state, restore = _install_stream_stubs(h, content=content)
    try:
        name = h.alloc(28, bytes(28))
        _put_string(h, name, b'data\\maps\\kingdom.map')
        entry = h.alloc(0x18, b'\xA5' * 0x18)
        diffs = h.compare(INIT_NAME, args=[name], regs={UC_X86_REG_ECX: entry}, ret='eax')
        if diffs:
            return ['name: %s' % d for d in diffs]
        res = h.call(INIT_NAME, args=[name], regs={UC_X86_REG_ECX: entry})
        if res['fault']:
            return ['name: replacement faulted: %s' % res['fault']]
        if res['eax'] != entry:
            return ['name: returned %08X, not the object' % res['eax']]
        got = struct.unpack('<6I', h.uc.mem_read(entry, 0x18))
        if got[0] != FILE_VTABLE or got[1] != 0 or got[5] != 0x10:
            return ['name: vtable/child/data/begin/end/size %r' % (got,)]
        if not (got[2] == got[3] and got[4] == got[2] + 0x10):
            return ['name: buffer %r' % (got,)]
        if bytes(h.uc.mem_read(got[2], 0x11)) != content + b'\0':
            return ['name: buffer contents %r' % (bytes(h.uc.mem_read(got[2], 0x11)),)]

        source = _fs_entry(h, b'data\\maps\\kingdom.map', size=0x10, offset=0x1234, pak=3)
        entry2 = h.alloc(0x18, b'\xA5' * 0x18)
        diffs = h.compare(INIT_FROM, args=[source], regs={UC_X86_REG_ECX: entry2}, ret='eax')
        if diffs:
            return ['from-entry: %s' % d for d in diffs]
        res = h.call(INIT_FROM, args=[source], regs={UC_X86_REG_ECX: entry2})
        if res['fault']:
            return ['from-entry: replacement faulted: %s' % res['fault']]
        if res['eax'] != entry2:
            return ['from-entry: returned %08X, not the object' % res['eax']]
        got = struct.unpack('<6I', h.uc.mem_read(entry2, 0x18))
        if got[0] != FILE_VTABLE or got[1] != 0 or got[5] != 0x10:
            return ['from-entry: vtable/child/data/begin/end/size %r' % (got,)]
        if not (got[2] == got[3] and got[4] == got[2] + 0x10):
            return ['from-entry: buffer %r' % (got,)]
        if bytes(h.uc.mem_read(got[2], 0x11)) != content + b'\0':
            return ['from-entry: buffer contents %r' % (bytes(h.uc.mem_read(got[2], 0x11)),)]
    finally:
        restore()
    return None


def test_file_entry_destroy(h):
    entry = _base_entry(h, data=h.alloc(0x10, bytes(0x10)))
    diffs = h.compare(DESTROY, regs={UC_X86_REG_ECX: entry}, ret=None)
    if diffs:
        return ['destroy: %s' % d for d in diffs]
    res = h.call(DESTROY, regs={UC_X86_REG_ECX: entry})
    if res['fault']:
        return ['destroy: replacement faulted: %s' % res['fault']]
    if _u32(h, entry) != OBJECT_VTABLE or _u32(h, entry + 8) != 0:
        return ['destroy: vtable %08X data %08X' % (_u32(h, entry), _u32(h, entry + 8))]

    for flags in (0, 1):
        entry = _base_entry(h, data=h.alloc(0x10, bytes(0x10)))
        diffs = h.compare(RELEASE, args=[flags], regs={UC_X86_REG_ECX: entry}, ret='eax')
        if diffs:
            return ['release %d: %s' % (flags, d) for d in diffs]
        res = h.call(RELEASE, args=[flags], regs={UC_X86_REG_ECX: entry})
        if res['fault']:
            return ['release %d: replacement faulted: %s' % (flags, res['fault'])]
        if res['eax'] != entry:
            return ['release %d: returned %08X, not the object' % (flags, res['eax'])]
        if _u32(h, entry) != OBJECT_VTABLE or _u32(h, entry + 8) != 0:
            return ['release %d: vtable %08X data %08X' % (flags, _u32(h, entry), _u32(h, entry + 8))]
    return None
