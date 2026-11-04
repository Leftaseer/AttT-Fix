"""Check the native three-coordinate bounds and signed conversion."""
import struct


def test_integer_coordinate_bounds(h):
    from unicorn.x86_const import UC_X86_REG_FPCW

    nan = float('nan')
    indefinite = -0x80000000
    cases = [
        ((1.75, -2.75, 0.0), (-2, 1)),
        ((-2.75, 0.0, 1.75), (-2, 1)),
        ((0.0, 1.75, -2.75), (-2, 1)),
        ((-0.0, 0.0, -0.0), (0, 0)),
        ((1.0, 0.0, nan), (indefinite, 1)),
        ((1.0, 2.0, nan), (indefinite, 2)),
        ((nan, 2.0, 3.0), (2, 3)),
        ((2.0, nan, 3.0), (3, indefinite)),
        ((float('inf'), 1.0, 0.0), (0, indefinite)),
        ((2.0 ** 31, -2147483520.0, 0.0), (-2147483520, indefinite)),
        ((-2147483904.0, -4.75, -2.25), (indefinite, -2)),
    ]
    address = 0x00473280
    outputs = h.alloc(8, bytes(8))
    saved_control = h.uc.reg_read(UC_X86_REG_FPCW)
    diffs = []
    try:
        for control in (0x27f, 0x7f):
            for coords, expected in cases:
                args = (*struct.unpack('<III', struct.pack('<fff', *coords)), outputs, outputs + 4)
                label = f'cw={control:x} coordinates={coords}'
                h.uc.reg_write(UC_X86_REG_FPCW, control)
                h.uc.mem_write(outputs, b'\xa5' * 8)
                diffs.extend(f'{label}: {diff}' for diff in h.compare(address, args=args, ret=None))
                result = h.call(h.to_rebuilt(address), args=args)
                observed = struct.unpack('<ii', h.uc.mem_read(outputs, 8))
                if result['fault'] or result['esp'] != 24 or observed != expected:
                    diffs.append(f'{label}: expected {expected}, got {observed} ({result})')
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, saved_control)
    return diffs
