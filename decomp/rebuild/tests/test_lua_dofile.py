"""CLuaWrapper::DoFile (0x432620): loads <name>.lua from the archive and runs it in the script machine.

The chunk loader 0x57D220 is replaced here by a stub that records its arguments (chunk buffer, length, chunk name
and the machine), so the test does not need a live lua_State.  The archive lookup and the file read are the same
ones the file entry tests use."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

DO_FILE = 0x00432620
RUN_CHUNK = 0x0057D220

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


def _archive(h, entries):
    archive = h.alloc(0x11C, bytes(0x11C))
    _file_map(h, archive + 0x38, entries, 1, 1)
    h.uc.mem_write(SINGLETON, struct.pack('<I', archive))
    return archive


def _game_path(h, exe=b'C:\\game\\'):
    path = h.alloc(0x20, bytes(0x20))
    _put_string(h, path + 4, exe)
    h.uc.mem_write(GAME_PATH, struct.pack('<I', path))


def _patch_run_chunk(h, scratch):
    """replace 0x57D220 (a thiscall with three stack arguments) with a stub that records ecx and the arguments
    at scratch+0..15, then returns; the original pops its 12 argument bytes"""
    code = b''
    for i in range(3):
        code += b'\x8b\x44\x24' + bytes([4 + 4 * i]) + b'\xa3' + struct.pack('<I', scratch + 4 * i)
    code += b'\x89\x0d' + struct.pack('<I', scratch + 12)
    code += b'\xc2\x0c\x00'     # ret 12
    h.uc.mem_write(RUN_CHUNK, code)
    return len(code)


def test_do_file(h):
    content = b'return 42\n'
    _archive(h, [(b'scripts\\test.lua', 0x1234, len(content), 2)])
    _game_path(h)
    state, restore = _install_stream_stubs(h, content=content)
    original = bytes(h.uc.mem_read(RUN_CHUNK, 0x30))
    scratch = h.alloc(0x10, bytes(0x10))
    try:
        _patch_run_chunk(h, scratch)
        vm = h.alloc(0x10, bytes(0x10))
        name = h.alloc(0x10, b'scripts\\test\0' + bytes(2))
        diffs = h.compare(DO_FILE, args=[name], regs={UC_X86_REG_ECX: vm}, ret=None)
        if diffs:
            return diffs

        state['opens'].clear()
        state['seek'].clear()
        state['reads'].clear()
        res = h.call(DO_FILE, args=[name], regs={UC_X86_REG_ECX: vm})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        buf, size, chunk_name, machine = struct.unpack('<4I', h.uc.mem_read(scratch, 0x10))
        if size != len(content):
            return ['chunk size %d, want %d' % (size, len(content))]
        if bytes(h.uc.mem_read(buf, size)) != content:
            return ['chunk %r, want %r' % (bytes(h.uc.mem_read(buf, size)), content)]
        if h._cstr(chunk_name) != b'scripts\\test':
            return ['chunk name %r, want the caller\'s name' % (h._cstr(chunk_name),)]
        if machine != vm:
            return ['ran in %08X, not the machine' % machine]
        if state['opens'] != [b'C:\\game\\Resource2.pak']:
            return ['opened %r' % (state['opens'],)]
        if state['seek'] != [0x1234]:
            return ['sought %r, want [0x1234]' % (state['seek'],)]
        if state['reads'] != [len(content)]:
            return ['read %r bytes' % (state['reads'],)]
    finally:
        h.uc.mem_write(RUN_CHUNK, original)
        restore()
    return None
