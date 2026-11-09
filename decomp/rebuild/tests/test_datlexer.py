"""The dat scanner: flex 2.5's yylex (0x470410) and the input machinery it is generated with (0x46FB90,
0x46FC60, 0x46FD30, 0x46FEE0, 0x470020, 0x4700B0, 0x470150, 0x4702C0, 0x470390, 0x493130, 0x493140).

The scanner reads through the globals 0x6CA080 (the reader struct), 0x6CA078 (its character count), 0x6CA07C
(the character a token's NUL replaced), 0x6CA084 (the position), 0x6C9064 (yytext) and 0x6C9068 (a word token's
text).  A reader struct over a small in-memory text feeds every path without a file: 0x6CA278 (the bytes left of
the game file) is zero, so a refill ends at once.
"""
import struct
from unicorn.x86_const import UC_X86_REG_EAX

LEXER = 0x00470410
FIRST_CALL = 0x006C0F94
TOKEN_TEXT = 0x006C9068
TOKEN_NUMBER = 0x006C9060
TEXT_START = 0x006C9064
TOKEN_LENGTH = 0x006CA074
CHARS_READ = 0x006CA078
HOLD_CHAR = 0x006CA07C
CURRENT = 0x006CA080
POSITION = 0x006CA084
START_STATE = 0x006CA088
SWITCHED = 0x006CA070
LAST_POS = 0x006CA068
LAST_STATE = 0x006CA06C
INPUT_FILE = 0x006CA08C
OUTPUT_FILE = 0x006CA090
BYTES_LEFT = 0x006CA278
GAME_FILE = 0x006CA280


def _w32(h, addr, value):
    h.uc.mem_write(addr, struct.pack('<I', value & 0xFFFFFFFF))


def _w8(h, addr, value):
    h.uc.mem_write(addr, bytes((value & 0xFF,)))


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def _text(h):
    """the NUL-terminated text of the last word token"""
    return bytes(h.uc.mem_read(TOKEN_TEXT, 0x40)).split(b'\0')[0]


def _alloc(h, text):
    return h.alloc(0x28), h.alloc(len(text) + 2)


def _fill(h, state, data, text, n_chars=None, status=1, fill=1, size=0x4000, own=0):
    """a reader struct over text with the two closing NULs of a filled flex buffer"""
    h.uc.mem_write(data, text + b'\0\0')
    _w32(h, state + 0x00, 0)                                     # input file
    _w32(h, state + 0x04, data)                                  # ch_buf
    _w32(h, state + 0x08, data)                                  # buf_pos
    _w32(h, state + 0x0C, size)                                  # buf_size
    _w32(h, state + 0x10, len(text) if n_chars is None else n_chars)
    _w32(h, state + 0x14, own)                                   # own_buffer
    _w32(h, state + 0x18, 0)                                     # interactive
    _w32(h, state + 0x1C, 1)                                     # at_bol
    _w32(h, state + 0x20, fill)                                  # fill_buffer
    _w32(h, state + 0x24, status)                                # status
    _w32(h, CURRENT, state)


def _globals(h, data, n_chars, hold, first_call=0):
    _w32(h, FIRST_CALL, first_call)
    _w32(h, CHARS_READ, n_chars)
    _w8(h, HOLD_CHAR, hold)
    _w32(h, POSITION, data)
    _w32(h, TEXT_START, data)
    _w32(h, START_STATE, 1)
    _w32(h, SWITCHED, 0)
    _w32(h, TOKEN_LENGTH, 0)
    _w32(h, LAST_POS, 0)
    _w32(h, LAST_STATE, 0)
    _w32(h, TOKEN_NUMBER, 0)
    _w32(h, INPUT_FILE, 0)      # no file: a restart reads nothing and never touches stdio
    _w32(h, OUTPUT_FILE, 0)
    _w32(h, BYTES_LEFT, 0)      # nothing left of the game file: a refill is an end of file
    _w32(h, GAME_FILE + 0x24, 0)


def _lexer(h, state, data, text, first_call=0):
    _fill(h, state, data, text)
    _globals(h, data, len(text), text[0] if text else 0, first_call)


def _lex(h, text, first_call=0):
    """compare one yylex call and return the token of the replacement"""
    state, data = _alloc(h, text)

    def setup(h):
        _lexer(h, state, data, text, first_call)

    diffs = h.compare(LEXER, setup=setup)
    if diffs:
        return diffs, None
    setup(h)
    res = h.call(LEXER)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']], None
    return None, res


def test_first_call_sync(h):
    """the first call takes its state from the reader struct, not from the globals"""
    state, data = _alloc(h, b'Hello')

    def setup(h):
        _lexer(h, state, data, b'Hello')
        _w32(h, FIRST_CALL, 1)
        _w32(h, INPUT_FILE, 1)   # non-null, so the first call does not reach for stdio
        _w32(h, OUTPUT_FILE, 1)
        _w32(h, CHARS_READ, 0x777)
        _w8(h, HOLD_CHAR, 0x55)
        _w32(h, POSITION, 0x0DEAD000)
        _w32(h, TEXT_START, 0x0DEAD000)
        _w32(h, START_STATE, 0)

    diffs = h.compare(LEXER, setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(LEXER)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != 0x104:
        return ['token %#x, wanted a word' % res['eax']]
    if _u32(h, FIRST_CALL) != 0:
        return ['the first-call flag was not cleared']
    if _u32(h, CHARS_READ) != 5 or _u32(h, START_STATE) != 1:
        return ['characters %d, start state %d' % (_u32(h, CHARS_READ), _u32(h, START_STATE))]
    if _u32(h, INPUT_FILE) != 0:
        return ['the input file is not the reader struct\'s']
    if _text(h) != b'Hello':
        return ['text %r' % _text(h)]
    return None


def test_word_token(h):
    diffs, res = _lex(h, b'Hello')
    if diffs:
        return diffs
    if res['eax'] != 0x104:
        return ['token %#x, wanted a word' % res['eax']]
    if _text(h) != b'Hello':
        return ['text %r' % _text(h)]
    if _u32(h, TOKEN_LENGTH) != 5:
        return ['token length %d' % _u32(h, TOKEN_LENGTH)]
    return None


def test_number_token(h):
    diffs, res = _lex(h, b'2.5')
    if diffs:
        return diffs
    if res['eax'] != 0x105:
        return ['token %#x, wanted a number' % res['eax']]
    if _f32(h, TOKEN_NUMBER) != 2.5:
        return ['number %r' % _f32(h, TOKEN_NUMBER)]
    return None


def test_quoted_string(h):
    """the action reads to the closing quote and drops the whitespace characters"""
    diffs, res = _lex(h, b'"A\tB\nC"')
    if diffs:
        return diffs
    if res['eax'] != 0x104:
        return ['token %#x, wanted a word' % res['eax']]
    if _text(h) != b'ABC':
        return ['text %r' % _text(h)]
    return None


def test_block_delimiters(h):
    for text, token in ((b'{', 0x102), (b'}', 0x103)):
        diffs, res = _lex(h, text)
        if diffs:
            return diffs
        if res['eax'] != token:
            return ['%r gave %#x, wanted %#x' % (text, res['eax'], token)]
    return None


def test_keyword(h):
    """#scene is a record keyword (0x141), not a word; the game file's reader has lowercased the '#' word"""
    diffs, res = _lex(h, b'#scene')
    if diffs:
        return diffs
    if res['eax'] != 0x141:
        return ['token %#x, wanted 0x141' % res['eax']]
    return None


def test_whitespace(h):
    diffs, res = _lex(h, b' \t\r\nHello')
    if diffs:
        return diffs
    if res['eax'] != 0x104 or _text(h) != b'Hello':
        return ['token %#x text %r' % (res['eax'], _text(h))]
    return None


def test_line_comment(h):
    diffs, res = _lex(h, b'// x\nHello')
    if diffs:
        return diffs
    if res['eax'] != 0x104 or _text(h) != b'Hello':
        return ['token %#x text %r' % (res['eax'], _text(h))]
    return None


def test_block_comment(h):
    diffs, res = _lex(h, b'/* x */ Hello')
    if diffs:
        return diffs
    if res['eax'] != 0x104 or _text(h) != b'Hello':
        return ['token %#x text %r' % (res['eax'], _text(h))]
    return None


def test_end_of_file(h):
    for text in (b'', b' \t\r\n'):
        diffs, res = _lex(h, text)
        if diffs:
            return diffs
        if res['eax'] != 0:
            return ['%r gave %#x, wanted end of file' % (text, res['eax'])]
    return None


def test_flush_buffer(h):
    state, data = _alloc(h, b'abc')

    def setup(h):
        _fill(h, state, data, b'abc')
        _w32(h, state + 0x00, 0x12345678)
        _w32(h, state + 0x08, data + 1)
        _w32(h, state + 0x1C, 0)
        _globals(h, data, 0x77, 0x41)
        _w32(h, CHARS_READ, 7)
        _w32(h, POSITION, data + 2)
        _w32(h, TEXT_START, data + 2)

    diffs = h.compare(0x0046FD30, args=[state], setup=setup, ret=None)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x0046FD30, args=[state])
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    ch_buf = _u32(h, state + 0x04)
    if _u32(h, state + 0x10) != 0 or _u32(h, state + 0x24) != 0:
        return ['n_chars %d status %d' % (_u32(h, state + 0x10), _u32(h, state + 0x24))]
    if _u32(h, state + 0x08) != ch_buf or _u32(h, state + 0x1C) != 1:
        return ['buf_pos %08X at_bol %d' % (_u32(h, state + 0x08), _u32(h, state + 0x1C))]
    if bytes(h.uc.mem_read(ch_buf, 2)) != b'\0\0':
        return ['the first two buffer bytes are not NULs']
    if _u32(h, CHARS_READ) != 0 or _u32(h, TEXT_START) != ch_buf or _u32(h, POSITION) != ch_buf:
        return ['the globals did not follow the buffer']
    if _u32(h, INPUT_FILE) != 0x12345678 or h.uc.mem_read(HOLD_CHAR, 1) != b'\0':
        return ['input file %08X hold %02X' % (_u32(h, INPUT_FILE), h.uc.mem_read(HOLD_CHAR, 1)[0])]
    return None


def test_init_buffer(h):
    state, data = _alloc(h, b'')

    def setup(h):
        _fill(h, state, data, b'')
        _w32(h, state + 0x00, 0x12345678)
        _w32(h, state + 0x20, 0)
        _globals(h, data, 0x77, 0x41)

    diffs = h.compare(0x0046FEE0, args=[state, 0], setup=setup)
    if diffs:
        return diffs
    setup(h)
    h.call(0x0046FEE0, args=[state, 0])
    if _u32(h, state + 0x00) != 0 or _u32(h, state + 0x20) != 1 or _u32(h, state + 0x18) != 0:
        return ['input %08X fill %d interactive %d' % (_u32(h, state + 0x00), _u32(h, state + 0x20),
                                                       _u32(h, state + 0x18))]
    if _u32(h, state + 0x24) != 0 or bytes(h.uc.mem_read(data, 2)) != b'\0\0':
        return ['status %d or the flushed buffer bytes' % _u32(h, state + 0x24)]
    return None


def test_create_buffer(h):
    dummy = h.alloc(2, b'\0\0')

    def setup(h):
        _globals(h, dummy, 0, 0)
        _w32(h, CURRENT, 0)

    diffs = h.compare(0x00470020, args=[0, 0x20], setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x00470020, args=[0, 0x20])
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    buf = res['eax']
    if not buf:
        return ['no buffer']
    ch_buf = _u32(h, buf + 0x04)
    if _u32(h, buf + 0x0C) != 0x20:
        return ['buf_size %d' % _u32(h, buf + 0x0C)]
    if not ch_buf or bytes(h.uc.mem_read(ch_buf, 2)) != b'\0\0':
        return ['ch_buf %08X is not a flushed buffer' % ch_buf]
    if _u32(h, buf + 0x08) != ch_buf or _u32(h, buf + 0x1C) != 1:
        return ['buf_pos %08X at_bol %d' % (_u32(h, buf + 0x08), _u32(h, buf + 0x1C))]
    if _u32(h, buf + 0x10) != 0 or _u32(h, buf + 0x14) != 1 or _u32(h, buf + 0x20) != 1:
        return ['n_chars %d own %d fill %d' % (_u32(h, buf + 0x10), _u32(h, buf + 0x14), _u32(h, buf + 0x20))]
    if _u32(h, buf + 0x18) != 0 or _u32(h, buf + 0x24) != 0:
        return ['interactive %d status %d' % (_u32(h, buf + 0x18), _u32(h, buf + 0x24))]
    return None


def test_restart(h):
    state, data = _alloc(h, b'')

    def setup(h):
        h.uc.mem_write(data, b'\0\0')
        _fill(h, state, data, b'')
        _w32(h, state + 0x00, 0x12345678)
        _globals(h, data, 0x77, 0x41)

    diffs = h.compare(0x004700B0, args=[0], setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x004700B0, args=[0])
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    ch_buf = _u32(h, state + 0x04)
    if res['eax'] != ch_buf or _u32(h, TEXT_START) != ch_buf:
        return ['restart returned %08X, ch_buf %08X' % (res['eax'], ch_buf)]
    if _u32(h, state + 0x00) != 0 or _u32(h, state + 0x20) != 1 or _u32(h, state + 0x18) != 0:
        return ['input %08X fill %d interactive %d' % (_u32(h, state + 0x00), _u32(h, state + 0x20),
                                                       _u32(h, state + 0x18))]
    if _u32(h, CHARS_READ) != 0 or _u32(h, INPUT_FILE) != 0 or _u32(h, POSITION) != ch_buf:
        return ['the globals did not follow the restart']
    return None


def _input_case(h, text, position, hold, n_chars=None):
    state, data = _alloc(h, text)

    def setup(h):
        _fill(h, state, data, text, n_chars=n_chars)
        _globals(h, data, len(text) if n_chars is None else n_chars, hold)
        _w32(h, POSITION, data + position)

    diffs = h.compare(0x004702C0, setup=setup)
    if diffs:
        return diffs, None, data, state
    setup(h)
    res = h.call(0x004702C0)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']], None, data, state
    return None, res, data, state


def test_input(h):
    """a character of the buffer is returned and replaced with a NUL; the next one is held"""
    diffs, res, data, _ = _input_case(h, b'Abc', 0, ord('A'))
    if diffs:
        return diffs
    if res['eax'] != ord('A'):
        return ['read %#x, wanted A' % res['eax']]
    if bytes(h.uc.mem_read(data, 5)) != b'\0bc\0\0':
        return ['buffer %r' % bytes(h.uc.mem_read(data, 5))]
    if _u32(h, POSITION) != data + 1 or h.uc.mem_read(HOLD_CHAR, 1) != b'b':
        return ['position %08X hold %r' % (_u32(h, POSITION), h.uc.mem_read(HOLD_CHAR, 1))]
    return None


def test_input_embedded_nul(h):
    """a NUL inside the data is a character of its own, not the end of the buffer"""
    diffs, res, data, _ = _input_case(h, b'A\0c', 1, 0)
    if diffs:
        return diffs
    if res['eax'] != 0:
        return ['read %#x, wanted 0' % res['eax']]
    if _u32(h, POSITION) != data + 2 or h.uc.mem_read(HOLD_CHAR, 1) != b'c':
        return ['position %08X hold %r' % (_u32(h, POSITION), h.uc.mem_read(HOLD_CHAR, 1))]
    return None


def test_input_at_end_of_file(h):
    """at the buffer's end a refill runs into the end of the game file; yywrap then reports 0xffffffff"""
    diffs, res, data, state = _input_case(h, b'abc', 3, 0)
    if diffs:
        return diffs
    if res['eax'] != 0xFFFFFFFF:
        return ['read %#x, wanted 0xffffffff' % res['eax']]
    if _u32(h, CHARS_READ) != 0 or _u32(h, POSITION) != _u32(h, state + 0x04):
        return ['the restart did not rewind to the buffer start']
    return None


def test_get_next_buffer(h):
    state, data = _alloc(h, b'abcdef')

    def setup(h):
        _fill(h, state, data, b'abcdef')
        _globals(h, data, 6, ord('a'))
        _w32(h, POSITION, data + 4)

    diffs = h.compare(0x00470150, setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x00470150)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != 2:
        return ['result %d, wanted the last-match code' % res['eax']]
    if _u32(h, state + 0x24) != 2:
        return ['status %d, wanted the end-of-file-pending one' % _u32(h, state + 0x24)]
    if _u32(h, CHARS_READ) != 3 or bytes(h.uc.mem_read(data, 6)) != b'abc\0\0f':
        return ['characters %d buffer %r' % (_u32(h, CHARS_READ), bytes(h.uc.mem_read(data, 6)))]
    if _u32(h, TEXT_START) != data:
        return ['yytext %08X is not the buffer' % _u32(h, TEXT_START)]
    return None


def test_get_next_buffer_end_of_file(h):
    """only the character before the end was matched: the refill restarts and reports the end of the file"""
    state, data = _alloc(h, b'abcdef')

    def setup(h):
        _fill(h, state, data, b'abcdef')
        _globals(h, data, 6, ord('a'))
        _w32(h, POSITION, data + 1)
        _w32(h, TEXT_START, data)

    diffs = h.compare(0x00470150, setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x00470150)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != 1:
        return ['result %d, wanted the end-of-file code' % res['eax']]
    if _u32(h, CHARS_READ) != 0 or bytes(h.uc.mem_read(data, 2)) != b'\0\0':
        return ['characters %d buffer %r' % (_u32(h, CHARS_READ), bytes(h.uc.mem_read(data, 2)))]
    return None


def test_get_next_buffer_without_refill(h):
    """a buffer that does not fill (an uninitialised one) only reports whether more than one character matched"""
    state, data = _alloc(h, b'abcdef')

    def setup(h):
        _fill(h, state, data, b'abcdef', fill=0)
        _globals(h, data, 6, ord('a'))
        _w32(h, POSITION, data + 4)

    diffs = h.compare(0x00470150, setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x00470150)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != 2:
        return ['result %d, wanted 2' % res['eax']]
    return None


def test_skip_comment(h):
    state, data = _alloc(h, b'/* x */ rest')

    def setup(h):
        _fill(h, state, data, b'/* x */ rest')
        _globals(h, data, 12, ord(' '))
        _w32(h, POSITION, data + 2)

    diffs = h.compare(0x00470390, setup=setup, ret=None)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x00470390)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, POSITION) != data + 7 or h.uc.mem_read(HOLD_CHAR, 1) != b' ':
        return ['stopped at %08X with %r held, wanted the character after the comment'
                % (_u32(h, POSITION), h.uc.mem_read(HOLD_CHAR, 1))]
    return None


def test_previous_state(h):
    state, data = _alloc(h, b'abc')

    def setup(h):
        _fill(h, state, data, b'abc')
        _globals(h, data, 3, ord('a'))
        _w32(h, POSITION, data + 3)

    diffs = h.compare(0x0046FB90, setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x0046FB90)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != 43:
        return ['state %d, wanted the word state 43' % res['eax']]
    if _u32(h, LAST_POS) != data + 2 or _u32(h, LAST_STATE) != 43:
        return ['last accepting position %08X state %d' % (_u32(h, LAST_POS), _u32(h, LAST_STATE))]
    return None


def test_nul_transition(h):
    state, data = _alloc(h, b'')

    def setup(h):
        h.uc.mem_write(data, b'\0\0')
        _fill(h, state, data, b'')
        _globals(h, data, 0, 0)

    diffs = h.compare(0x0046FC60, regs={UC_X86_REG_EAX: 1}, setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x0046FC60, regs={UC_X86_REG_EAX: 1})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != 4:
        return ['state %#x, wanted the end-of-buffer path 4' % res['eax']]
    # the word state jams on the NUL: the scan has to take the last accepting match instead
    diffs = h.compare(0x0046FC60, regs={UC_X86_REG_EAX: 43}, setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x0046FC60, regs={UC_X86_REG_EAX: 43})
    if res['eax'] != 0:
        return ['state %#x, wanted the jam at the word state' % res['eax']]
    return None


def test_wrap(h):
    diffs = h.compare(0x00493130)
    if diffs:
        return diffs
    res = h.call(0x00493130)
    if res['eax'] != 1:
        return ['yywrap returned %d' % res['eax']]
    return None


def _make_stream(h, size):
    """the file object the global CGameFile (0x6CA280) reads through"""
    read = h.alloc(3, b'\xc2\x08\x00')                       # the stream's read: ret 8, it writes nothing
    vtable = h.alloc(8, struct.pack('<II', 0, read))
    return h.alloc(0xC, struct.pack('<III', vtable, 0, size))


def _read_game_file(h, buf, left, n):
    stream = _make_stream(h, left)

    def setup(h):
        _w32(h, BYTES_LEFT, left)
        _w32(h, GAME_FILE + 0x24, stream)

    diffs = h.compare(0x00493140, args=[buf, n], setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(0x00493140, args=[buf, n])
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != min(left, n):
        return ['read %d bytes, wanted %d' % (res['eax'], min(left, n))]
    if _u32(h, BYTES_LEFT) != left - min(left, n):
        return ['bytes left %d' % _u32(h, BYTES_LEFT)]
    return None


def test_read_game_file(h):
    """the stream's bytes stay put; the '#' words are lowercased and the result is NUL-terminated"""
    buf = h.alloc(16, b'#AbC x\0\0\0\0\0\0\0\0\0')
    diffs = _read_game_file(h, buf, 6, 6)
    if diffs:
        return diffs
    if bytes(h.uc.mem_read(buf, 7)) != b'#abc x\0':
        return ['buffer %r' % bytes(h.uc.mem_read(buf, 7))]
    return None


def test_read_game_file_limited(h):
    """never more than the bytes left of the game file, whatever the caller asks for"""
    buf = h.alloc(16, b'#HiThere\0\0\0\0\0\0\0\0')
    diffs = _read_game_file(h, buf, 3, 8)
    if diffs:
        return diffs
    if bytes(h.uc.mem_read(buf, 4)) != b'#hi\0':
        return ['buffer %r' % bytes(h.uc.mem_read(buf, 4))]
    return None


def test_read_game_file_closed(h):
    """no bytes left: the stream is not touched at all"""
    buf = h.alloc(8, b'#AbC\0\0\0\0')
    _w32(h, BYTES_LEFT, 0)
    diffs = h.compare(0x00493140, args=[buf, 4])
    if diffs:
        return diffs
    res = h.call(0x00493140, args=[buf, 4])
    if res['eax'] != 0:
        return ['read %d bytes from an empty game file' % res['eax']]
    if bytes(h.uc.mem_read(buf, 4)) != b'#AbC':
        return ['the buffer was touched: %r' % bytes(h.uc.mem_read(buf, 4))]
    return None
