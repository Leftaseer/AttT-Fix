"""Compare angular sorting on bounded arrays, including ties and unordered keys."""

import struct


def _arrays():
    axes = [(0.0, 1.0), (1.0, 0.0), (0.0, -1.0), (-1.0, 0.0)]
    return [axes, axes[::-1], axes * 2,
            [(1.0, 1.0)] * 4,
            [(float('nan'), 1.0), *axes, (1.0, float('nan'))]]


def _check(h, address, partition):
    from unicorn.x86_const import UC_X86_REG_FPCW
    diffs = []
    saved_cw = h.uc.reg_read(UC_X86_REG_FPCW)
    try:
        for cw in (0x27f, 0x7f):
            for values in _arrays():
                data = b''.join(struct.pack('<ff', *v) for v in values)
                array = h.alloc(len(data), data)
                end = array + len(data)
                args = [h.alloc(8, bytes(8)), array, end] if partition else [array, end, 0]
                h.uc.reg_write(UC_X86_REG_FPCW, cw)
                diffs += ['cw=%x n=%d: %s' % (cw, len(values), d)
                          for d in h.compare(address, args=args, ret=None)]
                result = h.call(address, args=args)
                if result['fault']:
                    diffs.append('bounded array faulted at %08X: %s' % (address, result['fault']))
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, saved_cw)
    return diffs


def test_angular_partition(h):
    return _check(h, 0x0048C980, True)


def test_angular_insertion(h):
    return _check(h, 0x0048CC40, False)
