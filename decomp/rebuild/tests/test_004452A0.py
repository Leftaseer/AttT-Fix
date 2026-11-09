"""ParseTokenNumber (0x004452A0): a whole token as a decimal number.  The token arrives as a copy of a
std::string in the argument area (seven dwords), which the callee pads with a NUL and destroys; the result goes
through the float pointer and the return byte says whether the token was a number."""
import struct

SENTINEL = b'\xcd\xcd\xcd\xcd'


def _set_string(h, addr, data):
    if len(data) < 16:
        h.uc.mem_write(addr + 4, data + b'\0' * (16 - len(data)))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(data), 15))
    else:
        p = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', p))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(data), len(data)))


def _args(h, token, out):
    arg = h.alloc(28, bytes(28))
    _set_string(h, arg, token)
    return list(struct.unpack('<7I', bytes(h.uc.mem_read(arg, 28)))) + [out]


def _case(h, token, valid):
    out = h.alloc(4, SENTINEL)
    args = _args(h, token, out)
    diffs = h.compare(0x004452A0, args=args, ret='al')
    if diffs:
        return diffs
    res = h.call(0x004452A0, args=args)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    got = res['eax'] & 0xFF
    if got != int(valid):
        return ['%r: returned %d, want %d' % (token, got, valid)]
    data = bytes(h.uc.mem_read(out, 4))
    if valid and data == SENTINEL:
        return ['%r: the number was not stored' % token]
    if not valid and data != SENTINEL:
        return ['%r: failed but stored %s' % (token, data.hex())]
    if valid and token == b'42' and data != struct.pack('<f', 42.0):
        return ['42 parsed as %s' % data.hex()]
    if valid and token == b'-7' and data != struct.pack('<f', -7.0):
        return ['-7 parsed as %s' % data.hex()]
    if valid and token == b'0.125' and data != struct.pack('<f', 0.125):
        return ['0.125 parsed as %s' % data.hex()]
    return None


def test_parse_token_number(h):
    cases = (
        # integers, with and without a sign
        (b'0', True), (b'5', True), (b'42', True), (b'123456789', True),
        (b'-7', True), (b'+7', True), (b'-0', True), (b'+0', True),
        # fractions, including a leading or a trailing point
        (b'.5', True), (b'-.5', True), (b'+.5', True), (b'3.25', True), (b'0.125', True),
        (b'12.', True), (b'-12.', True),
        # the divisor wraps as a 32-bit unsigned, as the original's does
        (b'1.2345678901234', True),
        # a very long integer saturates to infinity in a float, and the parse still succeeds
        (b'999999999999999999999999999999999999999999', True),
        # anything else is not a number
        (b'', False), (b'abc', False), (b'1a', False), (b'1.2.3', False), (b'1-2', False),
        (b'-', False), (b'+', False), (b'.', False), (b'-a', False), (b'--1', False),
        (b'++1', False), (b'-+.5', False), (b' 1', False), (b'1 ', False),
    )
    for token, valid in cases:
        diffs = _case(h, token, valid)
        if diffs:
            return ['%r: %s' % (token, d) for d in diffs]
    return None
