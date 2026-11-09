"""FsHashMap's bucket hash (0x450D20) and its int-keyed lookup (0x450DA0).

The map's bucket vector at +14 holds one node pointer per bucket plus the list end: the nodes of bucket i run
from buckets[i] to buckets[i+1] through next.  The int map's nodes are {next; prev; key; value}, and the lookup
returns the sentinel at +08 when the key is not in its bucket."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX


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
