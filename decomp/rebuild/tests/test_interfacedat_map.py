"""The engine's pointer-vector fill constructor (0x4CCC80) and the interface record map: its node sentinel
(0x4A2B40), its constructor (0x4A7040), its clear (0x422AD0), its operator[] (0x424270) and the insert path
that creates a node (0x423FB0 / 0x423D70 / 0x423C10 / 0x423C70 / 0x420AE0 / 0x422410).

The vector passed to 0x4CCC80 starts at its allocator byte: +00 allocator, +04 begin, +08 end, +0C limit.  The
record map is an FsHashMap (0x28 bytes) whose sentinel is a whole 0x15C-byte InterfaceRecordNode:
{next; prev; std::string key; InterfaceRecord value}, the value at +24."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

from difftest import STACK, STACK_SIZE

FILL_VECTOR = 0x004CCC80
CREATE_SENTINEL = 0x004A2B40
INIT_RECORD_MAP = 0x004A7040
CLEAR_RECORD_NODES = 0x00422AD0
INDEX = 0x00424270
INSERT_NODE = 0x00423FB0
CREATE_NODE = 0x00423D70
COPY_PAIR = 0x00423C10
BUILD_PAIR = 0x00423C70
DESTROY_PAIR = 0x00420AE0
ADD_MAP_SIZE = 0x00422410

RECORD_NODE_SIZE = 0x15C
RECORD_OFFSET = 0x24
RECORD_SIZE = 0x138
PAIR_SIZE = 0x154
PAIR_VALUE = 0x1C      # the record's offset inside the pair
MAP_SIZE = 0x28
BUCKETS = 9

# the record's string members: name, text142[2], three collection titles, text147
STRING_OFFSETS = (0x00, 0x1C, 0x38, 0x54, 0x80, 0xAC, 0xE8)
# the vectors' begin pointers and their untouched allocator dwords
VECTOR_BEGINS = (0x74, 0xA0, 0xCC, 0xDC, 0x11C, 0x12C)
VECTOR_ALLOCATORS = (0x70, 0x9C, 0xC8, 0xD8, 0x118, 0x128)


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


def _get_str(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    ptr = addr + 4 if cap < 16 else _u32(h, addr + 4)
    return bytes(h.uc.mem_read(ptr, size))


def _init_record_strings(h, rec):
    for off in STRING_OFFSETS:
        _put_str(h, rec + off, b'')


def _put_record(h, record, prefix, fill=0xA5):
    """a record with its seven strings, six empty vectors and the numbers"""
    h.uc.mem_write(record, bytes([fill]) * RECORD_SIZE)
    for i, off in enumerate(STRING_OFFSETS):
        _put_str(h, record + off, prefix + bytes([0x30 + i]))
    for off in VECTOR_BEGINS:
        h.uc.mem_write(record + off, bytes(12))
    h.uc.mem_write(record + 0x104, struct.pack('<f', 2.5))
    h.uc.mem_write(record + 0x108, struct.pack('<4f', 1.5, -2.25, 3.0, 4.0))


def _check_record(h, record, prefix, fill):
    """compares a copied record with _put_record's; fill is what its vector allocator dwords must still hold"""
    for i, off in enumerate(STRING_OFFSETS):
        want = prefix + bytes([0x30 + i])
        if _get_str(h, record + off) != want:
            return 'the string at +%02X is %r, wanted %r' % (off, _get_str(h, record + off), want)
    for off in VECTOR_BEGINS:
        if struct.unpack('<III', h.uc.mem_read(record + off, 12)) != (0, 0, 0):
            return 'the vector at +%02X is not empty' % off
    for off in VECTOR_ALLOCATORS:
        if _u32(h, record + off) != fill * 0x01010101:
            return 'the vector allocator at +%02X was touched' % off
    if struct.unpack('<f', h.uc.mem_read(record + 0x104, 4))[0] != 2.5:
        return 'the 0x14B float was not copied'
    if struct.unpack('<4f', h.uc.mem_read(record + 0x108, 16)) != (1.5, -2.25, 3.0, 4.0):
        return 'the 0x149 floats were not copied'
    return None


def _fill_stack(h):
    """The empty record's 0x149 floats are never written before the map copies them; both runs must read the
    same stale bytes from their (differently laid out) frames for the copied node to compare equal."""
    h.uc.mem_write(STACK + STACK_SIZE - 0x8000, bytes([0x5A]) * 0x8000)


def _init_map(h, mapobj):
    """an empty record map: a self-linked sentinel, no records and nine sentinel buckets"""
    sentinel = h.alloc(RECORD_NODE_SIZE, bytes(RECORD_NODE_SIZE))
    buckets = h.alloc(BUCKETS * 4, struct.pack('<%dI' % BUCKETS, *([sentinel] * BUCKETS)))
    h.uc.mem_write(sentinel, struct.pack('<II', sentinel, sentinel))
    h.uc.mem_write(mapobj + 0x08, struct.pack('<II', sentinel, 0))
    h.uc.mem_write(mapobj + 0x14, struct.pack('<III', buckets, buckets + BUCKETS * 4, buckets + BUCKETS * 4))
    h.uc.mem_write(mapobj + 0x20, struct.pack('<II', 1, 1))
    return sentinel


def _insert_key(h, mapobj, name):
    """a setup helper: insert an empty record through the translated operator[] and return its node"""
    key = h.alloc(0x1C, bytes(0x1C))
    _put_str(h, key, name)
    res = h.call(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        raise RuntimeError('operator[] faulted: %s' % res['fault'])
    return res['eax'] - RECORD_OFFSET


def _put_pair(h, pair, name, prefix):
    h.uc.mem_write(pair, bytes([0xA5]) * PAIR_SIZE)
    _put_str(h, pair, name)
    _put_record(h, pair + PAIR_VALUE, prefix)


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


def test_record_map_index_hit(h):
    """0x424270 returns &node->value of a key already in the map and leaves the map alone."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    node = h.alloc(RECORD_NODE_SIZE, bytes(RECORD_NODE_SIZE))
    key = h.alloc(0x1C, bytes(0x1C))
    state = {}

    def setup(h):
        sentinel = _init_map(h, mapobj)
        h.uc.mem_write(_u32(h, mapobj + 0x14), struct.pack('<I', node))
        h.uc.mem_write(mapobj + 0x0C, struct.pack('<I', 1))
        h.uc.mem_write(sentinel, struct.pack('<II', node, node))
        h.uc.mem_write(node, struct.pack('<II', sentinel, sentinel))
        _put_str(h, key, b'known')
        _put_str(h, node + 8, b'known')
        _put_record(h, node + RECORD_OFFSET, b'k')
        state['heap'] = h.heap_ptr

    diffs = h.compare(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != node + RECORD_OFFSET:
        return ['returned %#x, wanted &node->value %#x' % (res['eax'], node + RECORD_OFFSET)]
    if _u32(h, mapobj + 0x0C) != 1:
        return ['the map size changed to %d' % _u32(h, mapobj + 0x0C)]
    return []


def test_record_map_index_insert(h):
    """0x424270 inserts a node holding an empty record for a missing key and returns its value."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    key = h.alloc(0x1C, bytes(0x1C))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        _put_str(h, key, b'new-record')
        _fill_stack(h)
        state['heap'] = h.heap_ptr

    diffs = h.compare(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    record = res['eax']
    if not record:
        return ['returned null']
    node = record - RECORD_OFFSET
    sentinel = _u32(h, mapobj + 0x08)
    if _u32(h, mapobj + 0x0C) != 1:
        return ['the map size is %d' % _u32(h, mapobj + 0x0C)]
    if struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8)) != (1, 1):
        return ['mask/count changed']
    if (_u32(h, node), _u32(h, node + 4)) != (sentinel, sentinel):
        return ['the node does not sit before the sentinel']
    if (_u32(h, sentinel), _u32(h, sentinel + 4)) != (node, node):
        return ['the sentinel does not link to the node']
    if _u32(h, _u32(h, mapobj + 0x14)) != node:
        return ['the first bucket does not start at the node']
    if _get_str(h, node + 8) != b'new-record':
        return ['the key is %r' % _get_str(h, node + 8)]
    for off in STRING_OFFSETS:
        if _get_str(h, record + off) != b'':
            return ['the string at +%02X is not empty' % off]
    for off in VECTOR_BEGINS:
        if struct.unpack('<III', h.uc.mem_read(record + off, 12)) != (0, 0, 0):
            return ['the vector at +%02X is not null' % off]
    for off in VECTOR_ALLOCATORS:
        if _u32(h, record + off) != 0:
            return ['the vector allocator at +%02X was touched' % off]
    if _u32(h, record + 0x104) != 0:
        return ['the 0x14B float is not zero']
    if struct.unpack('<4I', h.uc.mem_read(record + 0x108, 16)) != (0x5A5A5A5A,) * 4:
        return ['the uninitialised 0x149 floats were not copied from the temporary record']
    return []


def test_record_map_index_long_key(h):
    """0x424270 copies a key longer than the inline buffer into the node."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    key = h.alloc(0x1C, bytes(0x1C))
    name = b'a-very-long-key-name-0123456789'
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        _put_str(h, key, name)
        _fill_stack(h)
        state['heap'] = h.heap_ptr

    diffs = h.compare(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax'] - RECORD_OFFSET
    if _get_str(h, node + 8) != name:
        return ['the key is %r' % _get_str(h, node + 8)]
    return []


def test_record_map_index_growth(h):
    """The insert that fills the last bucket rehashes the map: the mask grows to 15, the bucket vector doubles
    to seventeen slots and every node is still reachable.  (Earlier inserts grow the mask only.)"""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    key = h.alloc(0x1C, bytes(0x1C))
    state = {}
    names = tuple(b'key%02d' % i for i in range(32))

    def setup(h):
        _init_map(h, mapobj)
        for name in names:
            _insert_key(h, mapobj, name)
        _put_str(h, key, b'extra')
        _fill_stack(h)
        state['heap'] = h.heap_ptr

    diffs = h.compare(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, mapobj + 0x0C) != 33:
        return ['the map size is %d' % _u32(h, mapobj + 0x0C)]
    begin, end = struct.unpack('<II', h.uc.mem_read(mapobj + 0x14, 8))
    if end - begin != 17 * 4:
        return ['the bucket vector is %d bytes' % (end - begin)]
    if _u32(h, mapobj + 0x20) != 15:
        return ['the mask is %d' % _u32(h, mapobj + 0x20)]
    for name in names + (b'extra',):
        k = h.alloc(0x1C, bytes(0x1C))
        _put_str(h, k, name)
        found = h.call(INDEX, args=[k], regs={UC_X86_REG_ECX: mapobj})
        if found['fault']:
            return ['operator[] faulted: %s' % found['fault']]
        if _get_str(h, found['eax'] - RECORD_OFFSET + 8) != name:
            return ['the node of %r is not found after the growth' % name]
    return []


def test_insert_record_node(h):
    """0x423FB0 links a new node before its lower bound and reports it."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    result = h.alloc(8, bytes(8))
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        for name in (b'alpha', b'beta', b'gamma'):
            _insert_key(h, mapobj, name)
        _put_pair(h, pair, b'delta', b'd')
        state['heap'] = h.heap_ptr

    diffs = h.compare(INSERT_NODE, args=[result, pair], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INSERT_NODE, args=[result, pair], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != result:
        return ['returned %#x, not the result slot' % res['eax']]
    if h.uc.mem_read(result + 4, 1) != b'\x01':
        return ['the insert did not report a new node']
    node = _u32(h, result)
    if _get_str(h, node + 8) != b'delta':
        return ['the node key is %r' % _get_str(h, node + 8)]
    diffs = _check_record(h, node + RECORD_OFFSET, b'd', 0)
    if diffs:
        return [diffs]
    if _u32(h, mapobj + 0x0C) != 4:
        return ['the map size is %d' % _u32(h, mapobj + 0x0C)]
    if _u32(h, _u32(h, node + 4)) != node or _u32(h, _u32(h, node) + 4) != node:
        return ['the node links are inconsistent']
    return []


def test_insert_record_node_duplicate(h):
    """0x423FB0 returns the existing node of a duplicate key and does not allocate."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    result = h.alloc(8, bytes(8))
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        for name in (b'alpha', b'beta', b'gamma'):
            _insert_key(h, mapobj, name)
        _put_pair(h, pair, b'beta', b'x')
        state['heap'] = h.heap_ptr

    diffs = h.compare(INSERT_NODE, args=[result, pair], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    marker = h.heap_ptr
    res = h.call(INSERT_NODE, args=[result, pair], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if h.uc.mem_read(result + 4, 1) != b'\x00':
        return ['the insert reported a new node for a duplicate key']
    if _get_str(h, _u32(h, result) + 8) != b'beta':
        return ['the reported node is not the key\'s']
    if _u32(h, mapobj + 0x0C) != 3:
        return ['the map size is %d' % _u32(h, mapobj + 0x0C)]
    if h.heap_ptr != marker:
        return ['a duplicate insert allocated']
    return []


def test_insert_record_node_growth(h):
    """0x423FB0 rehashes when the last bucket is full, growing the bucket vector to seventeen slots."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    result = h.alloc(8, bytes(8))
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    state = {}
    names = tuple(b'key%02d' % i for i in range(32))

    def setup(h):
        _init_map(h, mapobj)
        for name in names:
            _insert_key(h, mapobj, name)
        _put_pair(h, pair, b'extra', b'e')
        state['heap'] = h.heap_ptr

    diffs = h.compare(INSERT_NODE, args=[result, pair], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INSERT_NODE, args=[result, pair], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if h.uc.mem_read(result + 4, 1) != b'\x01':
        return ['the insert did not report a new node']
    if _u32(h, mapobj + 0x0C) != 33:
        return ['the map size is %d' % _u32(h, mapobj + 0x0C)]
    begin, end = struct.unpack('<II', h.uc.mem_read(mapobj + 0x14, 8))
    if end - begin != 17 * 4:
        return ['the bucket vector is %d bytes' % (end - begin)]
    if _u32(h, mapobj + 0x20) != 15:
        return ['the mask is %d' % _u32(h, mapobj + 0x20)]
    return []


def test_create_record_node(h):
    """0x423D70 allocates a node and copies the pair behind its links."""
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))

    def setup(h):
        _put_pair(h, pair, b'node-key', b'n')

    diffs = h.compare(CREATE_NODE, args=[0x11111111, 0x22222222, pair], setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(CREATE_NODE, args=[0x11111111, 0x22222222, pair])
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax']
    if not node:
        return ['returned null']
    if (_u32(h, node), _u32(h, node + 4)) != (0x11111111, 0x22222222):
        return ['the links are %08X/%08X' % (_u32(h, node), _u32(h, node + 4))]
    if _get_str(h, node + 8) != b'node-key':
        return ['the key is %r' % _get_str(h, node + 8)]
    diffs = _check_record(h, node + RECORD_OFFSET, b'n', 0)
    if diffs:
        return [diffs]
    return []


def test_build_record_pair(h):
    """0x423C70 builds the key+record pair the insert copies."""
    pair = h.alloc(PAIR_SIZE, bytes([0x5A]) * PAIR_SIZE)
    key = h.alloc(0x1C, bytes(0x1C))
    record = h.alloc(RECORD_SIZE, bytes(RECORD_SIZE))

    def setup(h):
        _put_str(h, key, b'the-key')
        _put_record(h, record, b'r', 0x33)

    diffs = h.compare(BUILD_PAIR, args=[key, record], regs={UC_X86_REG_ECX: pair}, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(BUILD_PAIR, args=[key, record], regs={UC_X86_REG_ECX: pair})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != pair:
        return ['returned %#x, not the pair' % res['eax']]
    if _get_str(h, pair) != b'the-key':
        return ['the pair key is %r' % _get_str(h, pair)]
    diffs = _check_record(h, pair + PAIR_VALUE, b'r', 0x5A)
    if diffs:
        return [diffs]
    return []


def test_copy_record_pair(h):
    """0x423C10 copies a pair (the node's key copy does this)."""
    src = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    dst = h.alloc(PAIR_SIZE, bytes([0x5A]) * PAIR_SIZE)

    def setup(h):
        _put_pair(h, src, b'old-key', b'c')

    diffs = h.compare(COPY_PAIR, args=[src], regs={UC_X86_REG_ECX: dst}, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(COPY_PAIR, args=[src], regs={UC_X86_REG_ECX: dst})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != dst:
        return ['returned %#x, not the pair' % res['eax']]
    if _get_str(h, dst) != b'old-key':
        return ['the pair key is %r' % _get_str(h, dst)]
    diffs = _check_record(h, dst + PAIR_VALUE, b'c', 0x5A)
    if diffs:
        return [diffs]
    return []


def test_destroy_record_pair(h):
    """0x420AE0 releases the pair: the record first, then the key."""
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))

    def setup(h):
        _put_pair(h, pair, b'some-key', b'x')

    diffs = h.compare(DESTROY_PAIR, regs={UC_X86_REG_ECX: pair}, setup=setup, ret=None)
    if diffs:
        return diffs
    return []


def test_add_record_map_size(h):
    """0x422410 grows the map size field of the library's view (at +08)."""
    view = h.alloc(0x10, bytes(0x10))

    def setup(h):
        h.uc.mem_write(view + 8, struct.pack('<I', 5))

    diffs = h.compare(ADD_MAP_SIZE, args=[3], regs={UC_X86_REG_ECX: view}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(ADD_MAP_SIZE, args=[3], regs={UC_X86_REG_ECX: view})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, view + 8) != 8:
        return ['the size became %d' % _u32(h, view + 8)]
    return []
