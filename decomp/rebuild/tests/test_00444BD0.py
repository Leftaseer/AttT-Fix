"""CDelCom::PutChar (0x00444BD0): runs of spaces collapse, a newline after a space replaces it, and a second
newline in a row is dropped.  The text is the string at +0x94 and the two pending flags are globals."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

TEXT = 0x94
AFTER_SPACE = 0x006C8974
AFTER_NEWLINE = 0x006C0036


def _set_string(h, addr, data):
    h.uc.mem_write(addr + 4, data + b'\0' * (16 - len(data)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(data), 15))


def _get_string(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    data = (addr + 4) if cap < 16 else struct.unpack('<I', h.uc.mem_read(addr + 4, 4))[0]
    return bytes(h.uc.mem_read(data, size))


def _case(h, text, c, after_space, after_newline, want, want_space, want_newline):
    obj = h.alloc(0xB0, bytes(0xB0))
    _set_string(h, obj + TEXT, text)

    def setup(h):
        h.uc.mem_write(AFTER_SPACE, bytes([after_space]))
        h.uc.mem_write(AFTER_NEWLINE, bytes([after_newline]))

    diffs = h.compare(0x00444BD0, args=(c,), regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(0x00444BD0, args=(c,), regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    got = _get_string(h, obj + TEXT)
    if got != want:
        return ['text %r + %r: got %r, want %r' % (text, bytes([c]), got, want)]
    if h.uc.mem_read(AFTER_SPACE, 1)[0] != want_space or \
            h.uc.mem_read(AFTER_NEWLINE, 1)[0] != want_newline:
        return ['text %r + %r: flags %d,%d, want %d,%d' % (
            text, bytes([c]), h.uc.mem_read(AFTER_SPACE, 1)[0],
            h.uc.mem_read(AFTER_NEWLINE, 1)[0], want_space, want_newline)]
    return []


def test_put_char(h):
    cases = (
        # a normal character clears both flags
        (b'', ord('a'), 0, 0, b'a', 0, 0),
        (b'ab', ord('c'), 1, 0, b'abc', 0, 0),
        (b'ab', ord('c'), 0, 1, b'abc', 0, 0),
        # one space, and no second one
        (b'', ord(' '), 0, 0, b' ', 1, 0),
        (b'a ', ord(' '), 1, 0, b'a ', 1, 0),
        (b'a', ord(' '), 1, 1, b'a', 1, 1),
        # a newline after a space replaces it
        (b'a ', ord('\n'), 1, 0, b'a\n', 0, 1),
        (b'ab ', ord('\n'), 0, 0, b'ab \n', 0, 1),
        # a second newline is dropped
        (b'a\n', ord('\n'), 0, 1, b'a\n', 0, 1),
        # a newline with no pending space appends
        (b'ab', ord('\n'), 0, 0, b'ab\n', 0, 1),
        (b'ab', ord('\n'), 0, 1, b'ab', 0, 1),
        # a space after a newline is dropped
        (b'a\n', ord(' '), 0, 1, b'a\n', 0, 1),
    )
    for text, c, after_space, after_newline, want, want_space, want_newline in cases:
        diffs = _case(h, text, c, after_space, after_newline, want, want_space, want_newline)
        if diffs:
            return diffs
    return None
