"""Valid movement-direction contracts for the stored-float angular-difference helper."""
import math
import struct


def test_direction_delta_contract(h):
    from unicorn.x86_const import UC_X86_REG_FPCW
    cases = [
        ((1, 0, 1, 0), 0), ((1, 0, 0, 1), math.pi / 2),
        ((0, 1, 1, 0), -math.pi / 2), ((0, 1, -1, 0), math.pi / 2),
        ((-1, 0.0001, -1, -0.0001), None), ((-1, -0.0001, -1, 0.0001), None),
        ((1e30, 0, 0, 1e30), math.pi / 2), ((1, 2, -3, 4), None),
        ((-1, 0.0, -1, -0.0), 0), ((1, 0, -1, 0), None),
        ((0, 0, 0, 0), 0),
    ]
    diffs = []
    saved = h.uc.reg_read(UC_X86_REG_FPCW)
    try:
        for cw in (0x27F, 0x7F):
            h.uc.reg_write(UC_X86_REG_FPCW, cw)
            for values, expected in cases:
                args = list(struct.unpack('<4I', struct.pack('<4f', *values)))
                diffs += ['cw=%x %r: %s' % (cw, values, d)
                          for d in h.compare(0x0043F260, args=args, ret='st0')]
                result = h.call(0x0043F260, args=args)
                value = result['st0']
                if result['fault'] or value is None or not math.isfinite(value):
                    diffs.append('finite directions did not return normally: %r' % result)
                elif abs(value) > math.pi + 1e-6:
                    diffs.append('angular delta is outside [-pi, pi]: %r' % value)
                elif expected is not None and abs(value - expected) > 1e-6:
                    diffs.append('direction delta %r: expected approximately %r, got %r' % (values, expected, value))
                elif values[0] == -1 and abs(values[1]) == 0.0001 and abs(value) > 0.001:
                    diffs.append('crossing the -pi/pi boundary took the long turn: %r' % value)
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, saved)
    return diffs
