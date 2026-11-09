"""fs::FileSystemArchive's name locator (0x576A90).

A name with a drive letter is a path on disk: the file is opened only to measure it by seeking to the end.  Any
other name is lowercased and looked up in the archive's pak directory map; a miss yields a zero location."""
import struct

from difftest import STACK, STACK_SIZE
from unicorn.x86_const import UC_X86_REG_ECX

LOCATE = 0x00576A90

IFSTREAM_CTOR = '??0?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z'
IFSTREAM_DTOR = '??_D?$basic_ifstream@DU?$char_traits@D@std@@@std@@QAEXXZ'
ISTREAM_SEEKG = '?seekg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV12@JH@Z'
ISTREAM_TELLG = '?tellg@?$basic_istream@DU?$char_traits@D@std@@@std@@QAE?AV?$fpos@H@2@XZ'


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
    """FNV-1a over the bytes (char is signed, as in the original), then the same prime mixing as the int hash"""
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


def _install_imports(h):
    state = {'opens': 0, 'size': 0x2000}

    def ifstream_ctor():
        state['opens'] += 1
        h._ret(h._ecx(), 0x10)

    def ifstream_dtor():
        h._ret(h._ecx(), 0)

    def seekg():
        h._ret(h._ecx(), 8)

    def tellg():
        out = h._arg(0)
        h.uc.mem_write(out, struct.pack('<qi', state['size'], 0))
        h._ret(out, 4)

    def char_lower():
        p = h._arg(0)
        h.uc.mem_write(p, h._cstr(p).lower() + b'\0')
        h._ret(p, 4)

    stubs = {IFSTREAM_CTOR: ifstream_ctor, IFSTREAM_DTOR: ifstream_dtor, ISTREAM_SEEKG: seekg,
             ISTREAM_TELLG: tellg, 'CharLowerA': char_lower}
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


def test_locate_archive_file(h):
    archive = h.alloc(0x11C, bytes(0x11C))
    _file_map(h, archive + 0x38, [(b'data\\maps\\kingdom.map', 0x1234, 0x5678, 3)], 1, 1)
    state, restore = _install_imports(h)
    cases = [
        (b'data\\maps\\kingdom.map', (0x1234, 0x5678, 3)),
        (b'DATA\\MAPS\\Kingdom.Map', (0x1234, 0x5678, 3)),
        (b'data\\maps\\other.map', (0, 0, 0)),
        (b'C:\\game\\data.bin', (0, 0x2000, 0)),
    ]
    try:
        for name, want in cases:
            nameobj = h.alloc(28, bytes(28))
            _put_string(h, nameobj, name)
            out = h.alloc(0x0C, bytes(0x0C))
            args = [out, nameobj]
            diffs = h.compare(LOCATE, args=args, regs={UC_X86_REG_ECX: archive}, ret='eax')
            if diffs:
                return ['%r: %s' % (name, d) for d in diffs]
            state['opens'] = 0
            res = h.call(LOCATE, args=args, regs={UC_X86_REG_ECX: archive})
            if res['fault']:
                return ['%r: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != out:
                return ['%r: returned %08X, not the slot' % (name, res['eax'])]
            got = (_u32(h, out), _u32(h, out + 4), _u32(h, out + 8))
            if got != want:
                return ['%r: %08X/%08X/%d, want %08X/%08X/%d' % ((name,) + got + want)]
            on_disk = b':' in name
            if state['opens'] != (1 if on_disk else 0):
                return ['%r: %d stream opens' % (name, state['opens'])]
    finally:
        restore()
    return None
