"""The pak-directory map's copy path: the sentinel factory (0x5AD510), the node-list copy (0x451170), the map
assignment (0x451CF0), the copy constructor (0x452510) and CFileSystem::GetFiles (0x452760).

FsHashMap: +00 allocator bytes, +08 sentinel, +0C size, +10 vector allocator, +14 begin, +18 end, +1C limit,
+20 mask, +24 bucket count.  The pak nodes are 0x30 bytes: next, prev, std::string key, offset, size, pak.  The
bucket vector holds one node pointer per bucket plus the list end, the bucket starts covering the node list in
order."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

CREATE_SENTINEL = 0x005AD510
COPY_NODES = 0x00451170
COPY_FROM = 0x00451CF0
INIT_COPY = 0x00452510
GET_FILES = 0x00452760


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _put_string(h, addr, text=b''):
    """a VC8 string: allocator, inline buffer, size, capacity"""
    assert len(text) < 16
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _read_string(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    ptr = addr + 4 if cap < 16 else _u32(h, addr + 4)
    return bytes(h.uc.mem_read(ptr, size))


def _entry(h, node):
    return (_read_string(h, node + 8),) + struct.unpack('<III', h.uc.mem_read(node + 0x24, 12))


def _walk(h, sentinel, limit=64):
    out, node = [], _u32(h, sentinel)
    while node != sentinel and len(out) < limit:
        out.append(node)
        node = _u32(h, node)
    return out


def _check_ring(h, sentinel):
    forward = _walk(h, sentinel)
    back, node = [], _u32(h, sentinel + 4)
    while node != sentinel and len(back) < 64:
        back.append(node)
        node = _u32(h, node + 4)
    if forward != back[::-1]:
        return 'prev links disagree with next links'
    return None


def _make_pak_map(h, entries, bucket_of, mask, count, allocator=0x5A, addr=None):
    """entries: (key, offset, size, pak), stored grouped by bucket with the keys ascending inside a bucket.
    Returns (map, sentinel, {key: node}); addr places the map object at a given address (an embedded map)."""
    entries = sorted(entries, key=lambda e: (bucket_of(e[0]), e[0]))
    mapobj = h.alloc(0x28, bytes(0x28)) if addr is None else addr
    sentinel = h.alloc(0x30, bytes(0x30))
    nodes = {}
    for key, offset, size, pak in entries:
        node = h.alloc(0x30, bytes(0x30))
        _put_string(h, node + 8, key)
        h.uc.mem_write(node + 0x24, struct.pack('<III', offset, size, pak))
        nodes[key] = node
    ordered = [nodes[key] for key, _, _, _ in entries]
    ring = [sentinel] + ordered + [sentinel]
    for here, following in zip(ring, ring[1:]):
        h.uc.mem_write(here, struct.pack('<I', following))
    for here, previous in zip(ring[1:], ring):
        h.uc.mem_write(here + 4, struct.pack('<I', previous))

    buckets = h.alloc((count + 1) * 4, bytes((count + 1) * 4))
    for i in range(count + 1):
        first = sentinel
        for node, (key, _, _, _) in zip(ordered, entries):
            if bucket_of(key) >= i:
                first = node
                break
        h.uc.mem_write(buckets + 4 * i, struct.pack('<I', first))

    h.uc.mem_write(mapobj, struct.pack('<IIIIIIIII', allocator, 0x02020202, sentinel, len(entries),
                                       0x11111111, buckets, buckets + 4 * (count + 1),
                                       buckets + 4 * (count + 1), mask))
    h.uc.mem_write(mapobj + 0x24, struct.pack('<I', count))
    return mapobj, sentinel, nodes


def _first_bucket(key):
    return 0 if key[0] < ord('m') else 1


def test_create_string_map_sentinel(h):
    """0x5AD510 allocates the 0x30-byte node and links it to itself; the value stays unconstructed."""
    diffs = h.compare(CREATE_SENTINEL, ret='eax')
    if diffs:
        return diffs
    res = h.call(CREATE_SENTINEL)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax']
    if _u32(h, node) != node or _u32(h, node + 4) != node:
        return ['node %08X links %08X/%08X' % (node, _u32(h, node), _u32(h, node + 4))]
    return None


def test_copy_string_map_nodes(h):
    """0x451170 appends fresh copies of [first, last) before the sentinel and counts them in the map size."""
    entries = [(b'wall', 0x100, 0x200, 0), (b'floor', 0x300, 0x400, 1)]
    source, src_sentinel, src_nodes = _make_pak_map(h, entries, _first_bucket, 1, 2)
    counter = h.alloc(0x10, bytes(0x10))
    sentinel = h.alloc(0x30, bytes(0x30))
    existing = h.alloc(0x30, bytes(0x30))
    _put_string(h, existing + 8, b'old')
    h.uc.mem_write(sentinel, struct.pack('<I', existing))
    h.uc.mem_write(sentinel + 4, struct.pack('<I', existing))
    h.uc.mem_write(existing, struct.pack('<I', sentinel))
    h.uc.mem_write(existing + 4, struct.pack('<I', sentinel))

    args = [sentinel, _u32(h, src_sentinel), src_sentinel, source]
    diffs = h.compare(COPY_NODES, args=args, regs={UC_X86_REG_ECX: counter}, ret=None)
    if diffs:
        return diffs
    res = h.call(COPY_NODES, args=args, regs={UC_X86_REG_ECX: counter})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, counter + 8) != 2:
        return ['size %d' % _u32(h, counter + 8)]
    copied = _walk(h, sentinel)
    if len(copied) != 3 or copied[0] != existing:
        return ['list %r' % (copied,)]
    want = [(b'floor', 0x300, 0x400, 1), (b'wall', 0x100, 0x200, 0)]
    got = [_entry(h, node) for node in copied[1:]]
    if got != want:
        return ['entries %r want %r' % (got, want)]
    for node in copied[1:]:
        if node in src_nodes.values():
            return ['the copy reused a source node']
    if _u32(h, sentinel + 4) != copied[-1] or _u32(h, copied[-1]) != sentinel:
        return ['the sentinel tail is not the last copy']
    return _check_ring(h, sentinel)


def test_copy_from(h):
    """0x451CF0 takes the source's bucket count, mask and count, clears the destination nodes, copies the source
    list and points every destination bucket start at its copy."""
    src_entries = [(b'wall', 0x10, 0x20, 0), (b'floor', 0x30, 0x40, 1)]
    source, src_sentinel, src_nodes = _make_pak_map(h, src_entries, _first_bucket, 3, 4, allocator=0x5A)
    dest_entries = [(b'a', 1, 2, 3), (b'z', 4, 5, 6)]
    dest, dst_sentinel, dst_nodes = _make_pak_map(h, dest_entries, _first_bucket, 1, 2, allocator=0x11)

    diffs = h.compare(COPY_FROM, args=[source], regs={UC_X86_REG_ECX: dest}, ret=None)
    if diffs:
        return diffs
    res = h.call(COPY_FROM, args=[source], regs={UC_X86_REG_ECX: dest})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if bytes(h.uc.mem_read(dest, 1)) != b'\x5A':
        return ['the allocator byte is %02X' % bytes(h.uc.mem_read(dest, 1))[0]]
    if _u32(h, dest + 4) != 0x02020202:
        return ['the other allocator bytes changed: %08X' % _u32(h, dest + 4)]
    if struct.unpack('<II', h.uc.mem_read(dest + 0x20, 8)) != (3, 4):
        return ['mask/count %r' % (h.uc.mem_read(dest + 0x20, 8),)]
    if _u32(h, dest + 0xC) != 2:
        return ['size %d' % _u32(h, dest + 0xC)]

    copied = _walk(h, dst_sentinel)
    if len(copied) != 2:
        return ['list %r' % (copied,)]
    if set(copied) & set(dst_nodes.values()):
        return ['a destination node survived the copy']
    if set(copied) & set(src_nodes.values()):
        return ['the copy reused a source node']
    want = [(b'floor', 0x30, 0x40, 1), (b'wall', 0x10, 0x20, 0)]
    got = [_entry(h, node) for node in copied]
    if got != want:
        return ['entries %r want %r' % (got, want)]

    begin, end = _u32(h, dest + 0x14), _u32(h, dest + 0x18)
    if end - begin != 20:
        return ['the bucket vector is %d bytes' % (end - begin)]
    slots = list(struct.unpack('<5I', h.uc.mem_read(begin, 20)))
    if slots != [copied[0], copied[1], dst_sentinel, dst_sentinel, dst_sentinel]:
        return ['bucket starts %r' % (slots,)]
    return _check_ring(h, dst_sentinel)


def test_copy_from_empty_source(h):
    """a source without a bucket vector (a moved-from map) empties the destination."""
    source = h.alloc(0x28, bytes(0x28))
    src_sentinel = h.alloc(0x30, bytes(0x30))
    h.uc.mem_write(src_sentinel, struct.pack('<I', src_sentinel))
    h.uc.mem_write(src_sentinel + 4, struct.pack('<I', src_sentinel))
    h.uc.mem_write(source, struct.pack('<IIIIIIIII', 0x5A, 0x02020202, src_sentinel, 0,
                                       0x11111111, 0, 0, 0, 0))
    h.uc.mem_write(source + 0x24, struct.pack('<I', 0))

    dest, dst_sentinel, dst_nodes = _make_pak_map(h, [(b'a', 1, 2, 3), (b'z', 4, 5, 6)],
                                                  _first_bucket, 1, 2, allocator=0x11)
    diffs = h.compare(COPY_FROM, args=[source], regs={UC_X86_REG_ECX: dest}, ret=None)
    if diffs:
        return diffs
    res = h.call(COPY_FROM, args=[source], regs={UC_X86_REG_ECX: dest})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _walk(h, dst_sentinel):
        return ['the node list was not emptied']
    if _u32(h, dest + 0xC) != 0 or struct.unpack('<II', h.uc.mem_read(dest + 0x20, 8)) != (0, 0):
        return ['size/mask/count %08X/%r' % (_u32(h, dest + 0xC), h.uc.mem_read(dest + 0x20, 8))]
    if bytes(h.uc.mem_read(dest, 1)) != b'\x5A':
        return ['the allocator byte is %02X' % bytes(h.uc.mem_read(dest, 1))[0]]
    begin, end = _u32(h, dest + 0x14), _u32(h, dest + 0x18)
    if begin == 0 or begin != end:
        return ['the bucket vector is %08X/%08X' % (begin, end)]
    return _check_ring(h, dst_sentinel)


def test_init_string_map_copy(h):
    """0x452510 builds the destination from a source map and returns it; the vector allocator byte at +10 is
    left as the caller had it."""
    src_entries = [(b'wall', 0x10, 0x20, 0), (b'floor', 0x30, 0x40, 1), (b'actor', 0x50, 0x60, 2)]
    source, src_sentinel, src_nodes = _make_pak_map(h, src_entries, _first_bucket, 3, 4, allocator=0x5A)
    dest = h.alloc(0x28, b'\xA5' * 0x28)

    diffs = h.compare(INIT_COPY, args=[source], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    res = h.call(INIT_COPY, args=[source], regs={UC_X86_REG_ECX: dest})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != dest:
        return ['returned %08X, want %08X' % (res['eax'], dest)]
    if bytes(h.uc.mem_read(dest + 0x10, 4)) != b'\xA5' * 4:
        return ['the vector allocator bytes were touched: %r' % (h.uc.mem_read(dest + 0x10, 4),)]
    if bytes(h.uc.mem_read(dest, 1)) != b'\x5A':
        return ['the allocator byte is %02X' % bytes(h.uc.mem_read(dest, 1))[0]]
    sentinel = _u32(h, dest + 8)
    if sentinel == src_sentinel:
        return ['the destination reused the source sentinel']
    if _u32(h, dest + 0xC) != 3:
        return ['size %d' % _u32(h, dest + 0xC)]
    if struct.unpack('<II', h.uc.mem_read(dest + 0x20, 8)) != (3, 4):
        return ['mask/count %r' % (h.uc.mem_read(dest + 0x20, 8),)]
    copied = _walk(h, sentinel)
    want = [(b'actor', 0x50, 0x60, 2), (b'floor', 0x30, 0x40, 1), (b'wall', 0x10, 0x20, 0)]
    got = [_entry(h, node) for node in copied]
    if got != want:
        return ['entries %r want %r' % (got, want)]
    if set(copied) & set(src_nodes.values()):
        return ['the copy reused a source node']
    return _check_ring(h, sentinel)


def test_get_files(h):
    """0x452760 copies CFileSystem's pak directory (at +10) into the caller's map and returns it."""
    src_entries = [(b'wall', 0x100, 0x200, 0), (b'floor', 0x300, 0x400, 1), (b'ceiling', 0x500, 0x600, 2)]
    fs = h.alloc(0xB8, b'\xCC' * 0xB8)
    source, src_sentinel, src_nodes = _make_pak_map(h, src_entries, _first_bucket, 1, 2,
                                                   allocator=0x5A, addr=fs + 0x10)
    out = h.alloc(0x28, b'\xA5' * 0x28)

    diffs = h.compare(GET_FILES, args=[out], regs={UC_X86_REG_ECX: fs}, ret='eax')
    if diffs:
        return diffs
    res = h.call(GET_FILES, args=[out], regs={UC_X86_REG_ECX: fs})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != out:
        return ['returned %08X, want %08X' % (res['eax'], out)]
    if bytes(h.uc.mem_read(out + 0x10, 4)) != b'\xA5' * 4:
        return ['the vector allocator bytes were touched: %r' % (h.uc.mem_read(out + 0x10, 4),)]
    if bytes(h.uc.mem_read(out, 1)) != b'\x5A':
        return ['the allocator byte is %02X' % bytes(h.uc.mem_read(out, 1))[0]]
    if _u32(h, out + 0xC) != 3:
        return ['size %d' % _u32(h, out + 0xC)]
    copied = _walk(h, _u32(h, out + 8))
    want = [(b'ceiling', 0x500, 0x600, 2), (b'floor', 0x300, 0x400, 1), (b'wall', 0x100, 0x200, 0)]
    got = [_entry(h, node) for node in copied]
    if got != want:
        return ['entries %r want %r' % (got, want)]
    if len(_walk(h, src_sentinel)) != 3 or _u32(h, source + 0xC) != 3:
        return ['the source map changed']
    if set(copied) & set(src_nodes.values()):
        return ['the copy reused a source node']
    return None
