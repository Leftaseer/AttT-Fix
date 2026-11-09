"""The case-insensitive string map's hash (0x579BB0) and ordering (0x579C00).

The hash samples every (size/16+1)-st byte, folds it through the game's cp1251 lowercasing table at 0x6C7C90
and adds it to 0xDEADBEEF.  The ordering compares the folded bytes of the common prefix and falls back to the
lengths; it is the bool std::map's "less" uses."""
import struct

HASH_CASE = 0x00579BB0
LESS_CASE = 0x00579C00


def _lower_table():
    table = bytearray(range(256))
    for c in range(0x41, 0x5B):
        table[c] += 0x20
    for c in range(0xC0, 0xE0):
        table[c] += 0x20
    table[0xA8] = 0xB8
    return bytes(table)


TABLE = _lower_table()


def _put_string(h, addr, text):
    """a VC8 string: allocator, inline buffer or heap block, size, capacity"""
    if len(text) < 16:
        h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
        cap = 15
    else:
        block = h.alloc(len(text) + 1, text + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', block))
        cap = len(text)
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), cap))


def _string(h, text):
    obj = h.alloc(28, bytes(28))
    _put_string(h, obj, text)
    return obj


def _expected_hash(key):
    value = 0xDEADBEEF
    size = len(key)
    if size:
        step = (size >> 4) + 1
        i = 0
        while i <= size - step:
            value = (value + TABLE[key[i]]) & 0xFFFFFFFF
            i += step
    return value


def _expected_less(a, b):
    for x, y in zip(a, b):
        if TABLE[x] != TABLE[y]:
            return TABLE[x] < TABLE[y]
    return len(a) < len(b)


def test_hash_case_string(h):
    keys = [b'', b'a', b'ab', b'Alpha', b'Texture.tex', b'\xff\x80z', b'\xC0\xC1\xA8',
            b'abcdefghijklmnopqrstuvwxyz0123456789ABCD', b'\xA8\xB8']
    for key in keys:
        obj = _string(h, key)
        diffs = h.compare(HASH_CASE, args=[obj], ret='eax')
        if diffs:
            return ['key %r: %s' % (key, d) for d in diffs]
        res = h.call(HASH_CASE, args=[obj])
        if res['fault']:
            return ['key %r: replacement faulted: %s' % (key, res['fault'])]
        want = _expected_hash(key)
        if res['eax'] != want:
            return ['key %r: hash %08X, want %08X' % (key, res['eax'], want)]
    return None


def test_less_case_string(h):
    pairs = [(b'', b''), (b'a', b'a'), (b'A', b'a'), (b'a', b'A'), (b'A', b'B'), (b'B', b'A'),
             (b'alpha', b'ALPHA'), (b'ALPHA', b'alpha'), (b'a', b'ab'), (b'ab', b'a'),
             (b'Beta', b'betaA'), (b'\xC0\xC1', b'\xE0\xE1'), (b'\xE0', b'\xC0'),
             (b'\xA8', b'\xB8'), (b'\xB8', b'\xA8'), (b'\xff', b'\x80'), (b'\x80', b'\xff')]
    for a, b in pairs:
        aobj, bobj = _string(h, a), _string(h, b)
        diffs = h.compare(LESS_CASE, args=[aobj, bobj], ret='al')
        if diffs:
            return ['%r < %r: %s' % (a, b, d) for d in diffs]
        res = h.call(LESS_CASE, args=[aobj, bobj])
        if res['fault']:
            return ['%r < %r: replacement faulted: %s' % (a, b, res['fault'])]
        want = int(_expected_less(a, b))
        if (res['eax'] & 0xFF) != want:
            return ['%r < %r: %d, want %d' % (a, b, res['eax'] & 0xFF, want)]
    return None
