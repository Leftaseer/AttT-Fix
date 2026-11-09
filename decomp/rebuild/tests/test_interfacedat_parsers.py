"""The interface dat keyword parsers (0x4A5F00 / 0x4A5FD0 / 0x4A60A0 / 0x4A6C00 / 0x4A61C0 / 0x4A63B0) and the
element parsers they share (0x4A1A60 / 0x4A1B10), driven by the game's own lexer (0x470410).

The lexer reads through the globals 0x6CA080 (its reader struct), 0x6CA07C/0x6CA084 (the lookahead byte and the
position), 0x6CA088 (the DFA start state) and writes the token text into 0x6C9068.  Pointing the reader struct at a
small in-memory text feeds the parsers without a file.  A quoted word is token 0x104, a number 0x105, '}' 0x103.
"""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

LEXER = 0x00470410
TOKEN = 0x006CA2BC
TOKEN_TEXT = 0x006C9068
TOKEN_NUMBER = 0x006C9060

STRING_4C = (0x00, 0x1C)
STRING_48 = (0x00, 0x1C)


def _w32(h, addr, value):
    h.uc.mem_write(addr, struct.pack('<I', value & 0xFFFFFFFF))


def _lexer(h, text):
    """point the lexer at text: the reader struct [2] is the position, [4] the byte count"""
    buf = h.alloc(len(text) + 1, text + b'\0')
    state = h.alloc(0x40, bytes(0x40))
    _w32(h, state + 8, buf)
    _w32(h, state + 16, len(text))
    _w32(h, 0x006CA080, state)
    _w32(h, 0x006CA078, len(text))
    _w32(h, 0x006CA07C, text[0])
    _w32(h, 0x006CA084, buf)
    _w32(h, 0x006CA088, 1)   # the DFA start state
    _w32(h, 0x006C0F94, 0)   # no file behind it and no re-initialisation
    _w32(h, 0x006CA070, 0)
    _w32(h, 0x006CA08C, 0)
    _w32(h, 0x006CA090, 0)


def _advance(h):
    """lex the first token, so the element parsers find their name token current"""
    res = h.call(LEXER)
    if res['fault']:
        raise AssertionError('lexer: %s' % res['fault'])
    if res['eax'] != 0x104:
        raise AssertionError('first token %08X, wanted a word' % res['eax'])


def _put_string(h, addr, text=b''):
    """an empty (or short) VC8 string: allocator, inline buffer, size, capacity"""
    assert len(text) < 16
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _get_string(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    raw = h.uc.mem_read(addr + 4, 4)
    ptr = addr + 4 if cap < 16 else struct.unpack('<I', raw)[0]
    return bytes(h.uc.mem_read(ptr, size))


def _f32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _get_f32(h, addr):
    return _f32(h, addr)


def f32(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _element(h, size, string_offsets, text=()):
    obj = h.alloc(size, bytes(size))
    for off, s in zip(string_offsets, text):
        _put_string(h, obj + off, s)
    return obj


def _collection(h):
    obj = h.alloc(0x2C, bytes(0x2C))
    _put_string(h, obj)
    return obj


def _run(h, addr, obj, text, advance, ret='eax'):
    def setup(h):
        _lexer(h, text)
        if advance:
            _advance(h)

    diffs = h.compare(addr, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=ret)
    if diffs:
        return diffs
    setup(h)
    res = h.call(addr, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    return None


def _vector(h, addr):
    begin, end, limit = struct.unpack('<III', h.uc.mem_read(addr + 4, 12))
    return begin, end, limit


def test_item_4c(h):
    text = b'AbC "Def" 2 2.5 3.25 4.75 5.5 }'
    obj = _element(h, 0x4C, STRING_4C)
    diffs = _run(h, 0x004A1A60, obj, text, advance=True)
    if diffs:
        return diffs
    if _get_string(h, obj) != b'abc':
        return ['name %r' % _get_string(h, obj)]
    if _get_string(h, obj + 0x1C) != b'Def':
        return ['text %r' % _get_string(h, obj + 0x1C)]
    if h.uc.mem_read(obj + 0x38, 1)[0] != 2:
        return ['flag %02X' % h.uc.mem_read(obj + 0x38, 1)[0]]
    want = [f32(2.5), f32(3.25), f32(4.75), f32(5.5)]
    got = [_get_f32(h, obj + 0x3C + 4 * i) for i in range(4)]
    if got != want:
        return ['numbers %r, wanted %r' % (got, want)]
    return None


def test_item_4c_without_pair(h):
    text = b'AbC "Def" 2 2.5 3.25 }'
    obj = _element(h, 0x4C, STRING_4C)
    diffs = _run(h, 0x004A1A60, obj, text, advance=True)
    if diffs:
        return diffs
    if [_get_f32(h, obj + 0x3C + 4 * i) for i in range(4)] != [f32(2.5), f32(3.25), 0, 0]:
        return ['numbers are not 2.5, 3.25, 0, 0']
    return None


def test_item_48(h):
    text = b'AbC "Def" 1.5 2.5 3.5 4.5 }'
    obj = _element(h, 0x48, STRING_48)
    diffs = _run(h, 0x004A1B10, obj, text, advance=True)
    if diffs:
        return diffs
    if _get_string(h, obj) != b'abc' or _get_string(h, obj + 0x1C) != b'Def':
        return ['strings %r %r' % (_get_string(h, obj), _get_string(h, obj + 0x1C))]
    want = [f32(1.5), f32(2.5), f32(3.5), f32(4.5)]
    if [_get_f32(h, obj + 0x38 + 4 * i) for i in range(4)] != want:
        return ['numbers differ']
    return None


def test_items_4c(h):
    text = b'"Title" { AbC "Def" 1 2 3 4 5 }'
    obj = _collection(h)
    diffs = _run(h, 0x004A5F00, obj, text, advance=False, ret=None)
    if diffs:
        return diffs
    if _get_string(h, obj) != b'Title':
        return ['title %r' % _get_string(h, obj)]
    begin, end, limit = _vector(h, obj + 0x1C)
    if not begin or (end - begin) != 0x4C or not limit:
        return ['vector begin %08X end %08X limit %08X' % (begin, end, limit)]
    if _get_string(h, begin) != b'abc' or _get_string(h, begin + 0x1C) != b'Def':
        return ['element strings %r %r' % (_get_string(h, begin), _get_string(h, begin + 0x1C))]
    if [_get_f32(h, begin + 0x3C + 4 * i) for i in range(4)] != [f32(2.0), f32(3.0), f32(4.0), f32(5.0)]:
        return ['element numbers differ']
    return None


def test_items_48(h):
    text = b'"Title" { AbC "Def" 1 2 3 4 }'
    obj = _collection(h)
    diffs = _run(h, 0x004A5FD0, obj, text, advance=False, ret=None)
    if diffs:
        return diffs
    begin, end, _ = _vector(h, obj + 0x1C)
    if not begin or (end - begin) != 0x48:
        return ['vector begin %08X end %08X' % (begin, end)]
    if [_get_f32(h, begin + 0x38 + 4 * i) for i in range(4)] != [f32(1.0), f32(2.0), f32(3.0), f32(4.0)]:
        return ['element numbers differ']
    return None


def test_items_2c(h):
    text = b'"Title" { AbC 1 2 3 4 }'
    obj = _collection(h)
    diffs = _run(h, 0x004A60A0, obj, text, advance=False, ret=None)
    if diffs:
        return diffs
    begin, end, _ = _vector(h, obj + 0x1C)
    if not begin or (end - begin) != 0x2C:
        return ['vector begin %08X end %08X' % (begin, end)]
    if _get_string(h, begin) != b'AbC':
        return ['the 0x145 names are not lowercased: %r' % _get_string(h, begin)]
    if [_get_f32(h, begin + 0x1C + 4 * i) for i in range(4)] != [f32(1.0), f32(2.0), f32(3.0), f32(4.0)]:
        return ['element numbers differ']
    return None


def test_items_64(h):
    text = b'{ Name 0.5 1.5 u "s1" 2.5 "s2" }'
    obj = h.alloc(0x10, bytes(0x10))
    diffs = _run(h, 0x004A6C00, obj, text, advance=False, ret=None)
    if diffs:
        return diffs
    begin, end, _ = _vector(h, obj)
    if not begin or (end - begin) != 0x64:
        return ['vector begin %08X end %08X' % (begin, end)]
    if _get_string(h, begin) != b'Name':
        return ['name %r' % _get_string(h, begin)]
    if h.uc.mem_read(begin + 0x24, 1) != b'u':
        return ['flag %r' % h.uc.mem_read(begin + 0x24, 1)]
    if _get_string(h, begin + 0x28) != b's1' or _get_string(h, begin + 0x48) != b's2':
        return ['strings %r %r' % (_get_string(h, begin + 0x28), _get_string(h, begin + 0x48))]
    if [_get_f32(h, begin + 0x1C), _get_f32(h, begin + 0x20), _get_f32(h, begin + 0x44)] != \
            [f32(0.5), f32(1.5), f32(2.5)]:
        return ['element numbers differ']
    return None


def test_items_e4(h):
    text = b'{ AbC 1 2 u "s1" 3 "s2" 4 5 v "s3" 6 "s4" "s5" }'
    obj = h.alloc(0x10, bytes(0x10))
    diffs = _run(h, 0x004A61C0, obj, text, advance=False, ret=None)
    if diffs:
        return diffs
    begin, end, _ = _vector(h, obj)
    if not begin or (end - begin) != 0xE4:
        return ['vector begin %08X end %08X' % (begin, end)]
    if _get_string(h, begin) != b'AbC':
        return ['name %r' % _get_string(h, begin)]
    if _get_string(h, begin + 0xC8) != b'ab':
        return ['the lowercased name without its last character is %r'
                % _get_string(h, begin + 0xC8)]
    if h.uc.mem_read(begin + 0x24, 1) != b'u' or h.uc.mem_read(begin + 0x6C, 1) != b'v':
        return ['flags %r %r' % (h.uc.mem_read(begin + 0x24, 1), h.uc.mem_read(begin + 0x6C, 1))]
    strings = [_get_string(h, begin + off) for off in (0x28, 0x48, 0x70, 0x90, 0xAC)]
    if strings != [b's1', b's2', b's3', b's4', b's5']:
        return ['strings %r' % (strings,)]
    if [_get_f32(h, begin + off) for off in (0x1C, 0x20, 0x44, 0x64, 0x68, 0x8C)] != \
            [f32(1.0), f32(2.0), f32(3.0), f32(4.0), f32(5.0), f32(6.0)]:
        return ['element numbers differ']
    return None


def test_items_118(h):
    text = b'{ AbC 1 2 u "s1" 3 "s2" 4 5 6 v "s3" 7 "s4" 8 "s5" 9 10 w "s6" 11 "s7" }'
    obj = h.alloc(0x10, bytes(0x10))
    diffs = _run(h, 0x004A63B0, obj, text, advance=False, ret=None)
    if diffs:
        return diffs
    begin, end, _ = _vector(h, obj)
    if not begin or (end - begin) != 0x118:
        return ['vector begin %08X end %08X' % (begin, end)]
    if h.uc.mem_read(begin + 0x24, 1) != b'u' or h.uc.mem_read(begin + 0x70, 1) != b'v' \
            or h.uc.mem_read(begin + 0xD8, 1) != b'w':
        return ['flags differ']
    strings = [_get_string(h, begin + off) for off in (0x28, 0x48, 0x74, 0x94, 0xB4, 0xDC, 0xFC)]
    if strings != [b's1', b's2', b's3', b's4', b's5', b's6', b's7']:
        return ['strings %r' % (strings,)]
    numbers = [_get_f32(h, begin + off) for off in (0x1C, 0x20, 0x44, 0x64, 0x68, 0x6C, 0x90, 0xB0, 0xD0, 0xD4, 0xF8)]
    if numbers != [f32(float(i)) for i in range(1, 12)]:
        return ['element numbers %r' % (numbers,)]
    return None


def test_floats_149(h):
    for text, want in ((b'1 2 3 4 }', [f32(1.0), f32(2.0), f32(3.0), f32(4.0)]),
                       (b'1 2 }', [f32(1.0), f32(2.0), 0, 0])):
        obj = h.alloc(0x10, bytes(0x10))
        diffs = h.compare(0x004A1CA0, regs={UC_X86_REG_ECX: obj}, setup=lambda h: _lexer(h, text))
        if diffs:
            return diffs
        _lexer(h, text)
        res = h.call(0x004A1CA0, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        got = [struct.unpack('<I', h.uc.mem_read(obj + 4 * i, 4))[0] for i in range(4)]
        if got != want:
            return ['%r: %r, wanted %r' % (text, got, want)]
    return None
