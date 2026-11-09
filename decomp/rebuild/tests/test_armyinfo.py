"""CReadArmyInfo: the "Army" table of the global Lua chunk.  The troop builder and record operations
(0x491A90 ... 0x492210), the pair/node the map stores (0x491FB0 ... 0x4924B0), the army map's helpers
(0x4925A0 ... 0x492D70), the singleton's lifetime (0x492CD0 / 0x492E40 / 0x492EA0) and the loader (0x492EC0).

The records are plain layouts the original builds in raw storage; uninitialised value fields come from the
caller's stack, so the tests that compare such a record zero the stack first (the harness starts both runs from
the same snapshot).  The Lua-facing tests patch the nScript wrappers with small stubs, as the npc/render tests do.
"""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

from difftest import STACK, STACK_SIZE

BUILD_TROOP = 0x00491A90
TROOP_CTOR = 0x00491BF0
DESTROY_TROOPS = 0x00491CF0
VECTOR_COPY = 0x00491D80
INFO_COPY = 0x00491EE0
INFO_CTOR = 0x00491F30
INFO_DTOR = 0x00491F50
PAIR_DTOR = 0x00491FB0
PAIR_CTOR = 0x00492000
PAIR_COPY = 0x00492090
INFO_ASSIGN = 0x00492130
INFO_READ = 0x00492210
INFO_FROM_TABLE = 0x00492450
CREATE_NODE = 0x004924B0
CLEAR_LIST = 0x004925A0
INIT_MAP = 0x00492950
INSERT_NODE = 0x004929D0
INDEX = 0x00492D70
LOADER_CTOR = 0x00492E40
LOADER_DTOR = 0x00492CD0
DELETE_LOADER = 0x00492EA0
LOAD = 0x00492EC0

LUA_ROOT = 0x005608F0
LUA_FIELD = 0x00561830
LUA_FIELD_STRING = 0x00561520
LUA_FIELD_NUMBER = 0x005613A0
LUA_ITER = 0x00561C10
LUA_TABLE = 0x00561270
LUA_ADVANCE = 0x00560100
DO_FILE = 0x00432620

ARMY_VFT = 0x0060B914
CLASS_VFT = 0x0060FF4C
SINGLETON_VFT = 0x0060FF2C

TROOP_SIZE = 0x20
TROOP_QN = 0x1C
VECTOR_SIZE = 0x10
INFO_SIZE = 0x2C
PAIR_SIZE = 0x48
NODE_SIZE = 0x50
MAP_SIZE = 0x28
OBJECT_SIZE = 0x38

INFO_X = 0x04
INFO_FLAG = 0x10
INFO_FIELD14 = 0x14
INFO_TROOPS = 0x18
INFO_VALUE = 0x28
PAIR_VALUE = 0x1C
NODE_KEY = 0x08
NODE_VALUE = 0x24        # the record inside the node (+08 pair, +1C army)
STUB_FLAG = 0x30
BUCKETS = 9
NUMBER_STEP = 2.0


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


def _put_troop(h, troop, creature, qn):
    _put_str(h, troop, creature)
    h.uc.mem_write(troop + TROOP_QN, struct.pack('<i', qn))


def _check_troop(h, troop, creature, qn):
    if _get_str(h, troop) != creature:
        return 'the creature is %r, wanted %r' % (_get_str(h, troop), creature)
    if struct.unpack('<i', h.uc.mem_read(troop + TROOP_QN, 4))[0] != qn:
        return 'qn is %d' % struct.unpack('<i', h.uc.mem_read(troop + TROOP_QN, 4))[0]
    return None


def _put_vector(h, vector, buffer, count):
    h.uc.mem_write(vector, struct.pack('<IIII', 0, buffer, buffer + count * TROOP_SIZE,
                                       buffer + count * TROOP_SIZE))


def _put_record(h, record, x=0.0, y=0.0, z=0.0, flag=0, field14=0, buffer=0, count=0, value=0):
    h.uc.mem_write(record, struct.pack('<I3fB3xI', ARMY_VFT, x, y, z, flag, field14))
    _put_vector(h, record + INFO_TROOPS, buffer, count)
    h.uc.mem_write(record + INFO_VALUE, struct.pack('<I', value))


def _check_record(h, record, x, y, z, flag, field14):
    fields = struct.unpack('<3fB', h.uc.mem_read(record + INFO_X, 13))
    if fields != (x, y, z, flag):
        return 'the fields are %r' % (fields,)
    if struct.unpack('<i', h.uc.mem_read(record + INFO_FIELD14, 4))[0] != field14:
        return 'the int is %d' % struct.unpack('<i', h.uc.mem_read(record + INFO_FIELD14, 4))[0]
    return None


def _put_pair(h, pair, name, **record):
    h.uc.mem_write(pair, bytes([0xA5]) * PAIR_SIZE)
    _put_str(h, pair, name)
    _put_record(h, pair + PAIR_VALUE, **record)


def _make_troops(h, troops):
    buffer = h.alloc(len(troops) * TROOP_SIZE, bytes(len(troops) * TROOP_SIZE))
    for i, (creature, qn) in enumerate(troops):
        _put_troop(h, buffer + i * TROOP_SIZE, creature, qn)
    return buffer


def _put_object(h, addr, vftable, refcount, kind=0):
    h.uc.mem_write(addr, bytes(OBJECT_SIZE))
    h.uc.mem_write(addr, struct.pack('<III', vftable, refcount, kind))
    _put_str(h, addr + 0x10, b'')


def _release_stub(h):
    """slot 0: record the flag the caller pushed at object+0x30 (ret 4)"""
    return h.alloc(16, bytes.fromhex('8b442404 884130 c20400'))


def _vtable(h, stub):
    return h.alloc(4, struct.pack('<I', stub))


def _patch(h, addr, code, saved):
    saved.append((addr, bytes(h.uc.mem_read(addr, len(code)))))
    h.uc.mem_write(addr, code)
    h.uc.ctl_remove_cache(addr, addr + len(code))


def _restore(h, saved):
    for addr, code in reversed(saved):
        h.uc.mem_write(addr, code)
        h.uc.ctl_remove_cache(addr, addr + len(code))


def _import_call(h, predicate):
    for fake, (_, name) in h.imp_by_addr.items():
        if predicate(name):
            return fake
    raise RuntimeError('import not found')


def _ret(n):
    return b'\xc3' if n == 0 else b'\xc2' + struct.pack('<H', n)


def _stub_const(h, saved, addr, value, retpop):
    _patch(h, addr, b'\xb8' + struct.pack('<I', value) + _ret(retpop), saved)


def _stub_selector(h, saved, addr, match, if_equal, otherwise, retpop):
    """if ECX == match, EAX = if_equal, else EAX = otherwise"""
    code = (b'\x81\xf9' + struct.pack('<I', match)
            + b'\xb8' + struct.pack('<I', otherwise)
            + b'\x75\x05'
            + b'\xb8' + struct.pack('<I', if_equal)
            + _ret(retpop))
    _patch(h, addr, code, saved)


def _stub_text(h, saved, text):
    """0x561520: build the caller's out string from a fixed text through the MSVC string ctor (ret 8)"""
    block = h.alloc(len(text) + 1, text + b'\0')
    ctor_cstr = _import_call(h, lambda n: n.startswith('??0?$basic_string')
                             and n.endswith('QAE@PBD@Z'))
    code = (b'\x68' + struct.pack('<I', block)          # push the text
            + b'\x8b\x4c\x24\x08'                       # ecx = [esp+8] = the out string
            + b'\xb8' + struct.pack('<I', ctor_cstr)    # the import pops its text argument
            + b'\xff\xd0'
            + b'\x8b\x44\x24\x04'                       # return the out string
            + b'\xc2\x08\x00')
    _patch(h, LUA_FIELD_STRING, code, saved)


def _stub_number(h, saved, value):
    const = h.alloc(4, struct.pack('<f', value))
    _patch(h, LUA_FIELD_NUMBER, b'\xd9\x05' + struct.pack('<I', const) + b'\xc2\x04\x00', saved)


def _stub_table(h, saved):
    """0x561270: the freshly allocated object becomes the current value (count 1, a table)"""
    _patch(h, LUA_TABLE,
           b'\xc7\x41\x04\x01\x00\x00\x00'
           + b'\xc7\x41\x08\x05\x00\x00\x00'
           + b'\x8b\xc1'
           + b'\xc2\x04\x00', saved)


def _stub_advance(h, saved):
    """0x560100: the next value is not a table, so every loop runs once"""
    _patch(h, LUA_ADVANCE, b'\xc7\x41\x08\x03\x00\x00\x00' + b'\xc3', saved)


def _stub_troop_read(h, saved, text=b'griffin', number=7.0):
    _stub_text(h, saved, text)
    _stub_number(h, saved, number)


def _init_map(h, mapobj):
    """an empty army map: a self-linked sentinel, no records and nine sentinel buckets"""
    sentinel = h.alloc(NODE_SIZE, bytes(NODE_SIZE))
    buckets = h.alloc(BUCKETS * 4, struct.pack('<%dI' % BUCKETS, *([sentinel] * BUCKETS)))
    h.uc.mem_write(sentinel, struct.pack('<II', sentinel, sentinel))
    h.uc.mem_write(mapobj + 0x08, struct.pack('<II', sentinel, 0))
    h.uc.mem_write(mapobj + 0x14, struct.pack('<III', buckets, buckets + BUCKETS * 4, buckets + BUCKETS * 4))
    h.uc.mem_write(mapobj + 0x20, struct.pack('<II', 1, 1))
    return sentinel


def _insert_key(h, mapobj, name):
    """setup helper: insert a default record through the translated operator[] and return its record"""
    key = h.alloc(0x1C, bytes(0x1C))
    _put_str(h, key, name)
    res = h.call(INDEX, args=[key], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        raise RuntimeError('operator[] faulted: %s' % res['fault'])
    return res['eax']


def test_build_army_troop(h):
    """0x491A90 fills the name from 0x561520 and truncates the number from 0x5613A0."""
    troop = h.alloc(TROOP_SIZE, bytes(TROOP_SIZE))
    slot = h.alloc(4, struct.pack('<I', 0x12345678))
    saved = []
    state = {}

    def setup(h):
        _stub_troop_read(h, saved, b'griffin', 7.0)
        h.uc.mem_write(troop, bytes(TROOP_SIZE))
        state['heap'] = h.heap_ptr

    try:
        diffs = h.compare(BUILD_TROOP, args=[slot], regs={UC_X86_REG_ECX: troop}, setup=setup, ret=None)
        if diffs:
            return diffs
        h.heap_ptr = state['heap']
        res = h.call(BUILD_TROOP, args=[slot], regs={UC_X86_REG_ECX: troop})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
    finally:
        _restore(h, saved)
    error = _check_troop(h, troop, b'griffin', 7)
    return [error] if error else []


def test_init_army_troop(h):
    """0x491BF0 builds the empty name, then the fields of the value; it returns this."""
    troop = h.alloc(TROOP_SIZE, bytes(TROOP_SIZE))
    slot = h.alloc(4, struct.pack('<I', 0x12345678))
    saved = []
    state = {}

    def setup(h):
        _stub_troop_read(h, saved, b'wolf', 3.0)
        h.uc.mem_write(troop, bytes(TROOP_SIZE))
        state['heap'] = h.heap_ptr

    try:
        diffs = h.compare(TROOP_CTOR, args=[slot], regs={UC_X86_REG_ECX: troop}, setup=setup, ret=None)
        if diffs:
            return diffs
        h.heap_ptr = state['heap']
        res = h.call(TROOP_CTOR, args=[slot], regs={UC_X86_REG_ECX: troop})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != troop:
            return ['returned %#x, not this %#x' % (res['eax'], troop)]
    finally:
        _restore(h, saved)
    error = _check_troop(h, troop, b'wolf', 3)
    return [error] if error else []


def test_destroy_army_troops(h):
    """0x491CF0 destroys the troops' names, frees the buffer and clears the three pointers."""
    vector = h.alloc(VECTOR_SIZE, bytes(VECTOR_SIZE))
    state = {}

    def setup(h):
        buffer = h.alloc(2 * TROOP_SIZE, bytes(2 * TROOP_SIZE))
        _put_troop(h, buffer, b'alpha', 1)
        _put_troop(h, buffer + TROOP_SIZE, b'beta', 2)
        _put_vector(h, vector, buffer, 2)
        h.uc.mem_write(vector, struct.pack('<I', 0x5A))
        state['heap'] = h.heap_ptr

    diffs = h.compare(DESTROY_TROOPS, regs={UC_X86_REG_ECX: vector}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(DESTROY_TROOPS, regs={UC_X86_REG_ECX: vector})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<III', h.uc.mem_read(vector + 4, 12)) != (0, 0, 0):
        return ['the pointers are %r' % (h.uc.mem_read(vector + 4, 12),)]
    if h.uc.mem_read(vector, 1) != b'\x5A':
        return ['the allocator byte changed']
    return []


def test_copy_army_troop_vector(h):
    """0x491D80 copies the range into a buffer of its own; the allocator stays."""
    source = h.alloc(VECTOR_SIZE, bytes(VECTOR_SIZE))
    dest = h.alloc(VECTOR_SIZE, bytes(VECTOR_SIZE))
    state = {}

    def setup(h):
        buffer = _make_troops(h, [(b'wolf', 4), (b'bear', 5)])
        _put_vector(h, source, buffer, 2)
        h.uc.mem_write(dest, struct.pack('<I', 0x5A) + bytes(12))
        state['heap'] = h.heap_ptr

    diffs = h.compare(VECTOR_COPY, args=[source], regs={UC_X86_REG_ECX: dest}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(VECTOR_COPY, args=[source], regs={UC_X86_REG_ECX: dest})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != dest:
        return ['returned %#x, not this %#x' % (res['eax'], dest)]
    _, begin, end, limit = struct.unpack('<4I', h.uc.mem_read(dest, 16))
    if begin == 0 or end != begin + 2 * TROOP_SIZE or limit < end:
        return ['the copy is %r' % ((begin, end, limit),)]
    for i, (creature, qn) in enumerate(((b'wolf', 4), (b'bear', 5))):
        error = _check_troop(h, begin + i * TROOP_SIZE, creature, qn)
        if error:
            return [error]
    return []


def test_init_army_info(h):
    """0x491F30 tags the record and drops only the object slots; the values and the allocator stay."""
    info = h.alloc(INFO_SIZE, bytes([0x5A]) * INFO_SIZE)

    diffs = h.compare(INFO_CTOR, regs={UC_X86_REG_ECX: info}, setup=None, ret=None)
    if diffs:
        return diffs
    res = h.call(INFO_CTOR, regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, info) != ARMY_VFT:
        return ['the tag is %#x' % _u32(h, info)]
    if struct.unpack('<IIII', h.uc.mem_read(info + 0x1C, 16)) != (0, 0, 0, 0):
        return ['the object slots are %r' % (h.uc.mem_read(info + 0x1C, 16),)]
    if bytes(h.uc.mem_read(info + 4, 0x18)) != bytes([0x5A]) * 0x18:
        return ['the value fields and the allocator were written']
    return []


def test_copy_army_info(h):
    """0x491EE0 copies the five fields, deep-copies the troops and retains the value."""
    source = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    dest = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        value = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, value, _vtable(h, stub), 2)
        buffer = _make_troops(h, [(b'wolf', 4)])
        _put_record(h, source, 1.5, 2.5, 3.5, 6, 9, buffer, 1, value)
        h.uc.mem_write(dest, bytes(INFO_SIZE))
        state['heap'] = h.heap_ptr
        state['value'] = value

    diffs = h.compare(INFO_COPY, args=[source], regs={UC_X86_REG_ECX: dest}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INFO_COPY, args=[source], regs={UC_X86_REG_ECX: dest})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != dest:
        return ['returned %#x, not this %#x' % (res['eax'], dest)]
    if _u32(h, dest) != ARMY_VFT:
        return ['the tag is %#x' % _u32(h, dest)]
    error = _check_record(h, dest, 1.5, 2.5, 3.5, 6, 9)
    if error:
        return [error]
    _, begin, end, limit = struct.unpack('<4I', h.uc.mem_read(dest + INFO_TROOPS, 16))
    if begin == 0 or end != begin + TROOP_SIZE or limit < end:
        return ['the troop copy is %r' % ((begin, end, limit),)]
    error = _check_troop(h, begin, b'wolf', 4)
    if error:
        return [error]
    if _u32(h, dest + INFO_VALUE) != state['value']:
        return ['the value is %#x' % _u32(h, dest + INFO_VALUE)]
    if _u32(h, state['value'] + 4) != 3:
        return ['the value count is %d' % _u32(h, state['value'] + 4)]
    return []


def test_destroy_army_info(h):
    """0x491F50 drops the value (the last reference is destroyed) and frees the troops."""
    info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        value = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, value, _vtable(h, stub), 1)
        buffer = _make_troops(h, [(b'alpha', 1)])
        _put_record(h, info, value=value, buffer=buffer, count=1)
        state['heap'] = h.heap_ptr
        state['value'] = value

    diffs = h.compare(INFO_DTOR, regs={UC_X86_REG_ECX: info}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INFO_DTOR, regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, state['value'] + 4) != 0:
        return ['the value count is %d' % _u32(h, state['value'] + 4)]
    if h.uc.mem_read(state['value'] + STUB_FLAG, 1) != b'\x01':
        return ['the value was not destroyed with flag 1']
    if struct.unpack('<III', h.uc.mem_read(info + INFO_TROOPS + 4, 12)) != (0, 0, 0):
        return ['the troops were not cleared']
    return []


def test_assign_army_info(h):
    """0x492130 copies the fields and assigns the troops; the new value is kept, the old one dropped."""
    dest = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    source = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        vftable = _vtable(h, stub)
        old = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        new = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, old, vftable, 2)
        _put_object(h, new, vftable, 1)
        old_buffer = _make_troops(h, [(b'old', 1)])
        new_buffer = _make_troops(h, [(b'new', 2)])
        _put_record(h, dest, 0.0, 0.0, 0.0, 0, 0, old_buffer, 1, old)
        _put_record(h, source, 4.5, 5.5, 6.5, 8, 10, new_buffer, 1, new)
        state['heap'] = h.heap_ptr
        state['old'] = old
        state['new'] = new

    diffs = h.compare(INFO_ASSIGN, args=[source], regs={UC_X86_REG_ECX: dest}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INFO_ASSIGN, args=[source], regs={UC_X86_REG_ECX: dest})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    error = _check_record(h, dest, 4.5, 5.5, 6.5, 8, 10)
    if error:
        return [error]
    if _u32(h, dest + INFO_VALUE) != state['new']:
        return ['the value is %#x' % _u32(h, dest + INFO_VALUE)]
    if _u32(h, state['new'] + 4) != 2:
        return ['the new value count is %d' % _u32(h, state['new'] + 4)]
    if _u32(h, state['old'] + 4) != 1:
        return ['the old value count is %d' % _u32(h, state['old'] + 4)]
    begin = _u32(h, dest + INFO_TROOPS + 4)
    if begin == 0 or _get_str(h, begin) != b'new':
        return ['the troops were not assigned']
    return []


def test_build_army_pair(h):
    """0x492000 builds the key+record pair the map copies into a node."""
    pair = h.alloc(PAIR_SIZE, bytes([0x5A]) * PAIR_SIZE)
    key = h.alloc(0x1C, bytes(0x1C))
    record = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        value = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, value, _vtable(h, stub), 1)
        buffer = _make_troops(h, [(b'wolf', 2)])
        _put_str(h, key, b'the-key')
        _put_record(h, record, 1.25, 2.25, 3.25, 4, 5, buffer, 1, value)
        state['heap'] = h.heap_ptr
        state['value'] = value

    diffs = h.compare(PAIR_CTOR, args=[key, record], regs={UC_X86_REG_ECX: pair}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(PAIR_CTOR, args=[key, record], regs={UC_X86_REG_ECX: pair})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != pair:
        return ['returned %#x, not the pair' % res['eax']]
    if _get_str(h, pair) != b'the-key':
        return ['the pair key is %r' % _get_str(h, pair)]
    error = _check_record(h, pair + PAIR_VALUE, 1.25, 2.25, 3.25, 4, 5)
    if error:
        return [error]
    begin = _u32(h, pair + PAIR_VALUE + INFO_TROOPS + 4)
    if begin == 0 or _get_str(h, begin) != b'wolf':
        return ['the troops were not copied']
    if _u32(h, pair + PAIR_VALUE + INFO_VALUE) != state['value']:
        return ['the pair value is %#x' % _u32(h, pair + PAIR_VALUE + INFO_VALUE)]
    if _u32(h, state['value'] + 4) != 2:
        return ['the value count is %d' % _u32(h, state['value'] + 4)]
    return []


def test_copy_army_pair(h):
    """0x492090 copies the key and the record and retains the value."""
    source = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    dest = h.alloc(PAIR_SIZE, bytes([0x5A]) * PAIR_SIZE)
    state = {}

    def setup(h):
        stub = _release_stub(h)
        value = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, value, _vtable(h, stub), 1)
        buffer = _make_troops(h, [(b'bear', 3)])
        _put_pair(h, source, b'pair-key', x=7.0, y=8.0, z=9.0, flag=2, field14=3,
                  buffer=buffer, count=1, value=value)
        state['heap'] = h.heap_ptr
        state['value'] = value

    diffs = h.compare(PAIR_COPY, args=[source], regs={UC_X86_REG_ECX: dest}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(PAIR_COPY, args=[source], regs={UC_X86_REG_ECX: dest})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != dest:
        return ['returned %#x, not this %#x' % (res['eax'], dest)]
    if _get_str(h, dest) != b'pair-key':
        return ['the key is %r' % _get_str(h, dest)]
    error = _check_record(h, dest + PAIR_VALUE, 7.0, 8.0, 9.0, 2, 3)
    if error:
        return [error]
    begin = _u32(h, dest + PAIR_VALUE + INFO_TROOPS + 4)
    if begin == 0 or _get_str(h, begin) != b'bear':
        return ['the troops were not copied']
    if _u32(h, dest + PAIR_VALUE + INFO_VALUE) != state['value']:
        return ['the value is %#x' % _u32(h, dest + PAIR_VALUE + INFO_VALUE)]
    if _u32(h, state['value'] + 4) != 2:
        return ['the value count is %d' % _u32(h, state['value'] + 4)]
    return []


def test_destroy_army_pair(h):
    """0x491FB0 destroys the record first and the key last."""
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        value = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, value, _vtable(h, stub), 1)
        buffer = _make_troops(h, [(b'alpha', 1)])
        _put_pair(h, pair, b'gone', buffer=buffer, count=1, value=value)
        state['heap'] = h.heap_ptr
        state['value'] = value

    diffs = h.compare(PAIR_DTOR, regs={UC_X86_REG_ECX: pair}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(PAIR_DTOR, regs={UC_X86_REG_ECX: pair})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, state['value'] + 4) != 0:
        return ['the value count is %d' % _u32(h, state['value'] + 4)]
    if h.uc.mem_read(state['value'] + STUB_FLAG, 1) != b'\x01':
        return ['the value was not destroyed with flag 1']
    if struct.unpack('<III', h.uc.mem_read(pair + PAIR_VALUE + INFO_TROOPS + 4, 12)) != (0, 0, 0):
        return ['the troops were not cleared']
    # the harness's std::string destructor is a no-op, so the key's storage is the only observable part; the
    # destruction order itself is covered by the byte comparison.
    return []


def test_create_army_node(h):
    """0x4924B0 allocates a node and copies the pair behind its links."""
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    state = {}

    def setup(h):
        _put_pair(h, pair, b'node-key', x=1.0, y=2.0, z=3.0, flag=4, field14=5)
        state['heap'] = h.heap_ptr

    diffs = h.compare(CREATE_NODE, args=[0x11111111, 0x22222222, pair], setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
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
    error = _check_record(h, node + NODE_VALUE, 1.0, 2.0, 3.0, 4, 5)
    return [error] if error else []


def test_init_army_map(h):
    """0x492950: the allocator byte, the node sentinel, size 0 and nine buckets pointing at it."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    allocator = h.alloc(4, b'\x5A\x00\x00\x00')
    args = [allocator, allocator]

    diffs = h.compare(INIT_MAP, args=args, regs={UC_X86_REG_ECX: mapobj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(INIT_MAP, args=args, regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != mapobj:
        return ['returned %#x, not this' % res['eax']]
    if _u32(h, mapobj) & 0xFF != 0x5A:
        return ['the allocator byte is %02X' % (_u32(h, mapobj) & 0xFF)]
    sentinel = _u32(h, mapobj + 0x08)
    if _u32(h, mapobj + 0x0C) != 0:
        return ['size %d' % _u32(h, mapobj + 0x0C)]
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
    return []


def test_clear_army_map_list(h):
    """0x4925A0 empties the map: the nodes' values and troops are destroyed; the list starts over."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    sentinel = h.alloc(NODE_SIZE, bytes(NODE_SIZE))
    state = {}

    def setup(h):
        nodes = [h.alloc(NODE_SIZE, bytes(NODE_SIZE)) for _ in range(2)]
        for node, key in zip(nodes, (b'alpha', b'beta')):
            buffer = _make_troops(h, [(b'unit-of-' + key, 1)])
            _put_str(h, node + NODE_KEY, key)
            _put_record(h, node + NODE_VALUE, buffer=buffer, count=1)
        ring = [sentinel] + nodes + [sentinel]
        for here, following in zip(ring, ring[1:]):
            h.uc.mem_write(here, struct.pack('<I', following))
        for here, previous in zip(ring[1:], ring):
            h.uc.mem_write(here + 4, struct.pack('<I', previous))
        h.uc.mem_write(mapobj + 8, struct.pack('<I', sentinel))
        h.uc.mem_write(mapobj + 0xC, struct.pack('<I', len(nodes)))
        state['heap'] = h.heap_ptr

    diffs = h.compare(CLEAR_LIST, regs={UC_X86_REG_ECX: mapobj + 4}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(CLEAR_LIST, regs={UC_X86_REG_ECX: mapobj + 4})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return ['the node list was not emptied']
    if _u32(h, mapobj + 0x0C) != 0:
        return ['size %d' % _u32(h, mapobj + 0x0C)]
    return []


def _zero_stack(h):
    h.uc.mem_write(STACK, bytes(STACK_SIZE))


def test_army_map_index_hit(h):
    """0x492D70 returns &node->value of a key already in the map and leaves the map alone."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    lookup = h.alloc(0x1C, bytes(0x1C))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        _insert_key(h, mapobj, b'known')
        _put_str(h, lookup, b'known')
        state['heap'] = h.heap_ptr

    diffs = h.compare(INDEX, args=[lookup], regs={UC_X86_REG_ECX: mapobj}, setup=setup, ret='eax')
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(INDEX, args=[lookup], regs={UC_X86_REG_ECX: mapobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    record = res['eax']
    if record == mapobj or not record:
        return ['returned %#x' % record]
    if _get_str(h, record - NODE_VALUE + NODE_KEY) != b'known':
        return ['the record is not the key\'s']
    if _u32(h, mapobj + 0x0C) != 1:
        return ['the map size changed to %d' % _u32(h, mapobj + 0x0C)]
    return []


def test_army_map_index_insert(h):
    """0x492D70 inserts a node holding a default record for a missing key and returns its value."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    key = h.alloc(0x1C, bytes(0x1C))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        _put_str(h, key, b'new-army')
        _zero_stack(h)
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
    if (_u32(h, node), _u32(h, node + 4)) != (sentinel, sentinel):
        return ['the node does not sit before the sentinel']
    if (_u32(h, sentinel), _u32(h, sentinel + 4)) != (node, node):
        return ['the sentinel does not link to the node']
    if _u32(h, _u32(h, mapobj + 0x14)) != node:
        return ['the first bucket does not start at the node']
    if _get_str(h, node + NODE_KEY) != b'new-army':
        return ['the key is %r' % _get_str(h, node + NODE_KEY)]
    if _u32(h, record) != ARMY_VFT:
        return ['the record is not tagged']
    if struct.unpack('<3fB', h.uc.mem_read(record + INFO_X, 13)) != (0.0, 0.0, 0.0, 0):
        return ['the uninitialised fields were not copied as zero']
    if struct.unpack('<i', h.uc.mem_read(record + INFO_FIELD14, 4))[0] != 0:
        return ['the int is not zero']
    return []


def test_army_map_index_growth(h):
    """The insert that fills the last bucket rehashes the map: the mask grows to 15 and every node stays."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    key = h.alloc(0x1C, bytes(0x1C))
    names = tuple(b'key%02d' % i for i in range(32))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        for name in names:
            _insert_key(h, mapobj, name)
        _put_str(h, key, b'extra')
        _zero_stack(h)
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


def test_insert_army_node(h):
    """0x4929D0 links a new node before its lower bound and reports it."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    result = h.alloc(8, bytes(8))
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        for name in (b'alpha', b'beta', b'gamma'):
            _insert_key(h, mapobj, name)
        _put_pair(h, pair, b'delta', x=3.0, flag=1)
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
    error = _check_record(h, node + NODE_VALUE, 3.0, 0.0, 0.0, 1, 0)
    if error:
        return [error]
    if _u32(h, mapobj + 0x0C) != 4:
        return ['the map size is %d' % _u32(h, mapobj + 0x0C)]
    if _u32(h, _u32(h, node + 4)) != node or _u32(h, _u32(h, node) + 4) != node:
        return ['the node links are inconsistent']
    return []


def test_insert_army_node_duplicate(h):
    """0x4929D0 returns the existing node of a duplicate key and does not allocate."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    result = h.alloc(8, bytes(8))
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        for name in (b'alpha', b'beta', b'gamma'):
            _insert_key(h, mapobj, name)
        _put_pair(h, pair, b'beta')
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


def test_insert_army_node_growth(h):
    """0x4929D0 rehashes when the last bucket is full, growing the bucket vector to seventeen slots."""
    mapobj = h.alloc(MAP_SIZE, bytes(MAP_SIZE))
    result = h.alloc(8, bytes(8))
    pair = h.alloc(PAIR_SIZE, bytes(PAIR_SIZE))
    names = tuple(b'key%02d' % i for i in range(32))
    state = {}

    def setup(h):
        _init_map(h, mapobj)
        for name in names:
            _insert_key(h, mapobj, name)
        _put_pair(h, pair, b'extra')
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


def _fill_empty(h, obj):
    h.uc.mem_write(obj, struct.pack('<I', CLASS_VFT))
    alloc = h.alloc(1, b'\0')
    h.call(INIT_MAP, args=[alloc, alloc], regs={UC_X86_REG_ECX: obj + 0x04})


def test_loader_ctor(h):
    """0x492E40 tags the loader and initialises the map (the allocator byte is uninitialised stack)."""
    obj = h.alloc(0x2C, bytes(0x2C))
    diffs = h.compare(LOADER_CTOR, regs={UC_X86_REG_ECX: obj}, setup=_zero_stack, ret='eax')
    if diffs:
        return diffs
    res = h.call(LOADER_CTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['returned %#x, not this' % res['eax']]
    if _u32(h, obj) != CLASS_VFT:
        return ['the class vtable is not at +0']
    sentinel, size = struct.unpack('<II', h.uc.mem_read(obj + 0x0C, 8))
    mask, count = struct.unpack('<II', h.uc.mem_read(obj + 0x24, 8))
    if sentinel == 0 or size != 0 or mask != 1 or count != 1:
        return ['map: sentinel %#x size %d mask %d count %d' % (sentinel, size, mask, count)]
    return []


def test_loader_dtor(h):
    """0x492CD0 frees the buckets and the nodes and drops to the singleton vtable."""
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
    if _u32(h, obj) != SINGLETON_VFT:
        return ['the singleton vtable is not at +0 after the dtor']
    for off in (0x0C, 0x18, 0x1C, 0x20):
        if _u32(h, obj + off) != 0:
            return ['+0x%X is not cleared' % off]
    return []


def test_delete_loader(h):
    """0x492EA0 destroys the loader and deletes it only when flag 1 is set; it returns this."""
    diffs = []
    for flags in (0, 1):
        obj = h.alloc(0x2C, bytes(0x2C))
        state = {}

        def setup(h):
            _zero_stack(h)
            _fill_empty(h, obj)
            state['heap'] = h.heap_ptr

        diffs += h.compare(DELETE_LOADER, args=[flags], regs={UC_X86_REG_ECX: obj}, setup=setup, ret='eax')
        if diffs:
            return diffs
        h.heap_ptr = state['heap']
        res = h.call(DELETE_LOADER, args=[flags], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted for flag %d: %s' % (flags, res['fault'])]
        if res['eax'] != obj:
            diffs.append('flag %d returned %#x, not this %#x' % (flags, res['eax'], obj))
        if _u32(h, obj) != SINGLETON_VFT:
            diffs.append('flag %d did not run the dtor' % flags)
    return diffs


def _stub_read(h, saved, table, troops_table, iterator):
    """the wrappers Read drives: "troops" from any value, an iterator over the troops table, one value in it"""
    _stub_const(h, saved, LUA_FIELD, troops_table, 4)
    _stub_const(h, saved, LUA_ITER, iterator, 0)
    _stub_table(h, saved)
    _stub_advance(h, saved)
    _stub_troop_read(h, saved)


def test_init_army_info_from_table(h):
    """0x492450 tags the record, drops the slots and reads the value's "troops" table."""
    info = h.alloc(INFO_SIZE, bytes([0x5A]) * INFO_SIZE)
    table = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    _put_object(h, table, _vtable(h, _release_stub(h)), 1)
    troops_table = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    _put_object(h, troops_table, _vtable(h, _release_stub(h)), 1)
    iterator = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    _put_object(h, iterator, _vtable(h, _release_stub(h)), 1, kind=5)
    _put_str(h, iterator + 0x10, b'')
    saved = []
    state = {}

    def setup(h):
        _stub_read(h, saved, table, troops_table, iterator)
        state['heap'] = h.heap_ptr

    try:
        diffs = h.compare(INFO_FROM_TABLE, args=[table], regs={UC_X86_REG_ECX: info},
                          setup=setup, ret=None)
        if diffs:
            return diffs
        h.heap_ptr = state['heap']
        res = h.call(INFO_FROM_TABLE, args=[table], regs={UC_X86_REG_ECX: info})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != info:
            return ['returned %#x, not this' % res['eax']]
    finally:
        _restore(h, saved)
    if _u32(h, info) != ARMY_VFT:
        return ['the tag is %#x' % _u32(h, info)]
    _, begin, end, limit = struct.unpack('<4I', h.uc.mem_read(info + INFO_TROOPS, 16))
    if begin == 0 or end != begin + TROOP_SIZE or limit < end:
        return ['the troop vector is %r' % ((begin, end, limit),)]
    error = _check_troop(h, begin, b'griffin', 7)
    return [error] if error else []


def test_load_army_info(h):
    """0x492EC0 runs "armys", walks the global "Army" table and fills one record per value.

    The stubs make the table hold a single army: the iterator's key is "armyA" and its value's "troops" table
    holds one troop.  Read itself is the compiled function, so both runs share it."""
    info = h.alloc(0x2C, bytes(0x2C))
    lookup = h.alloc(0x1C, bytes(0x1C))
    saved = []
    state = {}

    def setup(h):
        root = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, root, _vtable(h, _release_stub(h)), 1)
        army_table = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, army_table, _vtable(h, _release_stub(h)), 1, kind=5)
        troops_table = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, troops_table, _vtable(h, _release_stub(h)), 1, kind=5)
        army_iterator = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, army_iterator, _vtable(h, _release_stub(h)), 1, kind=5)
        _put_str(h, army_iterator + 0x10, b'armyA')
        army_iterator_troops = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        _put_object(h, army_iterator_troops, _vtable(h, _release_stub(h)), 1, kind=5)
        _put_str(h, army_iterator_troops + 0x10, b'')

        _stub_const(h, saved, LUA_ROOT, root, 0)
        _stub_selector(h, saved, LUA_FIELD, root, army_table, troops_table, 4)
        _stub_selector(h, saved, LUA_ITER, army_table, army_iterator, army_iterator_troops, 0)
        _stub_table(h, saved)
        _stub_advance(h, saved)
        _stub_troop_read(h, saved, b'griffin', 7.0)
        _patch(h, h.symbols.get('?DoFile@CLuaWrapper@@QAEXPBD@Z', DO_FILE), _ret(4), saved)
        _put_str(h, lookup, b'armyA')
        h.uc.mem_write(info, bytes(0x2C))
        res = h.call(LOADER_CTOR, regs={UC_X86_REG_ECX: info})
        if res['fault']:
            raise RuntimeError('loader ctor faulted: %s' % res['fault'])
        _zero_stack(h)  # after the ctor: its frames would otherwise seed the record's uninitialised fields
        state['heap'] = h.heap_ptr

    try:
        diffs = h.compare(LOAD, regs={UC_X86_REG_ECX: info}, setup=setup, ret=None)
        if diffs:
            return diffs
        h.heap_ptr = state['heap']
        res = h.call(LOAD, regs={UC_X86_REG_ECX: info})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        found = h.call(INDEX, args=[lookup], regs={UC_X86_REG_ECX: info + 4})
        if found['fault']:
            return ['operator[] faulted: %s' % found['fault']]
    finally:
        _restore(h, saved)
    if _u32(h, info + 0x10) != 1:
        return ['the map size is %d' % _u32(h, info + 0x10)]
    record = found['eax']
    if _u32(h, record) != ARMY_VFT:
        return ['the record is not tagged']
    if _u32(h, record + INFO_VALUE) == 0:
        return ['the record value was not set']
    _, begin, end, limit = struct.unpack('<4I', h.uc.mem_read(record + INFO_TROOPS, 16))
    if begin == 0 or end != begin + TROOP_SIZE or limit < end:
        return ['the troop vector is %r' % ((begin, end, limit),)]
    error = _check_troop(h, begin, b'griffin', 7)
    return [error] if error else []
