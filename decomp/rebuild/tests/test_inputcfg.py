"""CReadInputCfg: the input.cfg key/value list - the vector<CfgPair> machinery (0x4A0BA0 ... 0x4A17A0), the
0x38-byte records and the loader object (0x4A1650 / 0x4A1690 / 0x46EA50).

Load (0x4A1840) drives the dat lexer over an open CGameFile, so it is covered by the build replacement only,
not here.  0x4A1230 (the fill that reports the end position) is the containers' allocator template already
translated in src/fixed.

pair   = {std::string key; std::string value} (0x38 bytes, value at +1C)
vector = {allocator; begin; end; limit} (0x10 bytes, allocator kept as the owner left it)
"""
import struct
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EDX

PAIR = 0x38
VECTOR = 0x10

CONSTRUCT_PAIR = 0x004A0BA0
CAPACITY = 0x004A0C30
COUNT = 0x004A0C60
COPY_CONSTRUCT_PAIR = 0x004A0C90
ASSIGN_PAIR = 0x004A0D10
COPY_BACKWARD = 0x004A0D40
ALLOCATE = 0x004A0E10
FILL_ASSIGN = 0x004A0E80
COPY_CONSTRUCT = 0x004A0F80
BUY = 0x004A1020
FILL_CONSTRUCT = 0x004A1080
DESTROY = 0x004A1130
COPY_CONSTRUCT_END = 0x004A1300
DESTROY_VECTOR = 0x004A12C0
INSERT = 0x004A1330
INSERT_AT = 0x004A1710
PUSH = 0x004A17A0

CTOR = 0x004A1650
DTOR = 0x004A1690
DELETE = 0x004A1780
INSTANCE = 0x0046EA50

VFT_CLASS = 0x00610078
VFT_SINGLETON = 0x00610070
INSTANCE_GLOB = 0x006C9010


# --- memory helpers -----------------------------------------------------------------------------------

def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _pad(h, addr, size, byte=0x5A):
    h.uc.mem_write(addr, bytes([byte]) * size)


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


def _put_pair(h, pair, key, value):
    _put_str(h, pair, key)
    _put_str(h, pair + 0x1C, value)


def _get_pair(h, pair):
    return (_get_str(h, pair), _get_str(h, pair + 0x1C))


def _check_pair(h, pair, spec):
    key, value = _get_pair(h, pair)
    if (key, value) != spec:
        return '%r/%r, wanted %r/%r' % (key, value, spec[0], spec[1])
    return None


def _alloc_pairs(h, specs, capacity):
    size = PAIR * max(capacity, 1)
    block = h.alloc(size)
    _pad(h, block, size)
    for i, spec in enumerate(specs):
        _put_pair(h, block + i * PAIR, *spec)
    return block


def _fill_vector(h, vec, specs, capacity=None, allocator=0):
    """fill a 0x10 vector; the allocator dword is set as the owner left it"""
    h.uc.mem_write(vec, struct.pack('<I', allocator))
    if not specs and not capacity:
        h.uc.mem_write(vec + 4, struct.pack('<III', 0, 0, 0))
        return 0
    cap = len(specs) if capacity is None else capacity
    block = _alloc_pairs(h, specs, cap)
    h.uc.mem_write(vec + 4, struct.pack('<III', block, block + len(specs) * PAIR, block + cap * PAIR))
    return block


def _make_vector(h, specs, capacity=None, allocator=0):
    vec = h.alloc(VECTOR)
    block = _fill_vector(h, vec, specs, capacity, allocator)
    return vec, block


def _check_vector(h, vec, specs):
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if (end - begin) // PAIR != len(specs):
        return ['%d pairs in the vector, wanted %d' % ((end - begin) // PAIR, len(specs))]
    errors = []
    for i, spec in enumerate(specs):
        error = _check_pair(h, begin + i * PAIR, spec)
        if error:
            errors.append('pair %d: %s' % (i, error))
    return errors


def _both(h, fn, args=(), regs=None, ret=None):
    """compare the original entry with the replacement; when they agree, run the replacement once more"""
    diffs = h.compare(fn, args=args, regs=regs, ret=ret)
    if diffs:
        return diffs, None
    res = h.call(fn, args=args, regs=regs)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']], None
    return [], res


P0 = (b'first', b'one')
P1 = (b'second key that does not fit inline', b'a rather long value that does not fit either')
P2 = (b'third', b'')
V = (b'inserted', b'new value')


# --- the record ---------------------------------------------------------------------------------------

def test_construct_pair(h):
    """0x4A0BA0 makes the two empty texts and returns this."""
    pair = h.alloc(PAIR)
    _pad(h, pair, PAIR, 0xA5)
    diffs, res = _both(h, CONSTRUCT_PAIR, regs={UC_X86_REG_ECX: pair}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != pair:
        return ['returned %#x, not this' % res['eax']]
    if _get_pair(h, pair) != (b'', b''):
        return ['the pair is %r' % (_get_pair(h, pair),)]
    return []


def test_copy_construct_pair(h):
    """0x4A0C90 copies the key and the value and returns this."""
    source = h.alloc(PAIR)
    _pad(h, source, PAIR)
    _put_pair(h, source, *P1)
    dst = h.alloc(PAIR)
    _pad(h, dst, PAIR)
    diffs, res = _both(h, COPY_CONSTRUCT_PAIR, args=[source], regs={UC_X86_REG_ECX: dst}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst:
        return ['returned %#x, not this' % res['eax']]
    error = _check_pair(h, dst, P1)
    return [error] if error else []


def test_assign_pair(h):
    """0x4A0D10 assigns both texts and returns this."""
    source = h.alloc(PAIR)
    _pad(h, source, PAIR)
    _put_pair(h, source, *P1)
    dst = h.alloc(PAIR)
    _pad(h, dst, PAIR)
    _put_pair(h, dst, b'old key', b'an old value which is long enough to be on the heap')
    diffs, res = _both(h, ASSIGN_PAIR, args=[source], regs={UC_X86_REG_ECX: dst}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst:
        return ['returned %#x, not this' % res['eax']]
    error = _check_pair(h, dst, P1)
    return [error] if error else []


def test_destroy_pairs(h):
    """0x4A1130 destroys the value and then the key of every pair."""
    block = _alloc_pairs(h, [P0, P1], 2)
    diffs, res = _both(h, DESTROY, args=[block, block + 2 * PAIR], ret=None)
    return diffs


# --- the vector ---------------------------------------------------------------------------------------

def test_capacity(h):
    """0x4A0C30 is the spare capacity, zero for a vector that owns nothing."""
    empty = h.alloc(VECTOR)
    h.uc.mem_write(empty, bytes(VECTOR))
    diffs, res = _both(h, CAPACITY, regs={UC_X86_REG_ECX: empty}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != 0:
        return ['the empty capacity is %d' % res['eax']]
    vec, _ = _make_vector(h, [P0, P1, P2], capacity=5)
    diffs, res = _both(h, CAPACITY, regs={UC_X86_REG_ECX: vec}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != 5:
        return ['the capacity is %d, wanted 5' % res['eax']]
    return []


def test_count(h):
    """0x4A0C60 is the number of pairs, zero for a vector that owns nothing."""
    empty = h.alloc(VECTOR)
    h.uc.mem_write(empty, bytes(VECTOR))
    diffs, res = _both(h, COUNT, regs={UC_X86_REG_ECX: empty}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != 0:
        return ['the empty count is %d' % res['eax']]
    vec, _ = _make_vector(h, [P0, P1, P2], capacity=5)
    diffs, res = _both(h, COUNT, regs={UC_X86_REG_ECX: vec}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != 3:
        return ['the count is %d, wanted 3' % res['eax']]
    return []


def test_allocate_pairs(h):
    """0x4A0E10 allocates count * 0x38 bytes through operator new."""
    for count in (0, 3):
        diffs, res = _both(h, ALLOCATE, args=[count], ret='eax')
        if diffs:
            return diffs
        if count and not res['eax']:
            return ['count %d returned null' % count]
    return []


def test_copy_construct_pairs(h):
    """0x4A0F80 copy-constructs [first, last) at dst and returns the position after them."""
    source = _alloc_pairs(h, [P0, P1], 2)
    dst = h.alloc(2 * PAIR)
    _pad(h, dst, 2 * PAIR)
    diffs, res = _both(h, COPY_CONSTRUCT, args=[source, source + 2 * PAIR, dst], ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst + 2 * PAIR:
        return ['returned %#x, wanted %#x' % (res['eax'], dst + 2 * PAIR)]
    errors = []
    for i, spec in enumerate([P0, P1]):
        error = _check_pair(h, dst + i * PAIR, spec)
        if error:
            errors.append('pair %d: %s' % (i, error))
    return errors


def test_copy_construct_pairs_end(h):
    """0x4A1300 is the copy-construct wrapper that reports the end position."""
    source = _alloc_pairs(h, [P0, P1], 2)
    dst = h.alloc(2 * PAIR)
    _pad(h, dst, 2 * PAIR)
    diffs, res = _both(h, COPY_CONSTRUCT_END, args=[source, source + 2 * PAIR, dst], ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst + 2 * PAIR:
        return ['returned %#x, wanted %#x' % (res['eax'], dst + 2 * PAIR)]
    errors = []
    for i, spec in enumerate([P0, P1]):
        error = _check_pair(h, dst + i * PAIR, spec)
        if error:
            errors.append('pair %d: %s' % (i, error))
    return errors


def test_fill_construct_pairs(h):
    """0x4A1080 constructs count copies of value at dst."""
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    dst = h.alloc(2 * PAIR)
    _pad(h, dst, 2 * PAIR)
    diffs, res = _both(h, FILL_CONSTRUCT, args=[dst, 2, value], ret=None)
    if diffs:
        return diffs
    errors = []
    for i in range(2):
        error = _check_pair(h, dst + i * PAIR, V)
        if error:
            errors.append('copy %d: %s' % (i, error))
    return errors


def test_fill_assign_pairs(h):
    """0x4A0E80 assigns copies of value over [first, last)."""
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    dst = _alloc_pairs(h, [P0, P1], 2)
    diffs, res = _both(h, FILL_ASSIGN, args=[dst, dst + 2 * PAIR, value], ret=None)
    if diffs:
        return diffs
    errors = []
    for i in range(2):
        error = _check_pair(h, dst + i * PAIR, V)
        if error:
            errors.append('pair %d: %s' % (i, error))
    return errors


def test_copy_backward(h):
    """0x4A0D40 assigns the last pair first and returns the position of the first one."""
    source = _alloc_pairs(h, [P0, P1], 2)
    dst = _alloc_pairs(h, [P2, P2, P2, P2], 4)
    diffs, res = _both(h, COPY_BACKWARD, args=[source, source + 2 * PAIR, dst + 3 * PAIR], ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst + PAIR:
        return ['returned %#x, wanted %#x' % (res['eax'], dst + PAIR)]
    errors = []
    if _get_pair(h, dst) != P2 or _get_pair(h, dst + 3 * PAIR) != P2:
        errors.append('the pairs outside the range changed')
    for i, spec in enumerate([P0, P1]):
        error = _check_pair(h, dst + (i + 1) * PAIR, spec)
        if error:
            errors.append('pair %d: %s' % (i + 1, error))
    return errors


def test_buy(h):
    """0x4A1020 allocates count empty slots; an empty request just clears the vector."""
    vec = h.alloc(VECTOR)
    _pad(h, vec, VECTOR, 0xA5)
    diffs, res = _both(h, BUY, args=[3], regs={UC_X86_REG_ECX: vec}, ret='al')
    if diffs:
        return diffs
    if (res['eax'] & 0xFF) != 1:
        return ['returned %d, wanted 1' % (res['eax'] & 0xFF)]
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if not begin:
        return ['the block is null']
    if end != begin or limit != begin + 3 * PAIR:
        return ['the pointers are %#x/%#x/%#x' % (begin, end, limit)]
    if _u32(h, vec) != 0xA5A5A5A5:
        return ['the allocator word changed']
    empty = h.alloc(VECTOR)
    _pad(h, empty, VECTOR, 0xA5)
    diffs, res = _both(h, BUY, args=[0], regs={UC_X86_REG_ECX: empty}, ret='al')
    if diffs:
        return diffs
    if (res['eax'] & 0xFF) != 0:
        return ['the empty request returned %d' % (res['eax'] & 0xFF)]
    if struct.unpack('<III', h.uc.mem_read(empty + 4, 12)) != (0, 0, 0):
        return ['the empty vector is %r' % (h.uc.mem_read(empty + 4, 12),)]
    if _u32(h, empty) != 0xA5A5A5A5:
        return ['the allocator word changed']
    return []


def test_destroy_vector(h):
    """0x4A12C0 destroys the pairs, frees the block and clears the three pointers (allocator untouched)."""
    vec, _ = _make_vector(h, [P0, P1], allocator=0xA5A5A5A5)
    diffs, res = _both(h, DESTROY_VECTOR, regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if struct.unpack('<III', h.uc.mem_read(vec + 4, 12)) != (0, 0, 0):
        return ['the vector is %r' % (h.uc.mem_read(vec + 4, 12),)]
    if _u32(h, vec) != 0xA5A5A5A5:
        return ['the allocator word changed']
    return []


def test_insert_grow(h):
    """0x4A1330 reallocates when the spare capacity is short: a two-pair vector grows to three."""
    vec, block = _make_vector(h, [P0, P1], capacity=2)
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    diffs, res = _both(h, INSERT, args=[block + PAIR, 1, value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    errors = _check_vector(h, vec, [P0, V, P1])
    if errors:
        return errors
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if limit - begin != 3 * PAIR:
        return ['the new capacity is %d pairs' % ((limit - begin) // PAIR)]
    return []


def test_insert_grow_empty(h):
    """0x4A1330 on a null vector allocates exactly size + count (two) and fills them."""
    vec = h.alloc(VECTOR)
    h.uc.mem_write(vec, bytes(VECTOR))
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    diffs, res = _both(h, INSERT, args=[0, 2, value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    errors = _check_vector(h, vec, [V, V])
    if errors:
        return errors
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if limit - begin != 2 * PAIR:
        return ['the capacity is %d pairs' % ((limit - begin) // PAIR)]
    return []


def test_insert_short_tail(h):
    """0x4A1330 with a tail shorter than count constructs it after the new pairs and fills the gap."""
    vec, block = _make_vector(h, [P0, P1, P2, (b'l3', b'3')], capacity=6)
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    diffs, res = _both(h, INSERT, args=[block + 3 * PAIR, 2, value], regs={UC_X86_REG_ECX: vec},
                       ret=None)
    if diffs:
        return diffs
    return _check_vector(h, vec, [P0, P1, P2, V, V, (b'l3', b'3')])


def test_insert_long_tail(h):
    """0x4A1330 with a tail at least count moves its last pairs first and shifts the middle back."""
    vec, block = _make_vector(h, [P0, P1, P2, (b'l3', b'3')], capacity=6)
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    diffs, res = _both(h, INSERT, args=[block + PAIR, 2, value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    return _check_vector(h, vec, [P0, V, V, P1, P2, (b'l3', b'3')])


def test_insert_at(h):
    """0x4A1710 inserts one pair and reports its position through result."""
    vec, block = _make_vector(h, [P0, P1], capacity=4)
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    result = h.alloc(4)
    _pad(h, result, 4)
    diffs, res = _both(h, INSERT_AT, args=[result, block + PAIR, value], regs={UC_X86_REG_ECX: vec},
                       ret=None)
    if diffs:
        return diffs
    errors = _check_vector(h, vec, [P0, V, P1])
    if errors:
        return errors
    if _u32(h, result) != block + PAIR:
        return ['the result is %#x, wanted %#x' % (_u32(h, result), block + PAIR)]
    return []


def test_push_spare(h):
    """0x4A17A0 constructs the pair in a spare slot when there is one."""
    vec, block = _make_vector(h, [P0, P1], capacity=4)
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    diffs, res = _both(h, PUSH, args=[value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    return _check_vector(h, vec, [P0, P1, V])


def test_push_grow(h):
    """0x4A17A0 inserts through the reallocation when the capacity is full."""
    vec, block = _make_vector(h, [P0, P1], capacity=2)
    value = h.alloc(PAIR)
    _pad(h, value, PAIR)
    _put_pair(h, value, *V)
    diffs, res = _both(h, PUSH, args=[value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    return _check_vector(h, vec, [P0, P1, V])


# --- the loader object --------------------------------------------------------------------------------

def test_inputcfg_ctor(h):
    """0x4A1650 stores the class vtable, nulls the vector and leaves EDX (and the allocator) alone."""
    obj = h.alloc(0x14)
    _pad(h, obj, 0x14, 0xA5)
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EDX: 0x12345678}
    diffs, res = _both(h, CTOR, regs=regs, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != obj:
        return ['returned %#x, not this' % res['eax']]
    if res['edx'] != 0x12345678:
        return ['EDX became %#x' % res['edx']]
    if _u32(h, obj) != VFT_CLASS:
        return ['the vtable is %#x' % _u32(h, obj)]
    if struct.unpack('<III', h.uc.mem_read(obj + 8, 12)) != (0, 0, 0):
        return ['the vector is %r' % (h.uc.mem_read(obj + 8, 12),)]
    if _u32(h, obj + 4) != 0xA5A5A5A5:
        return ['the allocator word changed']
    return []


def test_inputcfg_dtor(h):
    """0x4A1690 destroys the pairs, clears the vector and stores the singleton vtable last."""
    obj = h.alloc(0x14)
    _pad(h, obj, 0x14)
    h.uc.mem_write(obj, struct.pack('<I', VFT_CLASS))
    block = _alloc_pairs(h, [P0, P1], 2)
    _pad(h, obj + 4, 4)
    h.uc.mem_write(obj + 8, struct.pack('<III', block, block + 2 * PAIR, block + 2 * PAIR))
    diffs, res = _both(h, DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    if _u32(h, obj) != VFT_SINGLETON:
        return ['the vtable is %#x, wanted %#x' % (_u32(h, obj), VFT_SINGLETON)]
    if struct.unpack('<III', h.uc.mem_read(obj + 8, 12)) != (0, 0, 0):
        return ['the vector is %r' % (h.uc.mem_read(obj + 8, 12),)]
    return []


def test_inputcfg_delete(h):
    """0x4A1780 destroys the object and frees it only when bit 0 of the flags is set; returns this."""
    for flags in (0, 1):
        obj = h.alloc(0x14)
        _pad(h, obj, 0x14)
        h.uc.mem_write(obj, struct.pack('<I', VFT_CLASS))
        block = _alloc_pairs(h, [P0], 1)
        _pad(h, obj + 4, 4)
        h.uc.mem_write(obj + 8, struct.pack('<III', block, block + PAIR, block + PAIR))
        diffs, res = _both(h, DELETE, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        if res['eax'] != obj:
            return ['flags %d returned %#x, not this' % (flags, res['eax'])]
        if _u32(h, obj) != VFT_SINGLETON:
            return ['flags %d left the vtable %#x' % (flags, _u32(h, obj))]
    return []


def test_inputcfg_instance(h):
    """0x46EA50 allocates and constructs the loader once and remembers it in the singleton global."""
    def setup(m):
        m.uc.mem_write(INSTANCE_GLOB, struct.pack('<I', 0))

    diffs = h.compare(INSTANCE, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(INSTANCE)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    value = _u32(h, INSTANCE_GLOB)
    if value == 0:
        return ['the singleton global is still null']
    if res['eax'] != value:
        return ['returned %#x, the global is %#x' % (res['eax'], value)]
    if _u32(h, value) != VFT_CLASS:
        return ['the object vtable is %#x' % _u32(h, value)]
    return []
