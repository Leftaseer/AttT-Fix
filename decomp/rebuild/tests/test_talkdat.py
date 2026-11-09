"""CReadTalkDat: the talk table of Talks.dat - the vector<TalkLine> and vector<TalkEntry> machinery the loader
uses (0x4A99C0 ... 0x4AB5C0), the 0xA4-byte entries and their blocks (0x421150 / 0x420910 / 0x4AA570 /
0x4AA940 / 0x4AA7E0 / 0x4AA870), and the loader object (0x4AB470 / 0x4AB4B0).

The parser (0x4AAB70) and Load (0x4AB660) drive the dat lexer over an open CGameFile, so they are covered by
the build replacement only, not here.

line  = {kind; std::string text; duration} (0x24 bytes, text at +04, duration at +20)
block = {float x; float y; byte flag; std::string text; float value; std::string text2} (0x48 bytes)
entry = {id; block first; block second; vector<TalkLine> lines} (0xA4 bytes)
vector of lines/entries = {allocator; begin; end; limit} (0x10 bytes, allocator kept as the owner left it)
"""
import struct
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EDX

LINE = 0x24
ENTRY = 0xA4
VECTOR = 0x10

ALLOC_LINES = 0x004A99C0
ALLOC_ENTRIES = 0x004A9A20
COPY_CONSTRUCT_LINES = 0x004A9DE0
FILL_CONSTRUCT_LINES = 0x004A9E80
FILL_CONSTRUCT_LINES_END = 0x004AA010
COPY_ASSIGN_LINES = 0x004A9C10
FILL_ASSIGN_LINES = 0x004A9C60
COPY_BACKWARD_LINES = 0x004A9AB0
DESTROY_LINES = 0x004AA050
ERASE_LINES = 0x004AA0B0
DESTROY_LINE_VECTOR = 0x004AA120
COPY_CONSTRUCT_LINE_VECTOR = 0x004AA170
CLEAR_LINE_VECTOR = 0x004AA250
INSERT_LINES = 0x004AA270
INSERT_LINE_AT = 0x004AA8D0
PUSH_LINE = 0x004AAA80

COPY_CONSTRUCT_BLOCK = 0x00421150
DESTROY_BLOCK = 0x00420910
COPY_CONSTRUCT_ENTRY = 0x004AA570
ASSIGN_ENTRY = 0x004AA940
ASSIGN_LINE_VECTOR = 0x004AA5F0
CONSTRUCT_ENTRY = 0x004AA7E0
DESTROY_ENTRY = 0x004AA870
COPY_CONSTRUCT_ENTRIES = 0x004AAD90
FILL_CONSTRUCT_ENTRIES = 0x004AAE30
COPY_BACKWARD_ENTRIES = 0x004AAA20
FILL_ASSIGN_ENTRIES = 0x004AAB10
DESTROY_ENTRIES = 0x004AAED0
DESTROY_ENTRY_VECTOR = 0x004AB100
INSERT_ENTRIES = 0x004AB170
INSERT_ENTRY_AT = 0x004AB530
PUSH_ENTRY = 0x004AB5C0

TALKDAT_CTOR = 0x004AB470
TALKDAT_DTOR = 0x004AB4B0

VFT_CLASS = 0x0061015C
VFT_SINGLETON = 0x00610154


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


def _put_line(h, line, kind, text, duration):
    h.uc.mem_write(line, struct.pack('<I', kind))
    _put_str(h, line + 4, text)
    h.uc.mem_write(line + 0x20, struct.pack('<I', duration))


def _check_line(h, line, spec):
    kind, text, duration = spec
    if _u32(h, line) != kind:
        return 'kind %d, wanted %d' % (_u32(h, line), kind)
    if _get_str(h, line + 4) != text:
        return 'text %r, wanted %r' % (_get_str(h, line + 4), text)
    if _u32(h, line + 0x20) != duration:
        return 'duration %d, wanted %d' % (_u32(h, line + 0x20), duration)
    return None


def _alloc_lines(h, specs, capacity):
    size = LINE * max(capacity, 1)
    block = h.alloc(size)
    _pad(h, block, size)
    for i, spec in enumerate(specs):
        _put_line(h, block + i * LINE, *spec)
    return block


def _fill_lines_field(h, vec, specs, capacity=None):
    """fill a 0x10 vector object in place; the allocator dword is left alone"""
    if not specs and not capacity:
        h.uc.mem_write(vec + 4, struct.pack('<III', 0, 0, 0))
        return 0
    cap = len(specs) if capacity is None else capacity
    block = _alloc_lines(h, specs, cap)
    h.uc.mem_write(vec + 4, struct.pack('<III', block, block + len(specs) * LINE, block + cap * LINE))
    return block


def _make_vector(h, specs, capacity=None):
    vec = h.alloc(VECTOR)
    h.uc.mem_write(vec, bytes(VECTOR))
    block = _fill_lines_field(h, vec, specs, capacity)
    return vec, block


def _vector_size(h, vec):
    begin, end = struct.unpack('<II', h.uc.mem_read(vec + 4, 8))
    return (end - begin) // LINE


def _check_vector(h, vec, specs):
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if (end - begin) // LINE != len(specs):
        return ['%d lines in the vector, wanted %d' % ((end - begin) // LINE, len(specs))]
    errors = []
    for i, spec in enumerate(specs):
        error = _check_line(h, begin + i * LINE, spec)
        if error:
            errors.append('line %d: %s' % (i, error))
    return errors


def _put_block(h, block, x, y, flag, text, value, text2):
    h.uc.mem_write(block, struct.pack('<ff', x, y))
    h.uc.mem_write(block + 8, bytes([flag]))
    _put_str(h, block + 0x0C, text)
    h.uc.mem_write(block + 0x28, struct.pack('<f', value))
    _put_str(h, block + 0x2C, text2)


def _check_block(h, block, spec):
    x, y, flag, text, value, text2 = spec
    errors = []
    if struct.unpack('<ff', h.uc.mem_read(block, 8)) != (x, y):
        errors.append('numbers %r, wanted %r' % (struct.unpack('<ff', h.uc.mem_read(block, 8)), (x, y)))
    if h.uc.mem_read(block + 8, 1)[0] != flag:
        errors.append('flag byte %02X, wanted %02X' % (h.uc.mem_read(block + 8, 1)[0], flag))
    if _get_str(h, block + 0x0C) != text:
        errors.append('text %r, wanted %r' % (_get_str(h, block + 0x0C), text))
    if struct.unpack('<f', h.uc.mem_read(block + 0x28, 4))[0] != value:
        errors.append('value %r, wanted %r' % (struct.unpack('<f', h.uc.mem_read(block + 0x28, 4))[0], value))
    if _get_str(h, block + 0x2C) != text2:
        errors.append('text2 %r, wanted %r' % (_get_str(h, block + 0x2C), text2))
    return errors


def _put_entry(h, entry, ident, first, second, lines=()):
    h.uc.mem_write(entry, struct.pack('<I', ident))
    _put_block(h, entry + 0x04, *first)
    _put_block(h, entry + 0x4C, *second)
    _fill_lines_field(h, entry + 0x94, lines)


def _check_entry(h, entry, ident, first, second, lines):
    errors = []
    if _u32(h, entry) != ident:
        errors.append('id %d, wanted %d' % (_u32(h, entry), ident))
    errors += ['first ' + e for e in _check_block(h, entry + 0x04, first)]
    errors += ['second ' + e for e in _check_block(h, entry + 0x4C, second)]
    errors += _check_vector(h, entry + 0x94, lines)
    return errors


def _alloc_entries(h, specs, capacity):
    size = ENTRY * max(capacity, 1)
    block = h.alloc(size)
    _pad(h, block, size)
    for i, spec in enumerate(specs):
        _put_entry(h, block + i * ENTRY, *spec)
    return block


def _make_entries(h, specs, capacity=None):
    if not specs and not capacity:
        vec = h.alloc(VECTOR)
        h.uc.mem_write(vec, bytes(VECTOR))
        return vec, 0
    cap = len(specs) if capacity is None else capacity
    block = _alloc_entries(h, specs, cap)
    vec = h.alloc(VECTOR)
    h.uc.mem_write(vec, bytes(VECTOR))
    h.uc.mem_write(vec + 4, struct.pack('<III', block, block + len(specs) * ENTRY, block + cap * ENTRY))
    return vec, block


def _entry_ids(h, vec):
    begin, end = struct.unpack('<II', h.uc.mem_read(vec + 4, 8))
    return [_u32(h, begin + i * ENTRY) for i in range((end - begin) // ENTRY)]


def _both(h, fn, args=(), regs=None, ret=None):
    """compare the original entry with the replacement; when they agree, run the replacement once more"""
    diffs = h.compare(fn, args=args, regs=regs, ret=ret)
    if diffs:
        return diffs, None
    res = h.call(fn, args=args, regs=regs)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']], None
    return [], res


FIRST = (1.5, -2.25, 0x5A, b'first text', 3.0, b'first tail')
SECOND = (0.5, 7.0, 0x00, b'second text', -1.0, b'second tail')
B1 = (2.5, -3.5, 0x81, b'one', 4.0, b'two')
B2 = (-4.0, 12.25, 0xFF, b'three', 0.5, b'four')


# --- vector<TalkLine> storage -------------------------------------------------------------------------

def test_allocate_talk_lines(h):
    """0x4A99C0: count * 0x24 bytes through operator new."""
    diffs, res = _both(h, ALLOC_LINES, args=[3], ret='eax')
    if diffs:
        return diffs
    if not res['eax']:
        return ['returned null']
    return []


def test_allocate_talk_entries(h):
    """0x4A9A20: count * 0xa4 bytes through operator new."""
    diffs, res = _both(h, ALLOC_ENTRIES, args=[2], ret='eax')
    if diffs:
        return diffs
    if not res['eax']:
        return ['returned null']
    return []


def test_copy_construct_talk_lines(h):
    """0x4A9DE0 copy-constructs [first, last) at dst and returns the position after the last."""
    source = h.alloc(2 * LINE)
    _pad(h, source, 2 * LINE)
    _put_line(h, source, 3, b'first line', 100)
    _put_line(h, source + LINE, 4, b'a rather long second line', 200)
    dst = h.alloc(2 * LINE)
    _pad(h, dst, 2 * LINE)
    diffs, res = _both(h, COPY_CONSTRUCT_LINES, args=[source, source + 2 * LINE, dst], ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst + 2 * LINE:
        return ['returned %#x, wanted %#x' % (res['eax'], dst + 2 * LINE)]
    errors = []
    for i, spec in enumerate([(3, b'first line', 100), (4, b'a rather long second line', 200)]):
        error = _check_line(h, dst + i * LINE, spec)
        if error:
            errors.append('line %d: %s' % (i, error))
    return errors


def test_fill_construct_talk_lines(h):
    """0x4A9E80 constructs count copies of value at dst."""
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 9, b'the value', 55)
    dst = h.alloc(3 * LINE)
    _pad(h, dst, 3 * LINE)
    diffs, res = _both(h, FILL_CONSTRUCT_LINES, args=[dst, 3, value], ret=None)
    if diffs:
        return diffs
    errors = []
    for i in range(3):
        error = _check_line(h, dst + i * LINE, (9, b'the value', 55))
        if error:
            errors.append('copy %d: %s' % (i, error))
    return errors


def test_fill_construct_talk_lines_end(h):
    """0x4AA010 fills and returns dst + count (the wrapper the insertion algorithms use)."""
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 0, b'x', 50)
    dst = h.alloc(2 * LINE)
    _pad(h, dst, 2 * LINE)
    diffs, res = _both(h, FILL_CONSTRUCT_LINES_END, args=[dst, 2, value], ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst + 2 * LINE:
        return ['returned %#x, wanted %#x' % (res['eax'], dst + 2 * LINE)]
    return []


def test_copy_assign_talk_lines(h):
    """0x4A9C10 assigns [first, last) over dst and returns the position after them."""
    source = h.alloc(2 * LINE)
    _pad(h, source, 2 * LINE)
    _put_line(h, source, 5, b'source one', 60)
    _put_line(h, source + LINE, 6, b'source two is longer', 70)
    dst = h.alloc(3 * LINE)
    _pad(h, dst, 3 * LINE)
    _put_line(h, dst, 0, b'old zero', 1)
    _put_line(h, dst + LINE, 0, b'old one', 2)
    _put_line(h, dst + 2 * LINE, 0, b'old two', 3)
    diffs, res = _both(h, COPY_ASSIGN_LINES, args=[source, source + 2 * LINE, dst], ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst + 2 * LINE:
        return ['returned %#x, wanted %#x' % (res['eax'], dst + 2 * LINE)]
    errors = []
    for i, spec in enumerate([(5, b'source one', 60), (6, b'source two is longer', 70),
                              (0, b'old two', 3)]):
        error = _check_line(h, dst + i * LINE, spec)
        if error:
            errors.append('line %d: %s' % (i, error))
    return errors


def test_fill_assign_talk_lines(h):
    """0x4A9C60 assigns copies of value over [first, last)."""
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 2, b'replacement', 90)
    target = h.alloc(3 * LINE)
    _pad(h, target, 3 * LINE)
    _put_line(h, target, 0, b'a', 1)
    _put_line(h, target + LINE, 0, b'b', 2)
    _put_line(h, target + 2 * LINE, 0, b'c', 3)
    diffs, res = _both(h, FILL_ASSIGN_LINES, args=[target, target + 2 * LINE, value], ret=None)
    if diffs:
        return diffs
    errors = []
    for i in range(2):
        error = _check_line(h, target + i * LINE, (2, b'replacement', 90))
        if error:
            errors.append('line %d: %s' % (i, error))
    error = _check_line(h, target + 2 * LINE, (0, b'c', 3))
    if error:
        errors.append('untouched line: %s' % error)
    return errors


def test_copy_backward_talk_lines(h):
    """0x4A9AB0 copies [first, last) backwards and returns dst after the copies."""
    source = h.alloc(2 * LINE)
    _pad(h, source, 2 * LINE)
    _put_line(h, source, 7, b'back one', 30)
    _put_line(h, source + LINE, 8, b'back two', 40)
    dst = h.alloc(2 * LINE)
    _pad(h, dst, 2 * LINE)
    diffs, res = _both(h, COPY_BACKWARD_LINES, args=[source, source + 2 * LINE, dst + 2 * LINE], ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst:
        return ['returned %#x, wanted %#x' % (res['eax'], dst)]
    errors = []
    for i, spec in enumerate([(7, b'back one', 30), (8, b'back two', 40)]):
        error = _check_line(h, dst + i * LINE, spec)
        if error:
            errors.append('line %d: %s' % (i, error))
    return errors


def test_destroy_talk_lines(h):
    """0x4AA050 destroys [first, last); the harness's std::string destructor leaves the bytes."""
    block = h.alloc(2 * LINE)
    _pad(h, block, 2 * LINE)
    _put_line(h, block, 0, b'zap one', 10)
    _put_line(h, block + LINE, 1, b'zap two', 20)
    diffs, res = _both(h, DESTROY_LINES, args=[block, block + 2 * LINE], ret=None)
    return diffs


# --- vector<TalkLine> ---------------------------------------------------------------------------------

def test_erase_talk_lines(h):
    """0x4AA0B0 moves the tail after last over first, destroys the old tail and returns first."""
    vec, block = _make_vector(h, [(0, b'a', 10), (1, b'b', 20), (0, b'c', 30), (1, b'd', 40)])
    result = h.alloc(4)
    diffs, res = _both(h, ERASE_LINES, args=[result, block + LINE, block + 3 * LINE],
                       regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _u32(h, result) != block + LINE:
        return ['the result is %#x, wanted first %#x' % (_u32(h, result), block + LINE)]
    if _vector_size(h, vec) != 2:
        return ['the vector has %d lines' % _vector_size(h, vec)]
    return _check_vector(h, vec, [(0, b'a', 10), (1, b'd', 40)])


def test_destroy_talk_line_vector(h):
    """0x4AA120 destroys the elements, frees the block and clears the three pointers."""
    vec, block = _make_vector(h, [(1, b'one', 10), (2, b'two', 20)])
    h.uc.mem_write(vec, struct.pack('<I', 0xA5A5A5A5))
    diffs, res = _both(h, DESTROY_LINE_VECTOR, regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if struct.unpack('<III', h.uc.mem_read(vec + 4, 12)) != (0, 0, 0):
        return ['the pointers are %r' % (h.uc.mem_read(vec + 4, 12),)]
    if _u32(h, vec) != 0xA5A5A5A5:
        return ['the allocator word changed']
    return []


def test_copy_construct_talk_line_vector(h):
    """0x4AA170 allocates one block, copies the source lines and leaves an empty source null."""
    source, _ = _make_vector(h, [(0, b'copy a', 11), (1, b'copy b is longer', 22)])
    dest = h.alloc(VECTOR)
    _pad(h, dest, VECTOR, 0xA5)
    diffs, res = _both(h, COPY_CONSTRUCT_LINE_VECTOR, args=[source], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dest:
        return ['returned %#x, not this' % res['eax']]
    if _u32(h, dest) != 0xA5A5A5A5:
        return ['the allocator word changed']
    errors = _check_vector(h, dest, [(0, b'copy a', 11), (1, b'copy b is longer', 22)])
    if errors:
        return errors
    empty = h.alloc(VECTOR)
    h.uc.mem_write(empty, bytes(VECTOR))
    dest2 = h.alloc(VECTOR)
    _pad(h, dest2, VECTOR, 0xA5)
    diffs, res = _both(h, COPY_CONSTRUCT_LINE_VECTOR, args=[empty], regs={UC_X86_REG_ECX: dest2}, ret='eax')
    if diffs:
        return diffs
    if struct.unpack('<III', h.uc.mem_read(dest2 + 4, 12)) != (0, 0, 0):
        return ['an empty source left %r' % (h.uc.mem_read(dest2 + 4, 12),)]
    return []


def test_clear_talk_line_vector(h):
    """0x4AA250 erases [begin, end): the end moves back to the begin."""
    vec, block = _make_vector(h, [(0, b'c1', 1), (1, b'c2', 2), (0, b'c3', 3)])
    diffs, res = _both(h, CLEAR_LINE_VECTOR, regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    begin, end = struct.unpack('<II', h.uc.mem_read(vec + 4, 8))
    if end != begin:
        return ['the vector still holds %d lines' % ((end - begin) // LINE)]
    return []


def test_insert_talk_lines_grow(h):
    """0x4AA270 reallocates when the spare capacity is short: a two-line vector grows to four."""
    vec, block = _make_vector(h, [(0, b'alpha', 10), (1, b'beta', 20)], capacity=2)
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 7, b'inserted', 99)
    diffs, res = _both(h, INSERT_LINES, args=[block + LINE, 2, value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    errors = _check_vector(h, vec, [(0, b'alpha', 10), (7, b'inserted', 99), (7, b'inserted', 99),
                                    (1, b'beta', 20)])
    if errors:
        return errors
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if limit - begin != 4 * LINE:
        return ['the new capacity is %d lines' % ((limit - begin) // LINE)]
    return []


def test_insert_talk_lines_grow_empty(h):
    """0x4AA270 on a null vector allocates exactly size + count (two) and fills them."""
    vec = h.alloc(VECTOR)
    h.uc.mem_write(vec, bytes(VECTOR))
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 3, b'new', 44)
    diffs, res = _both(h, INSERT_LINES, args=[0, 2, value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    errors = _check_vector(h, vec, [(3, b'new', 44), (3, b'new', 44)])
    if errors:
        return errors
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if limit - begin != 2 * LINE:
        return ['the capacity is %d lines' % ((limit - begin) // LINE)]
    return []


def test_insert_talk_lines_short_tail(h):
    """0x4AA270 with a tail shorter than count constructs it after the new lines and fills the gap."""
    vec, block = _make_vector(h, [(0, b'l0', 10), (1, b'l1', 20), (0, b'l2', 30), (1, b'l3', 40)],
                              capacity=6)
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 9, b'v', 50)
    diffs, res = _both(h, INSERT_LINES, args=[block + 3 * LINE, 2, value], regs={UC_X86_REG_ECX: vec},
                       ret=None)
    if diffs:
        return diffs
    return _check_vector(h, vec, [(0, b'l0', 10), (1, b'l1', 20), (0, b'l2', 30), (9, b'v', 50),
                                  (9, b'v', 50), (1, b'l3', 40)])


def test_insert_talk_lines_long_tail(h):
    """0x4AA270 with a tail at least count moves its last lines first and shifts the middle back."""
    vec, block = _make_vector(h, [(0, b'l0', 10), (1, b'l1', 20), (0, b'l2', 30), (1, b'l3', 40)],
                              capacity=6)
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 9, b'v', 50)
    diffs, res = _both(h, INSERT_LINES, args=[block + LINE, 2, value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    return _check_vector(h, vec, [(0, b'l0', 10), (9, b'v', 50), (9, b'v', 50), (1, b'l1', 20),
                                  (0, b'l2', 30), (1, b'l3', 40)])


def test_insert_talk_line_at(h):
    """0x4AA8D0 inserts one line and reports its position through result."""
    vec, block = _make_vector(h, [(0, b'first', 10), (1, b'second', 20)], capacity=4)
    result = h.alloc(4)
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 6, b'middle', 60)
    diffs, res = _both(h, INSERT_LINE_AT, args=[result, block + LINE, value],
                       regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _u32(h, result) != block + LINE:
        return ['the new line is reported at %#x, wanted %#x' % (_u32(h, result), block + LINE)]
    return _check_vector(h, vec, [(0, b'first', 10), (6, b'middle', 60), (1, b'second', 20)])


def test_push_talk_line_spare(h):
    """0x4AAA80 constructs into the spare slot when the capacity allows it."""
    vec, block = _make_vector(h, [(0, b'p1', 1), (1, b'p2', 2)], capacity=4)
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 4, b'pushed', 30)
    diffs, res = _both(h, PUSH_LINE, args=[value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _vector_size(h, vec) != 3:
        return ['the vector has %d lines' % _vector_size(h, vec)]
    return _check_vector(h, vec, [(0, b'p1', 1), (1, b'p2', 2), (4, b'pushed', 30)])


def test_push_talk_line_grow(h):
    """0x4AAA80 with a full vector takes the insertion path and reallocates."""
    vec, block = _make_vector(h, [(0, b'p1', 1), (1, b'p2', 2)], capacity=2)
    value = h.alloc(LINE)
    _pad(h, value, LINE)
    _put_line(h, value, 4, b'pushed', 30)
    diffs, res = _both(h, PUSH_LINE, args=[value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _vector_size(h, vec) != 3:
        return ['the vector has %d lines' % _vector_size(h, vec)]
    return _check_vector(h, vec, [(0, b'p1', 1), (1, b'p2', 2), (4, b'pushed', 30)])


# --- blocks and entries -------------------------------------------------------------------------------

def test_copy_construct_talk_block(h):
    """0x421150 copies the numbers and the raw flag byte, then copy-constructs the two texts."""
    other = h.alloc(0x48)
    _put_block(h, other, *FIRST)
    dest = h.alloc(0x48)
    _pad(h, dest, 0x48, 0xA5)
    diffs, res = _both(h, COPY_CONSTRUCT_BLOCK, args=[other], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dest:
        return ['returned %#x, not this' % res['eax']]
    return _check_block(h, dest, FIRST)


def test_destroy_talk_block(h):
    """0x420910 destroys text2 and then text."""
    block = h.alloc(0x48)
    _put_block(h, block, *B1)
    diffs, res = _both(h, DESTROY_BLOCK, regs={UC_X86_REG_ECX: block}, ret=None)
    return diffs


def test_copy_construct_talk_entry(h):
    """0x4AA570 copies the id, copy-constructs both blocks and the line vector."""
    source = h.alloc(ENTRY)
    _pad(h, source, ENTRY)
    _put_entry(h, source, 0x1234, FIRST, SECOND,
               [(0, b'entry line one', 100), (1, b'entry line two', 200)])
    dest = h.alloc(ENTRY)
    _pad(h, dest, ENTRY, 0xA5)
    diffs, res = _both(h, COPY_CONSTRUCT_ENTRY, args=[source], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dest:
        return ['returned %#x, not this' % res['eax']]
    return _check_entry(h, dest, 0x1234, FIRST, SECOND,
                        [(0, b'entry line one', 100), (1, b'entry line two', 200)])


def test_assign_talk_entry(h):
    """0x4AA940 assigns the fields in place, including the raw flag bytes and the line vector."""
    dest = h.alloc(ENTRY)
    _pad(h, dest, ENTRY)
    _put_entry(h, dest, 1, SECOND, FIRST, [(0, b'old line', 5)])
    source = h.alloc(ENTRY)
    _pad(h, source, ENTRY)
    _put_entry(h, source, 2, B1, B2, [(1, b'new a', 11), (0, b'new b', 22), (1, b'new c', 33)])
    diffs, res = _both(h, ASSIGN_ENTRY, args=[source], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dest:
        return ['returned %#x, not this' % res['eax']]
    return _check_entry(h, dest, 2, B1, B2, [(1, b'new a', 11), (0, b'new b', 22), (1, b'new c', 33)])


def test_assign_line_vector_branches(h):
    """0x4AA5F0: empty source clears, a shorter one assigned over the prefix destroys the tail, a longer one
    either fits the spare capacity or takes a new block; self-assignment changes nothing."""
    errors = []
    # empty source
    source, _ = _make_vector(h, [])
    dest, _ = _make_vector(h, [(0, b'a', 1), (1, b'b', 2)])
    diffs, res = _both(h, ASSIGN_LINE_VECTOR, args=[source], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    if _vector_size(h, dest) != 0:
        errors.append('an empty source left %d lines' % _vector_size(h, dest))
    # shorter source
    source, _ = _make_vector(h, [(5, b'short', 50)])
    dest, _ = _make_vector(h, [(0, b'a', 1), (1, b'b', 2), (2, b'c', 3)])
    diffs, res = _both(h, ASSIGN_LINE_VECTOR, args=[source], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    errors += _check_vector(h, dest, [(5, b'short', 50)])
    # longer source, fits the capacity
    source, _ = _make_vector(h, [(1, b's0', 10), (2, b's1', 20), (3, b's2', 30), (4, b's3', 40)])
    dest, _ = _make_vector(h, [(0, b'a', 1), (0, b'b', 2)], capacity=5)
    diffs, res = _both(h, ASSIGN_LINE_VECTOR, args=[source], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    errors += _check_vector(h, dest, [(1, b's0', 10), (2, b's1', 20), (3, b's2', 30), (4, b's3', 40)])
    # longer source, too big for the capacity
    source, _ = _make_vector(h, [(1, b't0', 10), (2, b't1', 20), (3, b't2', 30)])
    dest, _ = _make_vector(h, [(0, b'a', 1), (0, b'b', 2)], capacity=2)
    diffs, res = _both(h, ASSIGN_LINE_VECTOR, args=[source], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    errors += _check_vector(h, dest, [(1, b't0', 10), (2, b't1', 20), (3, b't2', 30)])
    # self-assignment
    dest, block = _make_vector(h, [(7, b'self', 70), (8, b'again', 80)])
    diffs, res = _both(h, ASSIGN_LINE_VECTOR, args=[dest], regs={UC_X86_REG_ECX: dest}, ret='eax')
    if diffs:
        return diffs
    errors += _check_vector(h, dest, [(7, b'self', 70), (8, b'again', 80)])
    return errors


def test_construct_talk_entry(h):
    """0x4AA7E0 constructs the four texts empty and nulls the line vector; the numbers keep the memory."""
    entry = h.alloc(ENTRY)
    _pad(h, entry, ENTRY, 0xA5)
    diffs, res = _both(h, CONSTRUCT_ENTRY, regs={UC_X86_REG_ECX: entry}, ret='eax')
    if diffs:
        return diffs
    if res['eax'] != entry:
        return ['returned %#x, not this' % res['eax']]
    errors = []
    for name, off in (('first.text', 0x04 + 0x0C), ('first.text2', 0x04 + 0x2C),
                      ('second.text', 0x4C + 0x0C), ('second.text2', 0x4C + 0x2C)):
        if _get_str(h, entry + off) != b'':
            errors.append('%s is %r' % (name, _get_str(h, entry + off)))
    if struct.unpack('<III', h.uc.mem_read(entry + 0x98, 12)) != (0, 0, 0):
        errors.append('the line vector is %r' % (h.uc.mem_read(entry + 0x98, 12),))
    if _u32(h, entry) != 0xA5A5A5A5 or h.uc.mem_read(entry + 8, 1) != b'\xA5':
        errors.append('the untouched numbers changed')
    return errors


def test_destroy_talk_entry(h):
    """0x4AA870 frees the line block first, then destroys the second block's texts and the first's."""
    entry = h.alloc(ENTRY)
    _pad(h, entry, ENTRY)
    _put_entry(h, entry, 0x77, FIRST, SECOND, [(0, b'doomed', 12), (1, b'also doomed', 34)])
    diffs, res = _both(h, DESTROY_ENTRY, regs={UC_X86_REG_ECX: entry}, ret=None)
    if diffs:
        return diffs
    if struct.unpack('<III', h.uc.mem_read(entry + 0x98, 12)) != (0, 0, 0):
        return ['the line vector was not cleared: %r' % (h.uc.mem_read(entry + 0x98, 12),)]
    return []


def test_copy_construct_talk_entries(h):
    """0x4AAD90 copy-constructs [first, last) at dst and returns the position after them."""
    source = h.alloc(2 * ENTRY)
    _pad(h, source, 2 * ENTRY)
    _put_entry(h, source, 11, FIRST, SECOND, [(0, b'a0', 10)])
    _put_entry(h, source + ENTRY, 22, B1, B2, [(1, b'b0', 20), (0, b'b1', 30)])
    dst = h.alloc(2 * ENTRY)
    _pad(h, dst, 2 * ENTRY, 0xA5)
    diffs, res = _both(h, COPY_CONSTRUCT_ENTRIES, args=[source, source + 2 * ENTRY, dst], ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst + 2 * ENTRY:
        return ['returned %#x, wanted %#x' % (res['eax'], dst + 2 * ENTRY)]
    errors = _check_entry(h, dst, 11, FIRST, SECOND, [(0, b'a0', 10)])
    errors += _check_entry(h, dst + ENTRY, 22, B1, B2, [(1, b'b0', 20), (0, b'b1', 30)])
    return errors


def test_fill_construct_talk_entries(h):
    """0x4AAE30 constructs count copies of value at dst."""
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 33, SECOND, FIRST, [(1, b'fill', 66)])
    dst = h.alloc(2 * ENTRY)
    _pad(h, dst, 2 * ENTRY, 0xA5)
    diffs, res = _both(h, FILL_CONSTRUCT_ENTRIES, args=[dst, 2, value], ret=None)
    if diffs:
        return diffs
    errors = _check_entry(h, dst, 33, SECOND, FIRST, [(1, b'fill', 66)])
    errors += _check_entry(h, dst + ENTRY, 33, SECOND, FIRST, [(1, b'fill', 66)])
    return errors


def test_copy_backward_talk_entries(h):
    """0x4AAA20 assigns the entries from the last one down."""
    source = h.alloc(2 * ENTRY)
    _pad(h, source, 2 * ENTRY)
    _put_entry(h, source, 44, FIRST, B2, [(1, b'back a', 10)])
    _put_entry(h, source + ENTRY, 55, B1, SECOND, [(0, b'back b', 20)])
    dst = h.alloc(2 * ENTRY)
    _pad(h, dst, 2 * ENTRY)
    _put_entry(h, dst, 0, SECOND, FIRST, [])
    _put_entry(h, dst + ENTRY, 0, SECOND, FIRST, [])
    diffs, res = _both(h, COPY_BACKWARD_ENTRIES, args=[source, source + 2 * ENTRY, dst + 2 * ENTRY],
                       ret='eax')
    if diffs:
        return diffs
    if res['eax'] != dst:
        return ['returned %#x, wanted %#x' % (res['eax'], dst)]
    errors = _check_entry(h, dst, 44, FIRST, B2, [(1, b'back a', 10)])
    errors += _check_entry(h, dst + ENTRY, 55, B1, SECOND, [(0, b'back b', 20)])
    return errors


def test_fill_assign_talk_entries(h):
    """0x4AAB10 assigns copies of value over [first, last)."""
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 66, B2, B1, [(0, b'assigned', 5)])
    target = h.alloc(2 * ENTRY)
    _pad(h, target, 2 * ENTRY)
    _put_entry(h, target, 0, FIRST, SECOND, [])
    _put_entry(h, target + ENTRY, 0, FIRST, SECOND, [])
    diffs, res = _both(h, FILL_ASSIGN_ENTRIES, args=[target, target + 2 * ENTRY, value], ret=None)
    if diffs:
        return diffs
    errors = _check_entry(h, target, 66, B2, B1, [(0, b'assigned', 5)])
    errors += _check_entry(h, target + ENTRY, 66, B2, B1, [(0, b'assigned', 5)])
    return errors


def test_destroy_talk_entries(h):
    """0x4AAED0 destroys each entry of the range."""
    block = h.alloc(2 * ENTRY)
    _pad(h, block, 2 * ENTRY)
    _put_entry(h, block, 1, FIRST, SECOND, [(0, b'e0', 1)])
    _put_entry(h, block + ENTRY, 2, B1, B2, [(1, b'e1', 2)])
    diffs, res = _both(h, DESTROY_ENTRIES, args=[block, block + 2 * ENTRY], ret=None)
    if diffs:
        return diffs
    errors = []
    for i in range(2):
        if struct.unpack('<III', h.uc.mem_read(block + i * ENTRY + 0x98, 12)) != (0, 0, 0):
            errors.append('entry %d keeps its line vector' % i)
    return errors


def test_destroy_talk_entry_vector(h):
    """0x4AB100 destroys the entries, frees the block and clears the three pointers."""
    vec, block = _make_entries(h, [(1, FIRST, SECOND, [(0, b'v0', 1)]),
                                   (2, B1, B2, [(1, b'v1', 2)])])
    h.uc.mem_write(vec, struct.pack('<I', 0x5A5A5A5A))
    diffs, res = _both(h, DESTROY_ENTRY_VECTOR, regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if struct.unpack('<III', h.uc.mem_read(vec + 4, 12)) != (0, 0, 0):
        return ['the pointers are %r' % (h.uc.mem_read(vec + 4, 12),)]
    if _u32(h, vec) != 0x5A5A5A5A:
        return ['the allocator word changed']
    return []


def test_insert_talk_entries_grow(h):
    """0x4AB170 reallocates when the spare capacity is short: two entries grow to four."""
    vec, block = _make_entries(h, [(1, FIRST, SECOND, [(0, b'e0', 1)]),
                                   (2, B1, B2, [(1, b'e1', 2)])], capacity=2)
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 9, B2, FIRST, [(0, b'new', 3)])
    diffs, res = _both(h, INSERT_ENTRIES, args=[block + ENTRY, 2, value],
                       regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _entry_ids(h, vec) != [1, 9, 9, 2]:
        return ['the ids are %r' % _entry_ids(h, vec)]
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if limit - begin != 4 * ENTRY:
        return ['the new capacity is %d entries' % ((limit - begin) // ENTRY)]
    return _check_entry(h, begin + ENTRY, 9, B2, FIRST, [(0, b'new', 3)])


def test_insert_talk_entries_grow_empty(h):
    """0x4AB170 on a null vector allocates exactly size + count (two) entries."""
    vec = h.alloc(VECTOR)
    h.uc.mem_write(vec, bytes(VECTOR))
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 5, FIRST, SECOND, [])
    diffs, res = _both(h, INSERT_ENTRIES, args=[0, 2, value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _entry_ids(h, vec) != [5, 5]:
        return ['the ids are %r' % _entry_ids(h, vec)]
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(vec + 4, 12))
    if limit - begin != 2 * ENTRY:
        return ['the capacity is %d entries' % ((limit - begin) // ENTRY)]
    return []


def test_insert_talk_entries_short_tail(h):
    """0x4AB170 with a tail shorter than count constructs it after the new entries and fills the gap."""
    vec, block = _make_entries(h, [(0, FIRST, SECOND, []), (1, B1, B2, []), (2, SECOND, FIRST, []),
                                   (3, B2, B1, [])], capacity=6)
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 9, FIRST, B1, [])
    diffs, res = _both(h, INSERT_ENTRIES, args=[block + 3 * ENTRY, 2, value],
                       regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _entry_ids(h, vec) != [0, 1, 2, 9, 9, 3]:
        return ['the ids are %r' % _entry_ids(h, vec)]
    return []


def test_insert_talk_entries_long_tail(h):
    """0x4AB170 with a tail at least count moves its last entries first and shifts the middle back."""
    vec, block = _make_entries(h, [(0, FIRST, SECOND, []), (1, B1, B2, []), (2, SECOND, FIRST, []),
                                   (3, B2, B1, [])], capacity=6)
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 9, B1, SECOND, [])
    diffs, res = _both(h, INSERT_ENTRIES, args=[block + ENTRY, 2, value],
                       regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _entry_ids(h, vec) != [0, 9, 9, 1, 2, 3]:
        return ['the ids are %r' % _entry_ids(h, vec)]
    return []


def test_insert_talk_entry_at(h):
    """0x4AB530 inserts one entry and reports its position through result."""
    vec, block = _make_entries(h, [(1, FIRST, SECOND, []), (2, B1, B2, [])], capacity=4)
    result = h.alloc(4)
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 7, B2, FIRST, [])
    diffs, res = _both(h, INSERT_ENTRY_AT, args=[result, block + ENTRY, value],
                       regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _u32(h, result) != block + ENTRY:
        return ['the new entry is reported at %#x, wanted %#x' % (_u32(h, result), block + ENTRY)]
    if _entry_ids(h, vec) != [1, 7, 2]:
        return ['the ids are %r' % _entry_ids(h, vec)]
    return []


def test_push_talk_entry_spare(h):
    """0x4AB5C0 constructs into the spare slot when the capacity allows it."""
    vec, block = _make_entries(h, [(1, FIRST, SECOND, [])], capacity=3)
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 8, B1, B2, [(0, b'pushed', 4)])
    diffs, res = _both(h, PUSH_ENTRY, args=[value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _entry_ids(h, vec) != [1, 8]:
        return ['the ids are %r' % _entry_ids(h, vec)]
    return _check_entry(h, block + ENTRY, 8, B1, B2, [(0, b'pushed', 4)])


def test_push_talk_entry_grow(h):
    """0x4AB5C0 with a full vector takes the insertion path and reallocates."""
    vec, block = _make_entries(h, [(1, FIRST, SECOND, []), (2, B1, B2, [])], capacity=2)
    value = h.alloc(ENTRY)
    _pad(h, value, ENTRY)
    _put_entry(h, value, 8, B2, FIRST, [])
    diffs, res = _both(h, PUSH_ENTRY, args=[value], regs={UC_X86_REG_ECX: vec}, ret=None)
    if diffs:
        return diffs
    if _entry_ids(h, vec) != [1, 2, 8]:
        return ['the ids are %r' % _entry_ids(h, vec)]
    return []


# --- the loader object --------------------------------------------------------------------------------

def test_talkdat_ctor(h):
    """0x4AB470 stores the class vtable, nulls the vector and leaves EDX (and the allocator) alone."""
    obj = h.alloc(0x14)
    _pad(h, obj, 0x14, 0xA5)
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EDX: 0x12345678}
    diffs, res = _both(h, TALKDAT_CTOR, regs=regs, ret='eax')
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


def test_talkdat_dtor(h):
    """0x4AB4B0 destroys the talks, clears the vector and stores the singleton vtable last."""
    obj = h.alloc(0x14)
    _pad(h, obj, 0x14)
    h.uc.mem_write(obj, struct.pack('<I', VFT_CLASS))
    block = _alloc_entries(h, [(1, FIRST, SECOND, [(0, b'd0', 10)]),
                               (2, B1, B2, [(1, b'd1', 20)])], 2)
    h.uc.mem_write(obj + 8, struct.pack('<III', block, block + 2 * ENTRY, block + 2 * ENTRY))
    diffs, res = _both(h, TALKDAT_DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    if _u32(h, obj) != VFT_SINGLETON:
        return ['the vtable is %#x, wanted %#x' % (_u32(h, obj), VFT_SINGLETON)]
    if struct.unpack('<III', h.uc.mem_read(obj + 8, 12)) != (0, 0, 0):
        return ['the vector is %r' % (h.uc.mem_read(obj + 8, 12),)]
    errors = []
    for i in range(2):
        if struct.unpack('<III', h.uc.mem_read(block + i * ENTRY + 0x98, 12)) != (0, 0, 0):
            errors.append('entry %d keeps its line vector' % i)
    return errors
