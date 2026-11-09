"""CDatFile::ReadChar (0x00445240): takes sources[currentSource].text[sourcePos] into token, then advances sourcePos
without running past the last character."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

OBJ_SIZE = 0xBFC
SOURCE_TEXT = 0x24 + 0x1C   # sources[0].text
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


def _case(h, text, pos):
    obj = h.alloc(OBJ_SIZE, bytes(OBJ_SIZE))
    _set_string(h, obj + SOURCE_TEXT, text)
    h.uc.mem_write(obj + CURRENT_SOURCE, struct.pack('<I', 0))
    h.uc.mem_write(obj + SOURCE_POS, struct.pack('<I', pos))
    diffs = h.compare(0x00445240, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(0x00445240, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    token = h.uc.mem_read(obj + 4, 1)[0]
    got_pos = struct.unpack('<I', h.uc.mem_read(obj + SOURCE_POS, 4))[0]
    if text:
        want_token = text[pos] if pos < len(text) else 0
        want_pos = pos + 1 if pos + 1 < len(text) else pos
    else:
        want_token, want_pos = 0, 0
    if token != want_token:
        return ['text %r pos %d: token %r, want %r' % (text, pos, token, want_token)]
    if got_pos != want_pos:
        return ['text %r pos %d: position %d, want %d' % (text, pos, got_pos, want_pos)]


def test_read_char(h):
    for text, pos in ((b'abc', 0), (b'abc', 1), (b'abc', 2), (b'abc', 3), (b'x', 0), (b'', 0), (b'a b\nc', 2)):
        diffs = _case(h, text, pos)
        if diffs:
            return diffs
