"""CReadCursorDat: the cursor map of Cursors.dat.  Its sentinel (0x4A0750), constructor (0x4A07F0), clear
(0x4430D0), size guard (0x442EC0), node and pair builders (0x442FF0 / 0x442CE0), insert (0x443520) and
operator[] (0x4437E0), then the loader object (0x4A0910 / 0x4A0870).

The map is an FsHashMap (0x28 bytes) whose sentinel is a whole 0x48-byte CursorRecordNode:
{next; prev; std::string key; std::string text; unsigned x; unsigned y}, the value at +24."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

from difftest import STACK, STACK_SIZE

CREATE_SENTINEL = 0x004A0750
INIT_CURSOR_MAP = 0x004A07F0
CLEAR_CURSOR_NODES = 0x004430D0
ADD_MAP_SIZE = 0x00442EC0
CREATE_NODE = 0x00442FF0
BUILD_PAIR = 0x00442CE0
INSERT_NODE = 0x00443520
INDEX = 0x004437E0
LOADER_CTOR = 0x004A0910
LOADER_DTOR = 0x004A0870

VFT_CLASS = 0x0061005C
VFT_SINGLETON = 0x00610054

NODE_SIZE = 0x48
PAIR_SIZE = 0x40
PAIR_VALUE = 0x1C      # the record's offset inside the pair
NODE_KEY = 0x08
NODE_VALUE = 0x24      # the record's offset inside the node
RECORD_SIZE = 0x24
MAP_SIZE = 0x28
BUCKETS = 9


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


def _put_record(h, record, text, x=0, y=0):
    _put_str(h, record, text)
    h.uc.mem_write(record + 0x1C, struct.pack('<II', x, y))


def _check_record(h, record, text, x, y):
    if _get_str(h, record) != text:
        return 'the text is %r, wanted %r' % (_get_str(h, record), text)
    if struct.unpack('<II', h.uc.mem_read(record + 0x1C, 8)) != (x, y):
        return 'the numbers are %r' % (h.uc.mem_read(record + 0x1C, 8),)
    return None


def _put_pair(h, pair, name, text, x=0, y=0):
    h.uc.mem_write(pair, bytes([0xA5]) * PAIR_SIZE)
    _put_str(h, pair, name)
    _put_record(h, pair + PAIR_VALUE, text, x, y)


def _fill_stack(h):
    """The empty record's two numbers are never written before the map copies them; both runs must read the
    same stale bytes from their (differently laid out) frames for the copied node to compare equal."""
    h.uc.mem_write(STACK + STACK_SIZE - 0x8000, bytes([0x5A]) * 0x8000)


def _init_map(h, mapobj):
    """an empty cursor map: a self-linked sentinel, no records and nine sentinel buckets"""
    sentinel = h.alloc(NODE_SIZE, bytes(NODE_SIZE))
    buckets = h.alloc(BUCKETS * 4, struct.pack('<%dI' % BUCKETS, *([sentinel] * BUCKETS)))
    h.uc.mem_write(sentinel, struct.pack('<II', sentinel, sentinel))
    h.uc.mem_write(mapobj + 0x08, struct.pack('<II', sentinel, 0))
    h.uc.mem_write(mapobj + 0x14, struct.pack('<III', buckets, buckets + BUCKETS * 4, buckets + BUCKETS * 4))
    h.uc.mem_write(mapobj + 0x20, struct.pack('<II', 1, 1))
    return sentinel


def _insert_key(h, mapobj, name):
    """a setup helper: insert a default record through the translated operator[] and return its node"""
    key = h.alloc(0x1C, bytes(0x1C))
    _put_str(h, key, name)
    res = h.call(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        raise RuntimeError('operator[] faulted: %s' % res['fault'])
    return res['eax'] - NODE_VALUE


def test_cursor_node_sentinel(h):
    """0x4A0750 allocates a whole 0x48-byte cursor node linking to itself; the pair stays unconstructed."""
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


def test_init_cursor_map(h):
    """0x4A07F0: the allocator byte, the cursor-node sentinel, size 0 and nine buckets pointing at it."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    allocator = h.alloc(4, b'\x5A\x00\x00\x00')
    args = [allocator, allocator]
    diffs = h.compare(INIT_CURSOR_MAP, args=args, regs={UC_X86_REG_ECX: mapobj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(INIT_CURSOR_MAP, args=args, regs={UC_X86_REG_ECX: mapobj})
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
    if end - begin != BUCKETS * 4:
        return ['the bucket vector is %d bytes' % (end - begin)]
    for i in range(BUCKETS):
        if _u32(h, begin + 4 * i) != sentinel:
            return ['bucket slot %d is %08X' % (i, _u32(h, begin + 4 * i))]
    return None


def test_clear_cursor_nodes(h):
    """0x4430D0 empties the map: the nodes' pairs are destroyed and the list starts over."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    sentinel = h.alloc(NODE_SIZE, bytes(NODE_SIZE))
    nodes = [h.alloc(NODE_SIZE, bytes(NODE_SIZE)) for _ in range(2)]
    keys = [b'alpha', b'beta']

    def setup(h):
        ring = [sentinel] + nodes + [sentinel]
        for here, following in zip(ring, ring[1:]):
            h.uc.mem_write(here, struct.pack('<I', following))
        for here, previous in zip(ring[1:], ring):
            h.uc.mem_write(here + 4, struct.pack('<I', previous))
        for node, key in zip(nodes, keys):
            _put_str(h, node + NODE_KEY, key)
            _put_str(h, node + NODE_VALUE, b'text')
        h.uc.mem_write(mapobj + 8, struct.pack('<I', sentinel))
        h.uc.mem_write(mapobj + 0xC, struct.pack('<I', len(nodes)))

    diffs = h.compare(CLEAR_CURSOR_NODES, regs={UC_X86_REG_ECX: mapobj + 4}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(CLEAR_CURSOR_NODES, regs={UC_X86_REG_ECX: mapobj + 4})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return ['the node list was not emptied']
    if _u32(h, mapobj + 0xC) != 0:
        return ['size %d' % _u32(h, mapobj + 0xC)]
    return None


def test_add_cursor_map_size(h):
    """0x442EC0 grows the map size field of the library's view (at +08)."""
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


def test_create_cursor_node(h):
    """0x442FF0 allocates a node and copies the pair behind its links."""
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))

    def setup(h):
        _put_pair(h, pair, b'node-key', b'node-text', 11, 22)

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
    if _get_str(h, node + NODE_KEY) != b'node-key':
        return ['the key is %r' % _get_str(h, node + NODE_KEY)]
    error = _check_record(h, node + NODE_VALUE, b'node-text', 11, 22)
    if error:
        return [error]
    return []


def test_build_cursor_pair(h):
    """0x442CE0 builds the key+record pair operator[] copies into a node."""
    pair = h.alloc(PAIR_SIZE, bytes([0x5A]) * PAIR_SIZE)
    key = h.alloc(0x1C, bytes(0x1C))
    record = h.alloc(RECORD_SIZE, bytes(RECORD_SIZE))

    def setup(h):
        _put_str(h, key, b'the-key')
        _put_record(h, record, b'the-text', 7, 9)

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
    error = _check_record(h, pair + PAIR_VALUE, b'the-text', 7, 9)
    if error:
        return [error]
    return []


def test_cursor_map_index_hit(h):
    """0x4437E0 returns &node->value of a key already in the map and leaves the map alone."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    node = h.alloc(NODE_SIZE, bytes(NODE_SIZE))
    key = h.alloc(0x1C, bytes(0x1C))
    state = {}

    def setup(h):
        sentinel = _init_map(h, mapobj)
        h.uc.mem_write(_u32(h, mapobj + 0x14), struct.pack('<I', node))
        h.uc.mem_write(mapobj + 0x0C, struct.pack('<I', 1))
        h.uc.mem_write(sentinel, struct.pack('<II', node, node))
        h.uc.mem_write(node, struct.pack('<II', sentinel, sentinel))
        _put_str(h, key, b'known')
        _put_str(h, node + NODE_KEY, b'known')
        _put_record(h, node + NODE_VALUE, b'text', 1, 2)
        state['heap'] = h.heap_ptr

    diffs = h.compare(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != node + NODE_VALUE:
        return ['returned %#x, wanted &node->value %#x' % (res['eax'], node + NODE_VALUE)]
    if _u32(h, mapobj + 0x0C) != 1:
        return ['the map size changed to %d' % _u32(h, mapobj + 0x0C)]
    return []


def test_cursor_map_index_insert(h):
    """0x4437E0 inserts a node holding a default record for a missing key and returns its value."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    key = h.alloc(0x1C, bytes(0x1C))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        _put_str(h, key, b'new-cursor')
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
    node = record - NODE_VALUE
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
    if _get_str(h, node + NODE_KEY) != b'new-cursor':
        return ['the key is %r' % _get_str(h, node + NODE_KEY)]
    if _get_str(h, record) != b'':
        return ['the text is not empty']
    if struct.unpack('<II', h.uc.mem_read(record + 0x1C, 8)) != (0x5A5A5A5A,) * 2:
        return ['the uninitialised numbers were not copied from the temporary record']
    return []


def test_cursor_map_index_growth(h):
    """The insert that fills the last bucket rehashes the map: the mask grows to 15, the bucket vector doubles
    to seventeen slots and every node is still reachable."""
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
        if _get_str(h, found['eax'] - NODE_VALUE + NODE_KEY) != name:
            return ['the node of %r is not found after the growth' % name]
    return []


def test_insert_cursor_node(h):
    """0x443520 links a new node before its lower bound and reports it."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    result = h.alloc(8, bytes(8))
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        for name in (b'alpha', b'beta', b'gamma'):
            _insert_key(h, mapobj, name)
        _put_pair(h, pair, b'delta', b'd-text', 3, 4)
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
    if _get_str(h, node + NODE_KEY) != b'delta':
        return ['the node key is %r' % _get_str(h, node + NODE_KEY)]
    error = _check_record(h, node + NODE_VALUE, b'd-text', 3, 4)
    if error:
        return [error]
    if _u32(h, mapobj + 0x0C) != 4:
        return ['the map size is %d' % _u32(h, mapobj + 0x0C)]
    if _u32(h, _u32(h, node + 4)) != node or _u32(h, _u32(h, node) + 4) != node:
        return ['the node links are inconsistent']
    return []


def test_insert_cursor_node_duplicate(h):
    """0x443520 returns the existing node of a duplicate key and does not allocate."""
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
    if _get_str(h, _u32(h, result) + NODE_KEY) != b'beta':
        return ['the reported node is not the key\'s']
    if _u32(h, mapobj + 0x0C) != 3:
        return ['the map size is %d' % _u32(h, mapobj + 0x0C)]
    if h.heap_ptr != marker:
        return ['a duplicate insert allocated']
    return []


def test_insert_cursor_node_growth(h):
    """0x443520 rehashes when the last bucket is full, growing the bucket vector to seventeen slots."""
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


def _zero_stack(h):
    """The original hands the map ctor an uninitialised stack byte (the allocator, never read); the runs must
    read the same stale value for their maps to compare equal."""
    h.uc.mem_write(STACK + STACK_SIZE - 0x8000, bytes(0x8000))


def _fill_empty(h, obj):
    h.uc.mem_write(obj, struct.pack('<I', VFT_CLASS))
    alloc = h.alloc(1, b'\0')
    h.call(INIT_CURSOR_MAP, args=[alloc, alloc], regs={UC_X86_REG_ECX: obj + 0x04})


def test_cursordat_ctor(h):
    obj = h.alloc(0x2C, bytes(0x2C))
    diffs = h.compare(LOADER_CTOR, regs={UC_X86_REG_ECX: obj}, setup=_zero_stack, ret='eax')
    if diffs:
        return diffs
    res = h.call(LOADER_CTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['ctor returned %#x, not this' % res['eax']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_CLASS:
        return ['the class vtable is not at +0']
    sentinel, size = struct.unpack('<II', h.uc.mem_read(obj + 0x0C, 8))
    mask, count = struct.unpack('<II', h.uc.mem_read(obj + 0x24, 8))
    if sentinel == 0 or size != 0:
        return ['map: sentinel %#x size %d' % (sentinel, size)]
    if mask != 1 or count != 1:
        return ['map: mask %d count %d' % (mask, count)]
    return []


def test_cursordat_dtor(h):
    obj = h.alloc(0x2C, bytes(0x2C))

    def setup(h):
        _zero_stack(h)
        _fill_empty(h, obj)

    diffs = h.compare(LOADER_DTOR, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(LOADER_DTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_SINGLETON:
        return ['the singleton vtable is not at +0 after the dtor']
    for off in (0x0C, 0x18):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['+0x%X is not cleared' % off]
    for off in (0x1C, 0x20):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['map end/limit +0x%X is not cleared' % off]
    return []
