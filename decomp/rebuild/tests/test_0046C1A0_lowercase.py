"""The lowercased string copy in input.cpp: 0x46C1A0 copies the source into a 256-byte stack buffer, lowercases it
and assigns it to the output std::string (the keys of the input configuration's maps are lowercase).  A std::string
is 28 bytes: the allocator, the 16-byte inline buffer, the size and the capacity."""
import struct

LOWERCASE_COPY = 0x0046C1A0
STRING_SIZE = 28
SIZE = 0x14
CAPACITY = 0x18


def _make_string(h, text):
    raw = text.encode('latin1')
    assert len(raw) <= 15
    data = bytes(4) + raw + bytes(16 - len(raw)) + struct.pack('<II', len(raw), 15)
    return h.alloc(STRING_SIZE, data)


def _text(h, string):
    raw = h.uc.mem_read(string + 4, 16)
    size = struct.unpack('<I', h.uc.mem_read(string + SIZE, 4))[0]
    return bytes(raw[:size]).decode('latin1')


def test_0046C1A0_lowercase_copy(h):
    for text in ('HeLLo', '', 'MiXeD 123', 'ABCDEFGHIJKLMNO', 'already lower', 'c:\\Dir\\FILE', 'I'):
        source = _make_string(h, text)
        out = _make_string(h, '')

        diffs = h.compare(LOWERCASE_COPY, args=(source, out))
        if diffs:
            return ['%r: %s' % (text, d) for d in diffs]

        res = h.call(LOWERCASE_COPY, args=(source, out))
        if res['fault']:
            return ['%r: replacement faulted: %s' % (text, res['fault'])]
        if _text(h, source) != text:
            return ['%r: the source changed to %r' % (text, _text(h, source))]
        got = _text(h, out)
        want = text.lower()
        if got != want:
            return ['%r: the copy is %r, want %r' % (text, got, want)]
        size = struct.unpack('<I', h.uc.mem_read(out + SIZE, 4))[0]
        if size != len(want):
            return ['%r: size %d, want %d' % (text, size, len(want))]
        capacity = struct.unpack('<I', h.uc.mem_read(out + CAPACITY, 4))[0]
        if capacity != 15:
            return ['%r: capacity %d, want the inline 15' % (text, capacity)]
    return None
