"""The bucket-vector operations of the file system maps: the fill insert (0x553970), the range erase
(0x451350), the resize (0x553E40) and the assign (0x4EF350).

The vector object starts at its allocator byte: +00 allocator, +04 begin, +08 end, +0C limit.  The tests set up
the storage by hand so the old block, the new allocation and the untouched allocator bytes are all checked."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

INSERT = 0x00553970
ERASE = 0x00451350
RESIZE = 0x00553E40
ASSIGN = 0x004EF350
MAX_SIZE = 0x3FFFFFFF
UNUSED = 0xEEEEEEEE


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _vector(h, capacity, values):
    """an allocator-prefixed vector: the allocator 0xA5, the elements in their own block, the used slots 0xEE"""
    vec = h.alloc(0x10, b'\xA5' * 0x10)
    if capacity == 0:
        h.uc.mem_write(vec + 4, bytes(12))
        return vec, 0
    slots = values + [UNUSED] * (capacity - len(values))
    data = h.alloc(4 * capacity, struct.pack('<%dI' % capacity, *slots))
    h.uc.mem_write(vec + 4, struct.pack('<III', data, data + 4 * len(values), data + 4 * capacity))
    return vec, data


def _state(h, vec):
    return struct.unpack('<III', h.uc.mem_read(vec + 4, 12))


def _elements(h, begin, end):
    return list(struct.unpack('<%dI' % ((end - begin) // 4), h.uc.mem_read(begin, end - begin)))


def _grown(capacity, size, count):
    grown = 0 if capacity > MAX_SIZE - capacity // 2 else capacity + capacity // 2
    return max(grown, size + count)


def test_vector_insert(h):
    """0x553970 inserts count copies at position, growing the block when the capacity is short."""
    value = 0xCAFEBABE
    cases = [
        (0, [], 0, 3),
        (5, [10, 20], 2, 2),
        (6, [10, 20, 30, 40], 1, 2),
        (8, [10, 20, 30], 1, 3),
        (2, [10, 20], 1, 2),
        (4, [10, 20, 30, 40], 0, 1),
    ]
    for capacity, values, index, count in cases:
        label = 'cap %d values %r at %d x%d' % (capacity, values, index, count)
        vec, data = _vector(h, capacity, values)
        value_slot = h.alloc(4, struct.pack('<I', value))
        args = [data + 4 * index if data else 0, count, value_slot]
        diffs = h.compare(INSERT, args=args, regs={UC_X86_REG_ECX: vec}, ret=None)
        if diffs:
            return ['%s: %s' % (label, d) for d in diffs]
        res = h.call(INSERT, args=args, regs={UC_X86_REG_ECX: vec})
        if res['fault']:
            return ['%s: replacement faulted: %s' % (label, res['fault'])]
        if _u32(h, vec) != 0xA5A5A5A5:
            return ['%s: the allocator bytes were touched' % label]
        begin, end, limit = _state(h, vec)
        want = values[:index] + [value] * count + values[index:]
        got = _elements(h, begin, end)
        if got != want:
            return ['%s: got %r want %r' % (label, got, want)]
        if capacity < len(values) + count:
            capacity_want = _grown(capacity, len(values), count)
            if limit - begin != 4 * capacity_want:
                return ['%s: the grown block is %d bytes, want %d' % (label, limit - begin, 4 * capacity_want)]
        elif data and begin != data:
            return ['%s: the block moved without growing' % label]
    return None


def test_vector_insert_none(h):
    """0x553970 with a count of 0 leaves the vector untouched."""
    vec, data = _vector(h, 4, [10, 20])
    value_slot = h.alloc(4, struct.pack('<I', 0xCAFEBABE))
    before = bytes(h.uc.mem_read(vec, 0x10))
    diffs = h.compare(INSERT, args=[data + 4, 0, value_slot], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    h.call(INSERT, args=[data + 4, 0, value_slot], regs={UC_X86_REG_ECX: vec})
    if bytes(h.uc.mem_read(vec, 0x10)) != before:
        return ['the vector fields changed']
    return None


def test_vector_erase(h):
    """0x451350 moves the tail over the erased range and reports the first iterator."""
    vec, data = _vector(h, 6, [10, 20, 30, 40, 50])
    out = h.alloc(4, bytes(4))
    first, last = data + 4, data + 12
    diffs = h.compare(ERASE, args=[out, first, last], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    res = h.call(ERASE, args=[out, first, last], regs={UC_X86_REG_ECX: vec})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    begin, end, limit = _state(h, vec)
    if (begin, end, limit) != (data, data + 12, data + 24):
        return ['the vector is %08X/%08X/%08X' % (begin, end, limit)]
    if _elements(h, begin, end) != [10, 40, 50]:
        return ['the elements are %r' % (_elements(h, begin, end),)]
    if _u32(h, out) != first:
        return ['the reported iterator is %08X, want %08X' % (_u32(h, out), first)]

    vec, data = _vector(h, 4, [10, 20])
    out = h.alloc(4, bytes(4))
    diffs = h.compare(ERASE, args=[out, data + 4, data + 4], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    h.call(ERASE, args=[out, data + 4, data + 4], regs={UC_X86_REG_ECX: vec})
    if _state(h, vec)[1] != data + 8 or _u32(h, out) != data + 4:
        return ['the empty erase changed the vector']
    return None


def test_vector_resize(h):
    """0x553E40 grows with copies of the value and shrinks by erasing the tail."""
    value = 0x12345678
    cases = [
        (0, [], 3),
        (6, [10, 20], 5),
        (6, [10, 20, 30, 40, 50], 3),
        (6, [10, 20, 30], 3),
        (2, [10, 20], 4),
    ]
    for capacity, values, count in cases:
        label = 'cap %d values %r -> %d' % (capacity, values, count)
        vec, data = _vector(h, capacity, values)
        args = [count, value]
        diffs = h.compare(RESIZE, args=args, regs={UC_X86_REG_ECX: vec}, ret=None)
        if diffs:
            return ['%s: %s' % (label, d) for d in diffs]
        res = h.call(RESIZE, args=args, regs={UC_X86_REG_ECX: vec})
        if res['fault']:
            return ['%s: replacement faulted: %s' % (label, res['fault'])]
        if _u32(h, vec) != 0xA5A5A5A5:
            return ['%s: the allocator bytes were touched' % label]
        begin, end, limit = _state(h, vec)
        want = values + [value] * (count - len(values)) if count > len(values) else values[:count]
        got = _elements(h, begin, end)
        if got != want:
            return ['%s: got %r want %r' % (label, got, want)]
        if count <= len(values) and begin != data:
            return ['%s: the block moved without growing' % label]
    return None


def test_vector_assign(h):
    """0x4EF350 drops the elements and refills the vector with count copies of the value."""
    value = 0x0BADF00D
    cases = [
        (6, [10, 20, 30, 40, 50], 3),
        (0, [], 9),
        (2, [10, 20], 4),
    ]
    for capacity, values, count in cases:
        label = 'cap %d values %r := %d' % (capacity, values, count)
        vec, data = _vector(h, capacity, values)
        value_slot = h.alloc(4, struct.pack('<I', value))
        args = [count, value_slot]
        diffs = h.compare(ASSIGN, args=args, regs={UC_X86_REG_ECX: vec}, ret=None)
        if diffs:
            return ['%s: %s' % (label, d) for d in diffs]
        res = h.call(ASSIGN, args=args, regs={UC_X86_REG_ECX: vec})
        if res['fault']:
            return ['%s: replacement faulted: %s' % (label, res['fault'])]
        if _u32(h, vec) != 0xA5A5A5A5:
            return ['%s: the allocator bytes were touched' % label]
        begin, end, limit = _state(h, vec)
        got = _elements(h, begin, end)
        if got != [value] * count:
            return ['%s: got %r' % (label, got)]
        if capacity >= count and data and begin != data:
            return ['%s: the block moved without growing' % label]
        if capacity == 6 and data:
            after = values[count:] + [UNUSED] * (capacity - len(values))
            if _elements(h, begin + 4 * count, data + 4 * capacity) != after:
                return ['%s: the slots after the end changed' % label]
    return None
