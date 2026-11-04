"""Exercise the rebuilt string ordering helpers with valid VC8 string arrays."""

import itertools
import struct


STRING_SIZE = 28


def _string_array(h, values):
    start = h.alloc(STRING_SIZE * len(values), bytes(STRING_SIZE * len(values)))
    for i, value in enumerate(values):
        h._str_set(start + STRING_SIZE * i, value)
    return start


def test_string_median(h):
    diffs = []
    values = (b'zebra', b'middle with a heap buffer', b'a\0suffix')
    for order in itertools.permutations(values):
        for address in (0x005A1D40, 0x005A2020):
            start = _string_array(h, order)
            args = [start + STRING_SIZE * i for i in range(3)]
            diffs.extend(h.compare(address, args=args, ret=None))
            result = h.call(h.to_rebuilt(address), args=args)
            if result['fault']:
                diffs.append('%08X fault: %s' % (address, result['fault']))
            elif [h._str_get(ptr) for ptr in args] != sorted(order):
                diffs.append('%08X left the three keys out of order' % address)
    return diffs


def test_string_partition(h):
    address = 0x005A2780
    long_key = b'middle with a heap buffer'
    inputs = [
        [b'z', b'', b'aa'],
        [b'z', long_key, b'', long_key, b'a', b'z', b''],
        [b'same'] * 7,
        [b'z', long_key, b'a', b'a\0suffix', b''] * 10,
    ]
    diffs = []
    for values in inputs:
        start = _string_array(h, values)
        end = start + STRING_SIZE * len(values)
        out = h.alloc(8, bytes(8))
        args = [out, start, end]
        diffs.extend(h.compare(address, args=args, ret=None))
        result = h.call(h.to_rebuilt(address), args=args)
        if result['fault']:
            diffs.append('n=%d partition fault: %s' % (len(values), result['fault']))
            continue
        lo, hi = struct.unpack('<II', h.uc.mem_read(out, 8))
        if not start <= lo < hi <= end or (lo - start) % STRING_SIZE or (hi - start) % STRING_SIZE:
            diffs.append('n=%d invalid partition bounds' % len(values))
            continue
        keys = [h._str_get(ptr) for ptr in range(start, end, STRING_SIZE)]
        left, right = (lo - start) // STRING_SIZE, (hi - start) // STRING_SIZE
        pivot = keys[left]
        if (sorted(keys) != sorted(values) or any(key >= pivot for key in keys[:left])
                or any(key != pivot for key in keys[left:right]) or any(key <= pivot for key in keys[right:])):
            diffs.append('n=%d invalid partition ordering or contents' % len(values))
    return diffs
