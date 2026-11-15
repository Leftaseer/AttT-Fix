"""The rest of the dat scanner's buffer API in datlexer.cpp: 0x46FD00 loads the globals from the current buffer,
0x46FDF0 / 0x46FE10 are the word and number token actions, 0x46FE30 switches the current buffer, 0x46FEA0 deletes
one, and 0x46FF30 / 0x46FFB0 / 0x470080 make one over caller memory, over a copy of bytes and over a copy of a
text.  The game never calls these (yylex inlines the parts it needs); they complete flex's generated skeleton."""
import struct

LOAD_STATE = 0x0046FD00
COPY_WORD = 0x0046FDF0
SCAN_NUMBER = 0x0046FE10
SWITCH_BUFFER = 0x0046FE30
DELETE_BUFFER = 0x0046FEA0
SCAN_BUFFER = 0x0046FF30
SCAN_BYTES = 0x0046FFB0
SCAN_STRING = 0x00470080
CREATE_BUFFER = 0x00470020

TOKEN_TEXT = 0x006C9068
TOKEN_NUMBER = 0x006C9060
TEXT_START = 0x006C9064
CHARS_READ = 0x006CA078
HOLD_CHAR = 0x006CA07C
CURRENT = 0x006CA080
POSITION = 0x006CA084
SWITCHED = 0x006CA070
INPUT_FILE = 0x006CA08C


def _w32(h, addr, value):
    h.uc.mem_write(addr, struct.pack('<I', value & 0xFFFFFFFF))


def _w8(h, addr, value):
    h.uc.mem_write(addr, bytes((value & 0xFF,)))


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def _buffer(h, state, data, text, buf_pos=0, n_chars=None, own=0, size=0x40, status=1, at_bol=1, fill=1,
            input_file=0):
    """a scanner buffer over text (which has to keep two closing NULs)"""
    _w32(h, state + 0x00, input_file)
    _w32(h, state + 0x04, data)
    _w32(h, state + 0x08, data + buf_pos)
    _w32(h, state + 0x0C, size)
    _w32(h, state + 0x10, len(text) if n_chars is None else n_chars)
    _w32(h, state + 0x14, own)
    _w32(h, state + 0x18, 0)
    _w32(h, state + 0x1C, at_bol)
    _w32(h, state + 0x20, fill)
    _w32(h, state + 0x24, status)


def _globals(h):
    """the scanner's globals before the buffer state is loaded"""
    _w32(h, CHARS_READ, 0x77)
    _w32(h, TEXT_START, 0)
    _w32(h, POSITION, 0)
    _w8(h, HOLD_CHAR, 0xEE)
    _w32(h, INPUT_FILE, 0)
    _w32(h, SWITCHED, 0)


def test_load_buffer_state(h):
    state = h.alloc(0x28)
    data = h.alloc(8, b'abcdef\0\0')

    def setup(h):
        _buffer(h, state, data, b'abcdef', buf_pos=2, n_chars=5, input_file=0x12345678)
        _w32(h, CURRENT, state)
        _globals(h)

    diffs = h.compare(LOAD_STATE, setup=setup, ret=None)
    if diffs:
        return diffs
    setup(h)
    res = h.call(LOAD_STATE)
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if _u32(h, CHARS_READ) != 5:
        return ['chars read %d' % _u32(h, CHARS_READ)]
    if _u32(h, TEXT_START) != data + 2 or _u32(h, POSITION) != data + 2:
        return ['text %08X position %08X (want %08X)' % (_u32(h, TEXT_START), _u32(h, POSITION), data + 2)]
    if _u32(h, INPUT_FILE) != 0x12345678:
        return ['input file %08X' % _u32(h, INPUT_FILE)]
    if h.uc.mem_read(HOLD_CHAR, 1)[0] != ord('c'):
        return ['hold character %02X' % h.uc.mem_read(HOLD_CHAR, 1)[0]]
    return None


def test_copy_word(h):
    for text in (b'hello', b'', b'x' * 31):
        source = h.alloc(64, text + b'\0')

        def setup(h):
            _w32(h, TEXT_START, source)

        diffs = h.compare(COPY_WORD, setup=setup, ret=None)
        if diffs:
            return ['%r: %s' % (text, d) for d in diffs]
        setup(h)
        res = h.call(COPY_WORD)
        if res['fault']:
            return ['%r: replacement faulted: %s' % (text, res['fault'])]
        copied = bytes(h.uc.mem_read(TOKEN_TEXT, len(text) + 1))
        if copied != text + b'\0':
            return ['%r: copied %r' % (text, copied)]
    return None


def test_scan_number(h):
    for text, want in ((b'12.5', 12.5), (b'-3', -3.0), (b'1e3', 1000.0), (b'0.25', 0.25), (b'abc', 0.0),
                       (b'', 0.0)):
        source = h.alloc(16, text + b'\0')

        def setup(h):
            _w32(h, TEXT_START, source)
            _w32(h, TOKEN_NUMBER, 0)

        diffs = h.compare(SCAN_NUMBER, setup=setup, ret=None)
        if diffs:
            return ['%r: %s' % (text, d) for d in diffs]
        setup(h)
        res = h.call(SCAN_NUMBER)
        if res['fault']:
            return ['%r: replacement faulted: %s' % (text, res['fault'])]
        got = _f32(h, TOKEN_NUMBER)
        if got != want:
            return ['%r: value %r, want %r' % (text, got, want)]
    return None


def test_switch_buffer(h):
    target_data = h.alloc(8, b'abcdef\0\0')
    target = h.alloc(0x28)

    def setup(h):
        _buffer(h, target, target_data, b'abcdef', buf_pos=1, n_chars=5, input_file=0x1234)
        _w32(h, CURRENT, 0)
        _globals(h)

    diffs = h.compare(SWITCH_BUFFER, args=[target], setup=setup, ret=None)
    if diffs:
        return ['no current buffer: %s' % d for d in diffs]
    setup(h)
    res = h.call(SWITCH_BUFFER, args=[target])
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if _u32(h, CURRENT) != target or _u32(h, CHARS_READ) != 5:
        return ['current %08X chars %d' % (_u32(h, CURRENT), _u32(h, CHARS_READ))]
    if _u32(h, TEXT_START) != target_data + 1 or _u32(h, POSITION) != target_data + 1:
        return ['text %08X position %08X' % (_u32(h, TEXT_START), _u32(h, POSITION))]
    if _u32(h, INPUT_FILE) != 0x1234 or _u32(h, SWITCHED) != 1:
        return ['input %08X switched %d' % (_u32(h, INPUT_FILE), _u32(h, SWITCHED))]
    if h.uc.mem_read(HOLD_CHAR, 1)[0] != ord('b'):
        return ['hold character %02X' % h.uc.mem_read(HOLD_CHAR, 1)[0]]

    old_data = h.alloc(8, b'xyz\0\0\0\0')
    old = h.alloc(0x28)
    new_data = h.alloc(8, b'QR\0\0\0\0')
    new = h.alloc(0x28)

    def setup_old(h):
        _buffer(h, old, old_data, b'xyz', n_chars=3)
        _buffer(h, new, new_data, b'QR', n_chars=2, input_file=0x55)
        _w32(h, CURRENT, old)
        _globals(h)
        _w32(h, CHARS_READ, 3)
        _w32(h, TEXT_START, old_data)
        _w32(h, POSITION, old_data + 1)
        _w8(h, HOLD_CHAR, 0x59)

    diffs = h.compare(SWITCH_BUFFER, args=[new], setup=setup_old, ret=None)
    if diffs:
        return ['with a current buffer: %s' % d for d in diffs]
    setup_old(h)
    res = h.call(SWITCH_BUFFER, args=[new])
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if h.uc.mem_read(old_data + 1, 1)[0] != 0x59:
        return ['the hold character was not written back at the old position']
    if _u32(h, old + 0x08) != old_data + 1 or _u32(h, old + 0x10) != 3:
        return ['the old buffer kept position %08X chars %d' % (_u32(h, old + 0x08), _u32(h, old + 0x10))]
    if _u32(h, CURRENT) != new or _u32(h, CHARS_READ) != 2:
        return ['current %08X chars %d' % (_u32(h, CURRENT), _u32(h, CHARS_READ))]
    if _u32(h, TEXT_START) != new_data or _u32(h, INPUT_FILE) != 0x55:
        return ['text %08X input %08X' % (_u32(h, TEXT_START), _u32(h, INPUT_FILE))]
    if h.uc.mem_read(HOLD_CHAR, 1)[0] != ord('Q') or _u32(h, SWITCHED) != 1:
        return ['hold %02X switched %d' % (h.uc.mem_read(HOLD_CHAR, 1)[0], _u32(h, SWITCHED))]

    same = h.alloc(0x28)

    def setup_same(h):
        _buffer(h, same, new_data, b'QR', n_chars=2)
        _w32(h, CURRENT, same)
        _globals(h)

    diffs = h.compare(SWITCH_BUFFER, args=[same], setup=setup_same, ret=None)
    if diffs:
        return ['the same buffer: %s' % d for d in diffs]
    setup_same(h)
    h.call(SWITCH_BUFFER, args=[same])
    if _u32(h, CHARS_READ) != 0x77 or _u32(h, SWITCHED) != 0:
        return ['the same buffer was reloaded']
    return None


def test_delete_buffer(h):
    res = h.call(CREATE_BUFFER, args=[0, 0x20])
    if res['fault'] or not res['eax']:
        return ['could not create a buffer']
    buf = res['eax']
    _w32(h, CURRENT, buf)
    diffs = h.compare(DELETE_BUFFER, args=[buf], ret=None)
    if diffs:
        return ['owning buffer: %s' % d for d in diffs]
    res = h.call(DELETE_BUFFER, args=[buf])
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if _u32(h, CURRENT) != 0:
        return ['the deleted buffer is still current (%08X)' % _u32(h, CURRENT)]

    base = h.alloc(8, b'ab\0\0\0\0')
    res = h.call(SCAN_BUFFER, args=[base, 4])
    if res['fault'] or not res['eax']:
        return ['could not scan a caller buffer']
    buf = res['eax']
    _w32(h, CURRENT, buf)
    diffs = h.compare(DELETE_BUFFER, args=[buf], ret=None)
    if diffs:
        return ['caller buffer: %s' % d for d in diffs]
    res = h.call(DELETE_BUFFER, args=[buf])
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if _u32(h, CURRENT) != 0:
        return ['the deleted buffer is still current (%08X)' % _u32(h, CURRENT)]
    if bytes(h.uc.mem_read(base, 2)) != b'ab':
        return ['the caller memory was touched']

    _w32(h, CURRENT, 0)
    diffs = h.compare(DELETE_BUFFER, args=[0], ret=None)
    if diffs:
        return ['a null buffer: %s' % d for d in diffs]
    return None


def test_scan_buffer(h):
    text = b'hello'
    base = h.alloc(len(text) + 8, text + b'\0\0')

    def setup(h):
        h.uc.mem_write(base, text + b'\0\0')
        _w32(h, CURRENT, 0)
        _globals(h)

    diffs = h.compare(SCAN_BUFFER, args=[base, len(text) + 2], setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(SCAN_BUFFER, args=[base, len(text) + 2])
    if res['fault'] or not res['eax']:
        return ['replacement faulted or returned null: %s' % (res['fault'],)]
    buf = res['eax']
    if _u32(h, buf + 0x04) != base or _u32(h, buf + 0x08) != base:
        return ['ch_buf %08X buf_pos %08X' % (_u32(h, buf + 0x04), _u32(h, buf + 0x08))]
    if _u32(h, buf + 0x0C) != len(text) or _u32(h, buf + 0x10) != len(text):
        return ['buf_size %d n_chars %d' % (_u32(h, buf + 0x0C), _u32(h, buf + 0x10))]
    if _u32(h, buf + 0x14) != 0 or _u32(h, buf + 0x00) != 0:
        return ['own %d input %08X' % (_u32(h, buf + 0x14), _u32(h, buf + 0x00))]
    if _u32(h, buf + 0x18) != 0 or _u32(h, buf + 0x1C) != 1:
        return ['interactive %d at_bol %d' % (_u32(h, buf + 0x18), _u32(h, buf + 0x1C))]
    if _u32(h, buf + 0x20) != 0 or _u32(h, buf + 0x24) != 0:
        return ['fill %d status %d' % (_u32(h, buf + 0x20), _u32(h, buf + 0x24))]
    if _u32(h, CURRENT) != buf or _u32(h, CHARS_READ) != len(text) or _u32(h, SWITCHED) != 1:
        return ['current %08X chars %d switched %d' % (_u32(h, CURRENT), _u32(h, CHARS_READ), _u32(h, SWITCHED))]
    if _u32(h, TEXT_START) != base or _u32(h, POSITION) != base:
        return ['text %08X position %08X' % (_u32(h, TEXT_START), _u32(h, POSITION))]

    no_nul = h.alloc(4, b'abcd')

    def setup_bad(h):
        _w32(h, CURRENT, 0)
        _globals(h)

    diffs = h.compare(SCAN_BUFFER, args=[no_nul, 4], setup=setup_bad)
    if diffs:
        return ['without the two NULs: %s' % d for d in diffs]
    setup_bad(h)
    res = h.call(SCAN_BUFFER, args=[no_nul, 4])
    if res['eax'] != 0:
        return ['a buffer without the two NULs was accepted']

    diffs = h.compare(SCAN_BUFFER, args=[no_nul, 1], setup=setup_bad)
    if diffs:
        return ['size 1: %s' % d for d in diffs]
    setup_bad(h)
    if h.call(SCAN_BUFFER, args=[no_nul, 1])['eax'] != 0:
        return ['size 1 was accepted']
    return None


def test_scan_bytes(h):
    text = b'world'
    source = h.alloc(8, text)

    def setup(h):
        _w32(h, CURRENT, 0)
        _globals(h)

    diffs = h.compare(SCAN_BYTES, args=[source, len(text)], setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(SCAN_BYTES, args=[source, len(text)])
    if res['fault'] or not res['eax']:
        return ['replacement faulted or returned null: %s' % (res['fault'],)]
    buf = res['eax']
    memory = _u32(h, buf + 0x04)
    if memory == source:
        return ['the characters were not copied']
    if bytes(h.uc.mem_read(memory, len(text) + 2)) != text + b'\0\0':
        return ['copied %r' % bytes(h.uc.mem_read(memory, len(text) + 2))]
    if _u32(h, buf + 0x0C) != len(text) or _u32(h, buf + 0x10) != len(text):
        return ['buf_size %d n_chars %d' % (_u32(h, buf + 0x0C), _u32(h, buf + 0x10))]
    if _u32(h, buf + 0x14) != 1 or _u32(h, buf + 0x20) != 0:
        return ['own %d fill %d' % (_u32(h, buf + 0x14), _u32(h, buf + 0x20))]
    if _u32(h, CURRENT) != buf or _u32(h, TEXT_START) != memory or _u32(h, CHARS_READ) != len(text):
        return ['the globals did not follow the new buffer']

    empty = h.alloc(4, b'\0\0\0\0')

    def setup_empty(h):
        _w32(h, CURRENT, 0)
        _globals(h)

    diffs = h.compare(SCAN_BYTES, args=[empty, 0], setup=setup_empty)
    if diffs:
        return ['empty: %s' % d for d in diffs]
    setup_empty(h)
    res = h.call(SCAN_BYTES, args=[empty, 0])
    if res['fault'] or not res['eax']:
        return ['empty: replacement faulted or returned null']
    if _u32(h, res['eax'] + 0x0C) != 0 or _u32(h, res['eax'] + 0x10) != 0:
        return ['empty: buf_size %d n_chars %d' % (_u32(h, res['eax'] + 0x0C), _u32(h, res['eax'] + 0x10))]
    return None


def test_scan_string(h):
    text = b'hello'
    source = h.alloc(8, text + b'\0')

    def setup(h):
        _w32(h, CURRENT, 0)
        _globals(h)

    diffs = h.compare(SCAN_STRING, args=[source], setup=setup)
    if diffs:
        return diffs
    setup(h)
    res = h.call(SCAN_STRING, args=[source])
    if res['fault'] or not res['eax']:
        return ['replacement faulted or returned null: %s' % (res['fault'],)]
    buf = res['eax']
    memory = _u32(h, buf + 0x04)
    if bytes(h.uc.mem_read(memory, len(text) + 2)) != text + b'\0\0':
        return ['copied %r' % bytes(h.uc.mem_read(memory, len(text) + 2))]
    if _u32(h, buf + 0x0C) != len(text) or _u32(h, buf + 0x10) != len(text) or _u32(h, buf + 0x14) != 1:
        return ['buf_size %d n_chars %d own %d' % (_u32(h, buf + 0x0C), _u32(h, buf + 0x10),
                                                   _u32(h, buf + 0x14))]
    if _u32(h, CURRENT) != buf or _u32(h, CHARS_READ) != len(text):
        return ['the globals did not follow the new buffer']
    return None
