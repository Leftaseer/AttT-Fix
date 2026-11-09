"""FsHashMap's bucket hash (0x450D20), its int-keyed lookup (0x450DA0), its string-keyed lookup (0x450E60)
and CFileSystem's name-prefix resolver (0x451220).

The map's bucket vector at +14 holds one node pointer per bucket plus the list end: the nodes of bucket i run
from buckets[i] to buckets[i+1] through next.  The int map's nodes are {next; prev; key; value}, the string
map's are {next; prev; std::string key; value} with the value at +24.  A lookup returns the sentinel at +08
when the key is not in its bucket."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

STRING_HASH = 0x00579BB0


def _put_string(h, addr, text=b''):
    """a VC8 string: allocator, inline buffer, size, capacity"""
    assert len(text) < 16
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _string_hash(h, key):
    tmp = h.alloc(28, bytes(28))
    _put_string(h, tmp, key)
    return h.call(STRING_HASH, args=[tmp])['eax']


def _bucket_of_string(h, key, mask, count):
    bucket = _string_hash(h, key) & mask
    if count <= bucket:
        bucket = (bucket - 1 - (mask >> 1)) & 0xFFFFFFFF
    return bucket


def _make_string_map(h, entries, mask, count):
    """entries: (key bytes, value payload); keys ascending (case-insensitively) inside a bucket."""
    entries = sorted(entries, key=lambda e: (_bucket_of_string(h, e[0], mask, count), e[0].lower()))
    mapobj = h.alloc(0x28, bytes(0x28))
    sentinel = h.alloc(0x10, bytes(0x10))
    nodes = {}
    for key, payload in entries:
        node = h.alloc(0x28, bytes(0x28))
        _put_string(h, node + 8, key)
        h.uc.mem_write(node + 0x24, struct.pack('<I', payload))
        nodes[key] = node
    ordered = [nodes[key] for key, _ in entries]
    for here, following in zip(ordered, ordered[1:] + [sentinel]):
        h.uc.mem_write(here, struct.pack('<I', following))

    buckets = h.alloc((count + 1) * 4, b'\0' * ((count + 1) * 4))
    for i in range(count + 1):
        first = sentinel
        for node, (key, _) in zip(ordered, entries):
            if _bucket_of_string(h, key, mask, count) >= i:
                first = node
                break
        h.uc.mem_write(buckets + 4 * i, struct.pack('<I', first))

    h.uc.mem_write(mapobj, struct.pack('<IIIIIIIII', 0, 0, sentinel, len(entries), 0,
                                       buckets, buckets + 4 * (count + 1), buckets + 4 * (count + 1), mask))
    h.uc.mem_write(mapobj + 0x24, struct.pack('<I', count))
    return mapobj, sentinel, nodes


def _ldiv(a, b):
    q = abs(a) // b
    if a < 0:
        q = -q
    return q, a - q * b


def _bucket_of(key, mask, count):
    v = (key ^ 0xdeadbeef) & 0xFFFFFFFF
    if v >= 0x80000000:
        v -= 0x100000000
    quot, rem = _ldiv(v, 0x1f31d)
    bucket = (rem * 0x41a7 + quot * -0xb14) & 0xFFFFFFFF
    if bucket >= 0x80000000:
        bucket = (bucket + 0x7fffffff) & 0xFFFFFFFF
    bucket &= mask
    if count <= bucket:
        bucket = (bucket - 1 - (mask >> 1)) & 0xFFFFFFFF
    return bucket


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _make_map(h, entries, mask, count):
    """entries: (key, payload); the node list is grouped by bucket, keys ascending inside a bucket, as the
    map keeps it.  Returns (map, sentinel, {key: node})."""
    entries = sorted(entries, key=lambda e: (_bucket_of(e[0] & 0xFFFFFFFF, mask, count), e[0]))
    mapobj = h.alloc(0x28, bytes(0x28))
    sentinel = h.alloc(0x10, bytes(0x10))
    nodes = {}
    for key, payload in entries:
        nodes[key] = h.alloc(0x10, struct.pack('<IIII', 0, 0, key, payload))
    ordered = [nodes[key] for key, _ in entries]
    for here, following in zip(ordered, ordered[1:] + [sentinel]):
        h.uc.mem_write(here, struct.pack('<I', following))

    buckets = h.alloc((count + 1) * 4, b'\0' * ((count + 1) * 4))
    for i in range(count + 1):
        first = sentinel
        for node, (key, _) in zip(ordered, entries):
            if _bucket_of(key & 0xFFFFFFFF, mask, count) >= i:
                first = node
                break
        h.uc.mem_write(buckets + 4 * i, struct.pack('<I', first))

    h.uc.mem_write(mapobj, struct.pack('<IIIIIIIII', 0, 0, sentinel, len(entries), 0,
                                       buckets, buckets + 4 * (count + 1), buckets + 4 * (count + 1), mask))
    h.uc.mem_write(mapobj + 0x24, struct.pack('<I', count))
    return mapobj, sentinel, nodes


def test_bucket_index(h):
    for mask, count in ((1, 1), (7, 8), (0xF, 16)):
        mapobj = h.alloc(0x28, bytes(0x28))
        h.uc.mem_write(mapobj + 0x20, struct.pack('<II', mask, count))
        for key in (0, 1, 3, 0xD, 0x2C, 0x101, 0xBEEF, 0x7FFFFFFF, 0xFFFFFFFF):
            key_ptr = h.alloc(4, struct.pack('<I', key))
            diffs = h.compare(0x00450D20, args=[key_ptr], regs={UC_X86_REG_ECX: mapobj}, ret='eax')
            if diffs:
                return diffs
            res = h.call(0x00450D20, args=[key_ptr], regs={UC_X86_REG_ECX: mapobj})
            want = _bucket_of(key, mask, count)
            if res['eax'] != want:
                return ['key %08X with mask %X count %d: bucket %08X, want %08X'
                        % (key, mask, count, res['eax'], want)]
    return None


def test_find_int(h):
    mask, count = 7, 8
    keys = [3, 9, 17, 0x40, 0x101]
    mapobj, sentinel, nodes = _make_map(h, [(k, 0xA0 + k) for k in keys], mask, count)
    cases = [(k, nodes[k]) for k in keys]
    cases += [(0, sentinel), (4, sentinel), (0x41, sentinel), (0x100, sentinel), (0x10000, sentinel)]
    for key, want in cases:
        out = h.alloc(4, b'\0' * 4)
        key_ptr = h.alloc(4, struct.pack('<i', key))
        diffs = h.compare(0x00450DA0, args=[out, key_ptr], regs={UC_X86_REG_ECX: mapobj}, ret=None)
        if diffs:
            return diffs
        res = h.call(0x00450DA0, args=[out, key_ptr], regs={UC_X86_REG_ECX: mapobj})
        if res['fault']:
            return ['key %d: replacement faulted: %s' % (key, res['fault'])]
        got = _u32(h, out)
        if got != want:
            return ['key %d: node %08X, want %08X' % (key, got, want)]
    return None


def test_find_string(h):
    mask, count = 7, 8
    keys = [b'alpha', b'Beta', b'gamma', b'Delta', b'omega']
    mapobj, sentinel, nodes = _make_string_map(h, [(k, 0xB0 + i) for i, k in enumerate(keys)], mask, count)
    cases = [(k, nodes[k]) for k in keys]
    cases += [(b'ALPHA', nodes[b'alpha']), (b'bETA', nodes[b'Beta'])]
    cases += [(b'', sentinel), (b'zeta', sentinel), (b'alph', sentinel)]
    for key, want in cases:
        out = h.alloc(4, b'\0' * 4)
        keyptr = h.alloc(28, bytes(28))
        _put_string(h, keyptr, key)
        diffs = h.compare(0x00450E60, args=[out, keyptr], regs={UC_X86_REG_ECX: mapobj}, ret=None)
        if diffs:
            return diffs
        res = h.call(0x00450E60, args=[out, keyptr], regs={UC_X86_REG_ECX: mapobj})
        if res['fault']:
            return ['key %r: replacement faulted: %s' % (key, res['fault'])]
        got = _u32(h, out)
        if got != want:
            return ['key %r: node %08X, want %08X' % (key, got, want)]
    return None


def test_resolve_path(h):
    """CFileSystem+0xB4 points at the archive's prefix map; a mapped name yields directory + name."""
    mask, count = 3, 4
    directory = h.alloc(28, bytes(28))
    _put_string(h, directory, b'data\\')
    mapobj, sentinel, nodes = _make_string_map(h, [(b'tex', directory), (b'cfg', directory)], mask, count)
    fs = h.alloc(0xB8, bytes(0xB8))
    h.uc.mem_write(fs + 0xB4, struct.pack('<I', mapobj))

    for name, ok in ((b'tex', True), (b'TEX', True), (b'cfg', True), (b'other', False)):
        nameobj = h.alloc(28, bytes(28))
        _put_string(h, nameobj, name)
        path = h.alloc(28, bytes(28))
        _put_string(h, path)
        args = [nameobj, path]
        diffs = h.compare(0x00451220, args=args, regs={UC_X86_REG_ECX: fs}, ret='al')
        if diffs:
            return diffs
        res = h.call(0x00451220, args=args, regs={UC_X86_REG_ECX: fs})
        if res['fault']:
            return ['name %r: replacement faulted: %s' % (name, res['fault'])]
        if (res['eax'] & 0xFF) != int(ok):
            return ['name %r: returned %d' % (name, res['eax'] & 0xFF)]
        if ok:
            size = struct.unpack('<I', h.uc.mem_read(path + 20, 4))[0]
            cap = struct.unpack('<I', h.uc.mem_read(path + 24, 4))[0]
            ptr = path + 4 if cap < 16 else struct.unpack('<I', h.uc.mem_read(path + 4, 4))[0]
            got = bytes(h.uc.mem_read(ptr, size))
            if got != b'data\\' + name:
                return ['name %r: path %r' % (name, got)]
    return None


def test_find_int_one_bucket(h):
    """The initial map: mask 1, count 1, one real bucket and the list end."""
    mask, count = 1, 1
    keys = [5, 6, 7]
    mapobj, sentinel, nodes = _make_map(h, [(k, k * 2) for k in keys], mask, count)
    for key, want in [(k, nodes[k]) for k in keys] + [(8, sentinel), (1, sentinel)]:
        out = h.alloc(4, b'\0' * 4)
        key_ptr = h.alloc(4, struct.pack('<i', key))
        diffs = h.compare(0x00450DA0, args=[out, key_ptr], regs={UC_X86_REG_ECX: mapobj}, ret=None)
        if diffs:
            return diffs
        res = h.call(0x00450DA0, args=[out, key_ptr], regs={UC_X86_REG_ECX: mapobj})
        if res['fault']:
            return ['key %d: replacement faulted: %s' % (key, res['fault'])]
        got = _u32(h, out)
        if got != want:
            return ['key %d: node %08X, want %08X' % (key, got, want)]
    return None
