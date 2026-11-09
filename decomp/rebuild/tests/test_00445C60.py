"""CDatFile::ReadToken (0x00445C60): resets tokenText and spells the next token from the current source."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

OBJ_SIZE = 0xBFC
TOKEN_TEXT = 0x8
SOURCE_TEXT = 0x24 + 0x1C
SOURCE_POS = 0x294
CURRENT_SOURCE = 0x280


def _set_string(h, addr, data):
    if len(data) < 16:
        h.uc.mem_write(addr + 4, data + b'\0' * (16 - len(data)))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(data), 15))
    else:
        p = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', p))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(data), len(data)))


def _get_string(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    data = (addr + 4) if cap < 16 else struct.unpack('<I', h.uc.mem_read(addr + 4, 4))[0]
    return bytes(h.uc.mem_read(data, size))


def _case(h, text):
    obj = h.alloc(OBJ_SIZE, bytes(OBJ_SIZE))
    _set_string(h, obj + TOKEN_TEXT, b'stale')
    _set_string(h, obj + SOURCE_TEXT, text)
    h.uc.mem_write(obj + CURRENT_SOURCE, struct.pack('<I', 0))
    h.uc.mem_write(obj + SOURCE_POS, struct.pack('<I', 0))
    diffs = h.compare(0x00445C60, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(0x00445C60, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    return _get_string(h, obj + TOKEN_TEXT)


def test_read_token(h):
    # the text a keyword line can hold: single separators, a line break, and the end of the source
    for text, want in ((b'abc def', b'abc'),
                       (b'a b\nc', b'a'),
                       (b'abc\nxyz', b'abc'),
                       (b'#resolution 800\n', b'#resolution'),
                       (b'', b'')):
        got = _case(h, text)
        if isinstance(got, list):
            return got
        if got != want:
            return ['text %r: tokenText %r, want %r' % (text, got, want)]
    return None


def test_read_token_newline(h):
    # a line break ends the token: the next token is empty and the character is a line break
    obj = h.alloc(OBJ_SIZE, bytes(OBJ_SIZE))
    _set_string(h, obj + TOKEN_TEXT, b'stale')
    _set_string(h, obj + SOURCE_TEXT, b'\n abc')
    h.uc.mem_write(obj + CURRENT_SOURCE, struct.pack('<I', 0))
    h.uc.mem_write(obj + SOURCE_POS, struct.pack('<I', 0))
    diffs = h.compare(0x00445C60, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(0x00445C60, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    token = h.uc.mem_read(obj + 4, 1)[0]
    pos = struct.unpack('<I', h.uc.mem_read(obj + SOURCE_POS, 4))[0]
    if _get_string(h, obj + TOKEN_TEXT) != b'':
        return ['the line break produced a token']
    if token != 10 or pos != 1:
        return ['token %r position %d, want the line break at 1' % (token, pos)]
