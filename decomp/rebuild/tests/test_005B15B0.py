"""Partition float keys with unique payloads, tied keys and unordered comparisons."""
import struct


def test_float_partition(h):
    diffs = []
    cases = [[3, 1, 4, 2], [1, 1, 1, 1], [4, 3, 2, 1],
             [float('nan'), 2, 0, 1, float('nan'), -1],
             [1, float('nan'), 1, 0, 3, 2, 1, -1]]
    for values in cases:
        data = b''.join(struct.pack('<fI', key, i + 100) for i, key in enumerate(values))
        array = h.alloc(len(data), data)
        result = h.alloc(8, bytes(8))
        args = [result, array, array + len(data), 0]
        diffs += h.compare(0x005B15B0, args=args, ret=None)
        state = h.call(0x005B15B0, args=args)
        if state['fault']:
            diffs.append('bounded float partition faulted: %s' % state['fault'])
    return diffs
