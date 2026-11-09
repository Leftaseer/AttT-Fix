"""CDatFile::SelectKeyword (0x00445CD0): finds the keyword in the current format set and then its "#keyword" token."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

OBJ_SIZE = 0xBFC
TOKEN_TEXT = 0x8
SOURCE_TEXT = 0x24 + 0x1C
FORMAT_SET = 0x284
KEYWORD_INDEX = 0x290
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


def _datfile(h):
    obj = h.alloc(OBJ_SIZE, bytes(OBJ_SIZE))
    h.call(0x00444D50, regs={UC_X86_REG_ECX: obj})
    return obj


def _case(h, fmt, keyword, text):
    obj = _datfile(h)
    h.uc.mem_write(obj + FORMAT_SET, struct.pack('<I', fmt))
    h.uc.mem_write(obj + CURRENT_SOURCE, struct.pack('<I', 0))
    h.uc.mem_write(obj + SOURCE_POS, struct.pack('<I', 0))
    _set_string(h, obj + SOURCE_TEXT, text)
    kw = h.alloc(28, bytes(28))
    _set_string(h, kw, keyword)
    diffs = h.compare(0x00445CD0, args=[kw], regs={UC_X86_REG_ECX: obj}, ret='al')
    if diffs:
        return diffs
    res = h.call(0x00445CD0, args=[kw], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    return (res['eax'] & 0xFF) != 0


def test_select_keyword(h):
    for fmt, keyword, text, found in (
            (0, b'resolution', b'#resolution 800 600\n', True),
            (0, b'fullscreen', b'fullscreen 1\n', False),
            (1, b'cameratoggle', b'#cameratoggle\n', True),
            (0, b'texturequality', b'#resolution\n', False),
            (0, b'resolution', b'#fullscreen #resolution\n', True),
            (1, b'cameraforward', b'#cameraup #cameraforward\n', True),
            (0, b'nonsense', b'#resolution\n', False)):
        got = _case(h, fmt, keyword, text)
        if isinstance(got, list):
            return got
        if got != found:
            return ['%r in %r (set %d): %r, want %r' % (keyword, text, fmt, got, found)]
    return None


def test_select_keyword_state(h):
    # a match records the table index and leaves the keyword text; a miss leaves the index untouched
    obj = _datfile(h)
    h.uc.mem_write(obj + FORMAT_SET, struct.pack('<I', 0))
    h.uc.mem_write(obj + CURRENT_SOURCE, struct.pack('<I', 0))
    h.uc.mem_write(obj + SOURCE_POS, struct.pack('<I', 0))
    _set_string(h, obj + SOURCE_TEXT, b'#resolution 800\n')
    kw = h.alloc(28, bytes(28))
    _set_string(h, kw, b'resolution')
    res = h.call(0x00445CD0, args=[kw], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    index = struct.unpack('<I', h.uc.mem_read(obj + KEYWORD_INDEX, 4))[0]
    if index != 1:
        return ['the matched keyword index is %d, want 1' % index]
    if _get_string(h, obj + TOKEN_TEXT) != b'resolution':
        return ['token text %r after the match' % _get_string(h, obj + TOKEN_TEXT)]

    obj = _datfile(h)
    h.uc.mem_write(obj + FORMAT_SET, struct.pack('<I', 1))
    h.uc.mem_write(obj + CURRENT_SOURCE, struct.pack('<I', 0))
    h.uc.mem_write(obj + SOURCE_POS, struct.pack('<I', 0))
    _set_string(h, obj + SOURCE_TEXT, b'#gamepause\n')
    diffs = h.compare(0x00445CD0, args=[kw], regs={UC_X86_REG_ECX: obj}, ret='al')
    if diffs:
        return diffs
