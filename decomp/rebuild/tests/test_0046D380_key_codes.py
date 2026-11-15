"""The input configuration's key-name lookup in input.cpp: 0x46D380 maps a key name to its DirectInput scan code
(the name is lowercased first, so the lookup is case-insensitive; 0xFF when no key has the name).  The key comes in
as a by-value std::string (28 bytes: allocator, the 16-byte inline buffer, the size and the capacity), the way the
original's callers push it."""
import struct

KEY_CODE = 0x0046D380
UNKNOWN = 0xFF

KEYS = [
    ('esc', 1),
    ('1', 2),
    ('2', 3),
    ('3', 4),
    ('4', 5),
    ('5', 6),
    ('6', 7),
    ('7', 8),
    ('8', 9),
    ('9', 10),
    ('0', 11),
    ('-', 12),
    ('=', 13),
    ('backspace', 14),
    ('tab', 15),
    ('q', 16),
    ('w', 17),
    ('e', 18),
    ('r', 19),
    ('t', 20),
    ('y', 21),
    ('u', 22),
    ('i', 23),
    ('o', 24),
    ('p', 25),
    ('[', 26),
    (']', 27),
    ('enter', 28),
    ('leftctrl', 29),
    ('a', 30),
    ('s', 31),
    ('d', 32),
    ('f', 33),
    ('g', 34),
    ('h', 35),
    ('j', 36),
    ('k', 37),
    ('l', 38),
    (';', 39),
    ("'", 40),
    ('`', 41),
    ('leftshift', 42),
    ('\\', 43),
    ('z', 44),
    ('x', 45),
    ('c', 46),
    ('v', 47),
    ('b', 48),
    ('n', 49),
    ('m', 50),
    (',', 51),
    ('.', 52),
    ('/', 53),
    ('rightshift', 54),
    ('numpad*', 55),
    ('leftalt', 56),
    ('space', 57),
    ('capslock', 58),
    ('f1', 59),
    ('f2', 60),
    ('f3', 61),
    ('f4', 62),
    ('f5', 63),
    ('f6', 64),
    ('f7', 65),
    ('f8', 66),
    ('f9', 67),
    ('f10', 68),
    ('numlock', 69),
    ('scrolllock', 70),
    ('numpad7', 71),
    ('numpad8', 72),
    ('numpad9', 73),
    ('numpad-', 74),
    ('numpad4', 75),
    ('numpad5', 76),
    ('numpad6', 77),
    ('numpad+', 78),
    ('numpad1', 79),
    ('numpad2', 80),
    ('numpad3', 81),
    ('numpad0', 82),
    ('numpad.', 83),
    ('numpad/', 181),
    ('numpadenter', 156),
    ('f11', 87),
    ('f12', 88),
    ('rightctrl', 157),
    ('printscreen', 183),
    ('pause', 197),
    ('rightalt', 184),
    ('leftwin', 219),
    ('rightwin', 220),
    ('app', 221),
    ('up', 200),
    ('down', 208),
    ('left', 203),
    ('right', 205),
    ('insert', 210),
    ('delete', 211),
    ('home', 199),
    ('end', 207),
    ('pgup', 201),
    ('pgdown', 209),
    ('shift', 243),
    ('ctrl', 244),
    ('alt', 245),
]


def _string(name):
    """the seven argument dwords of a by-value std::string holding name in its inline buffer"""
    raw = name.encode('latin1')
    assert len(raw) <= 15
    buffer = raw + bytes(16 - len(raw))
    return [0] + list(struct.unpack('<4I', buffer)) + [len(raw), 15]


def _expected_code(h, name):
    dwords = _string(name)
    diffs = h.compare(KEY_CODE, args=dwords, ret='al')
    if diffs:
        return None, diffs
    res = h.call(KEY_CODE, args=_string(name))
    if res['fault']:
        return None, ['replacement faulted: %s' % (res['fault'],)]
    code = res['eax'] & 0xFF
    return code, None


def test_key_code_from_name(h):
    for name, code in KEYS:
        got, diffs = _expected_code(h, name)
        if diffs:
            return ['%r: %s' % (name, d) for d in diffs]
        if got != code:
            return ['%r: returned %d, want %d' % (name, got, code)]

    for name, code in (('ESC', 1), ('Enter', 28), ('PrintScreen', 183), ('NumpadEnter', 156), ('PgDown', 209),
                       ('LeftAlt', 56)):
        got, diffs = _expected_code(h, name)
        if diffs:
            return ['%r: %s' % (name, d) for d in diffs]
        if got != code:
            return ['%r (uppercase): returned %d, want %d' % (name, got, code)]

    for name in ('', 'xyz', 'numpad', 'escape', 'leftctrl ', '1 '):
        got, diffs = _expected_code(h, name)
        if diffs:
            return ['%r: %s' % (name, d) for d in diffs]
        if got != UNKNOWN:
            return ['%r: returned %d, want 0xFF' % (name, got)]
    return None
