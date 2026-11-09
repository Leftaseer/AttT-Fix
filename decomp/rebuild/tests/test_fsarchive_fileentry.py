"""The archive's file entry (0x432200 / 0x432010 / 0x576820).

The ctor caches the archive singleton in 0x8D10A4 and fills the entry from the archive's file map (a miss clears
the name); Read loads the whole file from the ResourceN.pak the entry points into, or straight from disk when the
name carries a drive, and terminates the buffer with a zero."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x00432200
LOCATE = 0x00432010
READ = 0x00576820

IFSTREAM_CTOR = '??0?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z'
IFSTREAM_DTOR = '??_D?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ'
ISTREAM_SEEKG_FPOS = '?seekg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@V?$fpos@H@2@@Z'
ISTREAM_SEEKG = '?seekg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@JH@Z'
ISTREAM_TELLG = '?tellg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAE?AV?$fpos@H@2@XZ'
ISTREAM_READ = '?read@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@PADH@Z'
IFSTREAM_CLOSE = '?close@?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ'

GAME_PATH = 0x006C88B4   # nCfg::GamePath*, its exePath string at +4
SINGLETON = 0x006C88D0   # fs::FileSystemArchive*
CACHED = 0x008D10A4      # the archive pointer FsFileEntry consults


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


def _entry(h, name=b'', size=0, offset=0, pak=0):
    entry = h.alloc(0x28, bytes(0x28))
    _put_string(h, entry + 8, name)
    h.uc.mem_write(entry, struct.pack('<II', size, offset))
    h.uc.mem_write(entry + 0x24, struct.pack('<i', pak))
    return entry


def _archive(h, entries):
    archive = h.alloc(0x11C, bytes(0x11C))
    _file_map(h, archive + 0x38, entries, 1, 1)
    return archive


def _point_at(h, archive):
    def setup(_h):
        h.uc.mem_write(SINGLETON, struct.pack('<I', archive))
        h.uc.mem_write(CACHED, struct.pack('<I', 0xDEADBEEF))
    return setup


def test_entry_ctor(h):
    archive = _archive(h, [(b'data\\maps\\kingdom.map', 0x1234, 0x5678, 3)])
    state, restore = _install_stream_stubs(h)
    try:
        for name, want, want_name in ((b'data\\maps\\kingdom.map', (0x5678, 0x1234, 3), b'data\\maps\\kingdom.map'),
                                      (b'no\\such.file', (0, 0, 0), b'')):
            nameobj = h.alloc(28, bytes(28))
            _put_string(h, nameobj, name)
            entry = h.alloc(0x28, bytes(0x28))
            diffs = h.compare(CTOR, args=[nameobj], regs={UC_X86_REG_ECX: entry},
                              setup=_point_at(h, archive), ret='eax')
            if diffs:
                return ['%r: %s' % (name, d) for d in diffs]
            res = h.call(CTOR, args=[nameobj], regs={UC_X86_REG_ECX: entry})
            if res['fault']:
                return ['%r: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != entry:
                return ['%r: returned %08X, not the object' % (name, res['eax'])]
            got = (_u32(h, entry), _u32(h, entry + 4), _u32(h, entry + 0x24))
            if got != want:
                return ['%r: %08X/%08X/%d, want %08X/%08X/%d' % ((name,) + got + want)]
            got_name = h._str_get(entry + 8)
            if got_name != want_name:
                return ['%r: name %r, want %r' % (name, got_name, want_name)]
            if _u32(h, CACHED) != archive:
                return ['0x8D10A4 holds %08X, not the archive' % _u32(h, CACHED)]
    finally:
        restore()
    return None


def test_entry_locate_disk(h):
    state, restore = _install_stream_stubs(h, file_size=0x2000)
    try:
        name = b'C:\\game\\data.bin'
        nameobj = h.alloc(28, bytes(28))
        _put_string(h, nameobj, name)
        entry = h.alloc(0x28, bytes(0x28))
        diffs = h.compare(LOCATE, args=[nameobj], regs={UC_X86_REG_ECX: entry}, ret=None)
        if diffs:
            return diffs
        res = h.call(LOCATE, args=[nameobj], regs={UC_X86_REG_ECX: entry})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        got = (_u32(h, entry), _u32(h, entry + 4), _u32(h, entry + 0x24))
        if got != (0x2000, 0, 0):
            return ['got %08X/%08X/%d, want %08X/0/0' % (got + (0x2000,))]
        if h._str_get(entry + 8) != name:
            return ['name %r, want %r' % (h._str_get(entry + 8), name)]
    finally:
        restore()
    return None


def test_entry_read(h):
    content = bytes(range(0x10))
    state, restore = _install_stream_stubs(h, content=content)
    try:
        exe = h.alloc(0x20, bytes(0x20))
        _put_string(h, exe + 4, b'C:\\game\\')
        h.uc.mem_write(GAME_PATH, struct.pack('<I', exe))

        cases = [(b'data\\maps\\kingdom.map', 3, 0x1234, b'C:\\game\\Resource3.pak'),
                 (b'C:\\game\\data.bin', 0, 0, b'C:\\game\\data.bin')]
        for name, pak, offset, want_path in cases:
            entry = _entry(h, name, size=0x10, offset=offset, pak=pak)
            diffs = h.compare(READ, args=[], regs={UC_X86_REG_ECX: entry}, ret='eax')
            if diffs:
                return ['%r: %s' % (name, d) for d in diffs]
            state['opens'].clear()
            state['seek'].clear()
            state['reads'].clear()
            res = h.call(READ, args=[], regs={UC_X86_REG_ECX: entry})
            if res['fault']:
                return ['%r: replacement faulted: %s' % (name, res['fault'])]
            data = res['eax']
            if data < 0x10000:
                return ['%r: returned %08X, not a buffer' % (name, data)]
            got = bytes(h.uc.mem_read(data, 0x11))
            if got != content + b'\0':
                return ['%r: buffer %r, want %r plus a zero' % (name, got, content)]
            if state['opens'] != [want_path]:
                return ['%r: opened %r, want %r' % (name, state['opens'], want_path)]
            if state['seek'] != [offset]:
                return ['%r: sought %r, want %r' % (name, state['seek'], [offset])]
            if state['reads'] != [0x10]:
                return ['%r: read %r bytes' % (name, state['reads'])]
    finally:
        restore()
    return None
