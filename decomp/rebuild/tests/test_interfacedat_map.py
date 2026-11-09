"""The engine's pointer-vector fill constructor (0x4CCC80) and the interface record map: its node sentinel
(0x4A2B40), its constructor (0x4A7040) and its clear (0x422AD0).

The vector passed to 0x4CCC80 starts at its allocator byte: +00 allocator, +04 begin, +08 end, +0C limit.  The
record map is an FsHashMap (0x28 bytes) whose sentinel is a whole 0x15C-byte InterfaceRecordNode:
{next; prev; std::string key; InterfaceRecord value}, the value at +24."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

FILL_VECTOR = 0x004CCC80
CREATE_SENTINEL = 0x004A2B40
INIT_RECORD_MAP = 0x004A7040
CLEAR_RECORD_NODES = 0x00422AD0

RECORD_NODE_SIZE = 0x15C
RECORD_OFFSET = 0x24

# the record's string members: name, text142[2], three collection titles, text147
STRING_OFFSETS = (0x00, 0x1C, 0x38, 0x54, 0x80, 0xAC, 0xE8)


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _put_str(h, addr, data):
    """store an MSVC 2005 std::string: the 16 inline bytes (or a pointer), the size and the capacity"""
    if len(data) < 16:
        h.uc.mem_write(addr + 4, data + b'\0' * (16 - len(data)))
        cap = 15
    else:
        block = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', block))
        cap = len(data)
    h.uc.mem_write(addr + 20, struct.pack('<II', len(data), cap))


def _init_record_strings(h, rec):
    for off in STRING_OFFSETS:
        _put_str(h, rec + off, b'')


def test_pointer_vector_fill(h):
    """0x4CCC80 zeroes begin/end/limit and fills a fresh block with copies of the value pointer."""
    for count in (0, 1, 2, 9, 17):
        vector = h.alloc(0x10, b'\xA5' * 0x10)
        value = h.alloc(4, struct.pack('<I', 0xDEADBEEF))
        args = [count, value]
        diffs = h.compare(FILL_VECTOR, args=args, regs={UC_X86_REG_ECX: vector}, ret=None)
        if diffs:
            return ['count %d: %s' % (count, d) for d in diffs]
        res = h.call(FILL_VECTOR, args=args, regs={UC_X86_REG_ECX: vector})
        if res['fault']:
            return ['count %d: replacement faulted: %s' % (count, res['fault'])]
        if _u32(h, vector) != 0xA5A5A5A5:
            return ['count %d: the allocator bytes were touched' % count]
        begin, end, limit = struct.unpack('<III', h.uc.mem_read(vector + 4, 12))
        if count == 0:
            if (begin, end, limit) != (0, 0, 0):
                return ['count 0: %08X/%08X/%08X' % (begin, end, limit)]
            continue
        if begin == 0 or end - begin != 4 * count or limit - begin != 4 * count:
            return ['count %d: begin %08X end %08X limit %08X' % (count, begin, end, limit)]
        for i in range(count):
            if _u32(h, begin + 4 * i) != 0xDEADBEEF:
                return ['count %d: slot %d is %08X' % (count, i, _u32(h, begin + 4 * i))]
    return None


def test_record_node_sentinel(h):
    """0x4A2B40 allocates a whole 0x15C-byte record node linking to itself; key and value stay unconstructed."""
    diffs = h.compare(CREATE_SENTINEL, ret='eax')
    if diffs:
        return diffs
    res = h.call(CREATE_SENTINEL)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax']
    if not node:
        return ['returned null']
    if _u32(h, node) != node or _u32(h, node + 4) != node:
        return ['links %08X/%08X, want %08X' % (_u32(h, node), _u32(h, node + 4), node)]
    return None


def test_init_record_map(h):
    """0x4A7040: the allocator byte, the record-node sentinel, size 0 and nine buckets pointing at it."""
    mapobj = h.alloc(0x28, bytes(0x28))
    allocator = h.alloc(4, b'\x5A\x00\x00\x00')
    args = [allocator, allocator]
    diffs = h.compare(INIT_RECORD_MAP, args=args, regs={UC_X86_REG_ECX: mapobj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(INIT_RECORD_MAP, args=args, regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != mapobj:
        return ['returned %08X, want %08X' % (res['eax'], mapobj)]
    if _u32(h, mapobj) & 0xFF != 0x5A:
        return ['allocator byte %02X' % (_u32(h, mapobj) & 0xFF)]
    sentinel = _u32(h, mapobj + 8)
    if _u32(h, mapobj + 0xC) != 0:
        return ['size %d' % _u32(h, mapobj + 0xC)]
    if not sentinel or _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return ['the sentinel does not link to itself']
    if struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8)) != (1, 1):
        return ['mask/count %r' % (h.uc.mem_read(mapobj + 0x20, 8),)]
    begin, end = struct.unpack('<II', h.uc.mem_read(mapobj + 0x14, 8))
    if end - begin != 36:
        return ['the bucket vector is %d bytes' % (end - begin)]
    for i in range(9):
        if _u32(h, begin + 4 * i) != sentinel:
            return ['bucket slot %d is %08X' % (i, _u32(h, begin + 4 * i))]
    return None


def test_clear_record_nodes(h):
    """0x422AD0 empties the map: the nodes' records and keys are destroyed and the list starts over."""
    mapobj = h.alloc(0x28, bytes(0x28))
    sentinel = h.alloc(RECORD_NODE_SIZE, bytes(RECORD_NODE_SIZE))
    nodes = [h.alloc(RECORD_NODE_SIZE, bytes(RECORD_NODE_SIZE)) for _ in range(2)]
    keys = [b'alpha', b'beta']

    def setup(h):
        ring = [sentinel] + nodes + [sentinel]
        for here, following in zip(ring, ring[1:]):
            h.uc.mem_write(here, struct.pack('<I', following))
        for here, previous in zip(ring[1:], ring):
            h.uc.mem_write(here + 4, struct.pack('<I', previous))
        for node, key in zip(nodes, keys):
            _put_str(h, node + 8, key)
            _init_record_strings(h, node + RECORD_OFFSET)
        h.uc.mem_write(mapobj + 8, struct.pack('<I', sentinel))
        h.uc.mem_write(mapobj + 0xC, struct.pack('<I', len(nodes)))

    diffs = h.compare(CLEAR_RECORD_NODES, regs={UC_X86_REG_ECX: mapobj + 4}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(CLEAR_RECORD_NODES, regs={UC_X86_REG_ECX: mapobj + 4})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return ['the node list was not emptied']
    if _u32(h, mapobj + 0xC) != 0:
        return ['size %d' % _u32(h, mapobj + 0xC)]
    return None
