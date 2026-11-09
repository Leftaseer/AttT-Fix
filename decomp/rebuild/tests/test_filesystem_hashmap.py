"""FsHashMap's bucket hashes (0x450D20, 0x422A20), its int-keyed lookup (0x450DA0), its string-keyed lookups
(0x450E60 case-insensitive, 0x422D80 case-sensitive), CFileSystem's name-prefix resolver (0x451220) and the
file system's singleton accessor (0x44ABE0).

The map's bucket vector at +14 holds one node pointer per bucket plus the list end: the nodes of bucket i run
from buckets[i] to buckets[i+1] through next.  The int map's nodes are {next; prev; key; value}, the string
map's are {next; prev; std::string key; value} with the value at +24.  A lookup returns the sentinel at +08
when the key is not in its bucket."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

STRING_HASH = 0x00579BB0
NAME_HASH = 0x00422A20
CREATE_PAK_NODE = 0x00451000
CREATE_STREAM_NODE = 0x00489070
INSERT_NAME = 0x00451770
INSERT_INT = 0x00451A50
INIT_STRING_MAP = 0x00451430
INIT_INT_MAP = 0x00489710


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


def _make_string_map(h, entries, mask, count, bucket=None, order=None):
    """entries: (key bytes, value payload); keys ascending inside a bucket, as the map keeps them.  bucket and
    order select the map's hash and comparison (by default the case-insensitive ones)."""
    if bucket is None:
        bucket = lambda key: _bucket_of_string(h, key, mask, count)
    if order is None:
        order = lambda key: key.lower()
    entries = sorted(entries, key=lambda e: (bucket(e[0]), order(e[0])))
    mapobj = h.alloc(0x28, bytes(0x28))
    sentinel = h.alloc(0x10, bytes(0x10))
    nodes = {}
    for key, payload in entries:
        node = h.alloc(0x28, bytes(0x28))
        _put_string(h, node + 8, key)
        h.uc.mem_write(node + 0x24, struct.pack('<I', payload))
        nodes[key] = node
    ordered = [nodes[key] for key, _ in entries]
    ring = [sentinel] + ordered + [sentinel]
    for here, following in zip(ring, ring[1:]):
        h.uc.mem_write(here, struct.pack('<I', following))
    for here, previous in zip(ring[1:], ring):
        h.uc.mem_write(here + 4, struct.pack('<I', previous))

    buckets = h.alloc((count + 1) * 4, b'\0' * ((count + 1) * 4))
    for i in range(count + 1):
        first = sentinel
        for node, (key, _) in zip(ordered, entries):
            if bucket(key) >= i:
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
    ring = [sentinel] + ordered + [sentinel]
    for here, following in zip(ring, ring[1:]):
        h.uc.mem_write(here, struct.pack('<I', following))
    for here, previous in zip(ring[1:], ring):
        h.uc.mem_write(here + 4, struct.pack('<I', previous))

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


def test_hash_name(h):
    for key in (b'', b'a', b'ab', b'alpha', b'texture.tex', b'\xff\x80z'):
        keyobj = h.alloc(28, bytes(28))
        _put_string(h, keyobj, key)
        diffs = h.compare(NAME_HASH, args=[keyobj], ret='eax')
        if diffs:
            return diffs
        res = h.call(NAME_HASH, args=[keyobj])
        if res['fault']:
            return ['key %r: replacement faulted: %s' % (key, res['fault'])]
        if res['eax'] != _name_hash(key):
            return ['key %r: hash %08X, want %08X' % (key, res['eax'], _name_hash(key))]
    return None


def test_find_name(h):
    """The case-sensitive file map: case must match, the comparison is std::string's operator<."""
    mask, count = 7, 8
    keys = [b'alpha', b'Beta', b'gamma', b'Delta', b'omega']
    bucket = lambda key: _name_bucket(key, mask, count)
    mapobj, sentinel, nodes = _make_string_map(h, [(k, 0xC0 + i) for i, k in enumerate(keys)],
                                               mask, count, bucket=bucket, order=lambda k: k)
    cases = [(k, nodes[k]) for k in keys]
    cases += [(b'ALPHA', sentinel), (b'beta', sentinel), (b'BETA', sentinel), (b'', sentinel),
              (b'zeta', sentinel), (b'alph', sentinel)]
    for key, want in cases:
        out = h.alloc(4, b'\0' * 4)
        keyptr = h.alloc(28, bytes(28))
        _put_string(h, keyptr, key)
        diffs = h.compare(0x00422D80, args=[out, keyptr], regs={UC_X86_REG_ECX: mapobj}, ret=None)
        if diffs:
            return diffs
        res = h.call(0x00422D80, args=[out, keyptr], regs={UC_X86_REG_ECX: mapobj})
        if res['fault']:
            return ['key %r: replacement faulted: %s' % (key, res['fault'])]
        got = _u32(h, out)
        if got != want:
            return ['key %r: node %08X, want %08X' % (key, got, want)]
    return None


def test_file_system_instance(h):
    """The getter builds the singleton on the first call and returns it thereafter."""
    diffs = h.compare(0x0044ABE0, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x0044ABE0)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    obj = res['eax']
    if not obj:
        return ['returned null']
    if _u32(h, 0x006C8C28) != obj:
        return ['singleton %08X, returned %08X' % (_u32(h, 0x006C8C28), obj)]
    return None


def _check_initial_map(h, mapobj, sentinel, allocator):
    if _u32(h, mapobj) & 0xFF != allocator:
        return ['allocator byte %02X, want %02X' % (_u32(h, mapobj) & 0xFF, allocator)]
    if not sentinel:
        return ['no sentinel']
    if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return ['sentinel does not link to itself']
    if _u32(h, mapobj + 0xC) != 0:
        return ['size %d' % _u32(h, mapobj + 0xC)]
    if struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8)) != (1, 1):
        return ['mask/count %r' % (h.uc.mem_read(mapobj + 0x20, 8),)]
    begin = _u32(h, mapobj + 0x14)
    if _u32(h, mapobj + 0x18) - begin != 36:
        return ['bucket vector is %d bytes' % (_u32(h, mapobj + 0x18) - begin)]
    for i in range(9):
        if _u32(h, begin + 4 * i) != sentinel:
            return ['bucket slot %d is %08X' % (i, _u32(h, begin + 4 * i))]
    return None


def _test_init_map(h, addr, allocator_value):
    mapobj = h.alloc(0x28, bytes(0x28))
    allocator = h.alloc(4, struct.pack('<I', allocator_value))
    args = [allocator, allocator]
    diffs = h.compare(addr, args=args, regs={UC_X86_REG_ECX: mapobj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(addr, args=args, regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != mapobj:
        return ['returned %08X, want %08X' % (res['eax'], mapobj)]
    sentinel = _u32(h, mapobj + 8)
    return _check_initial_map(h, mapobj, sentinel, allocator_value)


def test_init_string_map(h):
    return _test_init_map(h, 0x00451430, 0x5A)


def test_init_int_map(h):
    return _test_init_map(h, 0x00489710, 0xC3)


def test_clear_string_nodes(h):
    """0x5224A0 takes the library's map object at FsHashMap+4 and frees every node, destroying its key."""
    mask, count = 7, 8
    keys = [b'alpha', b'Beta', b'gamma']
    mapobj, sentinel, nodes = _make_string_map(h, [(k, 0xD0 + i) for i, k in enumerate(keys)], mask, count)
    diffs = h.compare(0x005224A0, regs={UC_X86_REG_ECX: mapobj + 4}, ret=None)
    if diffs:
        return diffs
    res = h.call(0x005224A0, regs={UC_X86_REG_ECX: mapobj + 4})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return ['node list not emptied']
    if _u32(h, mapobj + 0xC) != 0:
        return ['size %d' % _u32(h, mapobj + 0xC)]
    return None


def test_clear_int(h):
    """0x4EF7F0 frees the int map's nodes and resets the bucket vector, mask and count."""
    mask, count = 7, 8
    keys = [3, 9, 17]
    mapobj, sentinel, nodes = _make_map(h, [(k, k * 3) for k in keys], mask, count)
    diffs = h.compare(0x004EF7F0, regs={UC_X86_REG_ECX: mapobj}, ret=None)
    if diffs:
        return diffs
    res = h.call(0x004EF7F0, regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return ['node list not emptied']
    if _u32(h, mapobj + 0xC) != 0:
        return ['size %d' % _u32(h, mapobj + 0xC)]
    if struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8)) != (1, 1):
        return ['mask/count %r' % (h.uc.mem_read(mapobj + 0x20, 8),)]
    begin = _u32(h, mapobj + 0x14)
    for i in range(9):
        if _u32(h, begin + 4 * i) != sentinel:
            return ['bucket slot %d is %08X' % (i, _u32(h, begin + 4 * i))]
    return None


def _read_string(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    ptr = addr + 4 if cap < 16 else _u32(h, addr + 4)
    return bytes(h.uc.mem_read(ptr, size))


def _walk_string_list(h, mapobj):
    sentinel = _u32(h, mapobj + 8)
    keys, node = [], _u32(h, sentinel)
    while node != sentinel:
        keys.append(_read_string(h, node + 8))
        node = _u32(h, node)
    return keys


def _walk_int_list(h, mapobj):
    sentinel = _u32(h, mapobj + 8)
    keys, node = [], _u32(h, sentinel)
    while node != sentinel:
        keys.append(_u32(h, node + 8))
        node = _u32(h, node)
    return keys


def _check_ring(h, mapobj):
    """the node list is doubly linked and ends where it starts"""
    sentinel = _u32(h, mapobj + 8)
    node, forward = _u32(h, sentinel), []
    while node != sentinel:
        forward.append(node)
        node = _u32(h, node)
        if len(forward) > 10000:
            return ['node list does not end']
    back, node = [], _u32(h, sentinel + 4)
    while node != sentinel:
        back.append(node)
        node = _u32(h, node + 4)
    if forward != back[::-1]:
        return ['prev links disagree with next links']
    return None


def _check_string_buckets(h, mapobj):
    """every node of bucket i hashes to i, and the buckets cover the list in order"""
    mask, count = struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8))
    begin = _u32(h, mapobj + 0x14)
    sentinel = _u32(h, mapobj + 8)
    for bucket in range(count):
        node, end = _u32(h, begin + 4 * bucket), _u32(h, begin + 4 * bucket + 4)
        while node != end:
            if _name_bucket(_read_string(h, node + 8), mask, count) != bucket:
                return ['bucket %d holds %r' % (bucket, _read_string(h, node + 8))]
            if _u32(h, node) == sentinel and node != end and end != sentinel:
                return ['bucket %d runs past the sentinel' % bucket]
            node = _u32(h, node)
    return None


def _check_int_buckets(h, mapobj):
    mask, count = struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8))
    begin = _u32(h, mapobj + 0x14)
    for bucket in range(count):
        node, end = _u32(h, begin + 4 * bucket), _u32(h, begin + 4 * bucket + 4)
        while node != end:
            if _bucket_of(_u32(h, node + 8), mask, count) != bucket:
                return ['bucket %d holds %d' % (bucket, _u32(h, node + 8))]
            node = _u32(h, node)
    return None


def _fresh_map(h, init_addr, allocator):
    mapobj = h.alloc(0x28, bytes(0x28))
    alloc = h.alloc(4, struct.pack('<I', allocator))
    res = h.call(init_addr, args=[alloc, alloc], regs={UC_X86_REG_ECX: mapobj})
    if res['fault'] or res['eax'] != mapobj:
        raise AssertionError('map init %08X failed: %r' % (init_addr, res))
    return mapobj


def test_create_pak_node(h):
    """0x451000 allocates the 0x30-byte node, links it and copies the entry (key string and three fields)."""
    next_node = h.alloc(0x10, bytes(0x10))
    prev_node = h.alloc(0x10, bytes(0x10))
    entry = h.alloc(0x28, bytes(0x28))
    _put_string(h, entry, b'data\\wall.tex')
    h.uc.mem_write(entry + 0x1C, struct.pack('<III', 0x1234, 0x5678, 2))
    args = [next_node, prev_node, entry]
    diffs = h.compare(CREATE_PAK_NODE, args=args, ret='eax')
    if diffs:
        return diffs
    res = h.call(CREATE_PAK_NODE, args=args)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax']
    if _u32(h, node) != next_node or _u32(h, node + 4) != prev_node:
        return ['links %08X/%08X' % (_u32(h, node), _u32(h, node + 4))]
    if _read_string(h, node + 8) != b'data\\wall.tex':
        return ['key %r' % _read_string(h, node + 8)]
    if struct.unpack('<III', h.uc.mem_read(node + 0x24, 12)) != (0x1234, 0x5678, 2):
        return ['entry %r' % (h.uc.mem_read(node + 0x24, 12),)]
    return None


def test_create_stream_node(h):
    """0x489070 allocates the 0x10-byte node and copies the {index; stream} pair."""
    next_node = h.alloc(0x10, bytes(0x10))
    prev_node = h.alloc(0x10, bytes(0x10))
    entry = h.alloc(8, struct.pack('<II', 7, 0xDEADBEEF))
    args = [next_node, prev_node, entry]
    diffs = h.compare(CREATE_STREAM_NODE, args=args, ret='eax')
    if diffs:
        return diffs
    res = h.call(CREATE_STREAM_NODE, args=args)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax']
    if struct.unpack('<IIII', h.uc.mem_read(node, 16)) != (next_node, prev_node, 7, 0xDEADBEEF):
        return ['node %r' % (h.uc.mem_read(node, 16),)]
    return None


def test_insert_name(h):
    """0x451770 keeps the files by key: ascending case-sensitive keys, growth when a bucket fills up, the
    node a duplicate insert reports and the original value left alone."""
    mapobj = _fresh_map(h, INIT_STRING_MAP, 0x5A)
    keys = [b'zeta', b'Alpha', b'beta', b'gamma', b'Delta', b'epsilon', b'ALPHA',
            b'wall', b'floor', b'ceil', b'door', b'window', b'roof', b'stair',
            b'light', b'camera', b'model', b'actor', b'level', b'zone',
            b'trigger', b'sound', b'music', b'font', b'gui', b'shader']
    for i, key in enumerate(keys):
        entry = h.alloc(0x28, bytes(0x28))
        _put_string(h, entry, key)
        h.uc.mem_write(entry + 0x1C, struct.pack('<III', 0x100 + i, 0x200 + i, i & 3))
        result = h.alloc(8, bytes(8))
        diffs = h.compare(INSERT_NAME, args=[result, entry], regs={UC_X86_REG_ECX: mapobj}, ret=None)
        if diffs:
            return ['%r: %s' % (key, d) for d in diffs]
        res = h.call(INSERT_NAME, args=[result, entry], regs={UC_X86_REG_ECX: mapobj})
        if res['fault']:
            return ['%r: replacement faulted: %s' % (key, res['fault'])]
        node, inserted = struct.unpack('<IB', h.uc.mem_read(result, 5))
        if inserted != (0 if key in keys[:i] else 1):
            return ['%r: inserted %d' % (key, inserted)]
        if inserted:
            if _u32(h, node + 0x24) != 0x100 + i or _u32(h, node + 0x28) != 0x200 + i:
                return ['%r: value %08X/%08X' % (key, _u32(h, node + 0x24), _u32(h, node + 0x28))]
        elif node != _find_name(h, mapobj, key):
            return ['%r: duplicate reported another node' % (key,)]
        if _u32(h, mapobj + 0xC) != len(set(keys[:i + 1])):
            return ['%r: size %d' % (key, _u32(h, mapobj + 0xC))]
        problem = _check_ring(h, mapobj) or _check_string_buckets(h, mapobj)
        if problem:
            return ['%r: %s' % (key, problem)]
    expected = _expected_list(h, mapobj, set(keys), _name_bucket)
    if _walk_string_list(h, mapobj) != expected:
        return ['list %r, want %r' % (_walk_string_list(h, mapobj), expected)]
    return None


def _find_name(h, mapobj, key):
    keyobj = h.alloc(28, bytes(28))
    _put_string(h, keyobj, key)
    out = h.alloc(4, b'\0' * 4)
    h.call(0x00422D80, args=[out, keyobj], regs={UC_X86_REG_ECX: mapobj})
    return _u32(h, out)


def test_insert_int(h):
    """0x451A50 orders the streams by their index and grows the same way."""
    mapobj = _fresh_map(h, INIT_INT_MAP, 0xC3)
    keys = [5, 0, 17, 3, 9, 2, 31, 8, 1, 12, 4, 27, 6, 19, 11, 0,
            23, 14, 7, 30, 13, 21, 10, 25, 16, 29, 18, 15, 22, 20]
    for i, key in enumerate(keys):
        entry = h.alloc(8, struct.pack('<II', key & 0xFFFFFFFF, 0xA000 + i))
        result = h.alloc(8, bytes(8))
        diffs = h.compare(INSERT_INT, args=[result, entry], regs={UC_X86_REG_ECX: mapobj}, ret=None)
        if diffs:
            return ['key %d: %s' % (key, d) for d in diffs]
        res = h.call(INSERT_INT, args=[result, entry], regs={UC_X86_REG_ECX: mapobj})
        if res['fault']:
            return ['key %d: replacement faulted: %s' % (key, res['fault'])]
        node, inserted = struct.unpack('<IB', h.uc.mem_read(result, 5))
        if inserted != (0 if key in keys[:i] else 1):
            return ['key %d: inserted %d' % (key, inserted)]
        if _u32(h, mapobj + 0xC) != len(set(keys[:i + 1])):
            return ['key %d: size %d' % (key, _u32(h, mapobj + 0xC))]
        problem = _check_ring(h, mapobj) or _check_int_buckets(h, mapobj)
        if problem:
            return ['key %d: %s' % (key, problem)]
    expected = _expected_list(h, mapobj, set(keys), _bucket_of)
    if _walk_int_list(h, mapobj) != expected:
        return ['list %r, want %r' % (_walk_int_list(h, mapobj), expected)]
    return None


def test_map_size_guards(h):
    """0x4E66E0 / 0x4EB9C0 add to the map size as long as it stays within the node allocation limit."""
    for addr, limit, cases in ((0x004E66E0, 0x6666666, ((0, 1), (0x6666660, 6), (5, 0))),
                               (0x004EB9C0, 0x1FFFFFFF, ((0, 1), (0x1FFFFFF0, 15), (7, 0)))):
        for size, count in cases:
            buf = h.alloc(0x10, bytes(0x10))
            h.uc.mem_write(buf + 0xC, struct.pack('<I', size))
            diffs = h.compare(addr, args=[count], regs={UC_X86_REG_ECX: buf + 4}, ret=None)
            if diffs:
                return ['%08X size %X + %d: %s' % (addr, size, count, d) for d in diffs]
            res = h.call(addr, args=[count], regs={UC_X86_REG_ECX: buf + 4})
            if res['fault']:
                return ['%08X size %X + %d: fault %s' % (addr, size, count, res['fault'])]
            if _u32(h, buf + 0xC) != size + count:
                return ['%08X size %X + %d: got %X' % (addr, size, count, _u32(h, buf + 0xC))]
    return None


def _expected_list(h, mapobj, keys, bucket_of):
    """the list is the buckets in order, each holding its keys ascending"""
    mask, count = struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8))
    out = []
    for bucket in range(count):
        out += sorted(k for k in keys if bucket_of(k, mask, count) == bucket)
    return out
