"""Triangular-grid lookup with bounded cells and signed conversion overflow cases."""
import struct


def float_bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def test_grid_lookup(h):
    from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_FPCW
    obj = h.alloc(0x90, bytes(0x90))
    cells = h.alloc(17 * 17 * 16, bytes(17 * 17 * 16))
    for offset, data in [(0x60, struct.pack('<ffI', 1.0, 1.0, cells)),
                         (0x6c, struct.pack('<II', 8, 8)), (0x80, struct.pack('<I', 17))]:
        h.uc.mem_write(obj + offset, data)
    out = h.alloc(4, bytes(4))
    diffs = []
    cw = h.uc.reg_read(UC_X86_REG_FPCW)
    try:
        for control in (0x27f, 0x7f):
            for x, z in [(-2.0, -1.0), (-0.01, 0), (0, 0), (0.5, 0.25), (2, 1),
                         (2.0 ** 96, 0), (float('inf'), 0), (float('nan'), 0)]:
                h.uc.reg_write(UC_X86_REG_FPCW, control)
                args = [out, float_bits(x), float_bits(z)]
                diffs += ['cw=%x x=%r z=%r: %s' % (control, x, z, d)
                          for d in h.compare(0x004FCCB0, args=args, regs={UC_X86_REG_ECX: obj})]
                result = h.call(0x004FCCB0, args=args, regs={UC_X86_REG_ECX: obj})
                if result['fault']:
                    diffs.append('grid fixture faulted: %s' % result['fault'])
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, cw)
    return diffs


def test_grid_cells_and_pointer_callers(h):
    from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_FPCW

    # Recreate the cell records built by 004FD520 for unit scales and a translated origin.
    # Columns alternate their Z offset and rows run in descending Z order.
    half = 16
    stride = 2 * half + 1
    origin_x, origin_z = -16.0, 20.0
    cell_data = b''.join(
        struct.pack('<ffBBHI', origin_x + 1.5 * column, origin_z + 2 * row + (column % 2),
                    column % 2 == 0, 1, 0, 0)
        for row in range(half, -half - 1, -1)
        for column in range(-half, half + 1)
    )
    cells = h.alloc(len(cell_data), cell_data)
    obj = h.alloc(0x90, bytes(0x90))
    h.uc.mem_write(obj + 0x60, struct.pack('<ff7I3f', 1.0, 1.0, cells, half, half,
                                          half, half, stride * stride, stride, origin_x, 0, origin_z))
    out = h.alloc(4)
    vector = h.alloc(8)
    regs = {UC_X86_REG_ECX: obj}
    # The first four points reach the four native return paths. The remaining points straddle an edge.
    cases = [(float_bits(x), float_bits(z), index)
             for x, z, index in [(-19, 16, 608), (-16, 16, 610), (-18.75, 20, 542), (-18.5, 17, 609)]]
    cases.extend((float_bits(-15.5), float_bits(21.0) + delta, index)
                 for delta, index in [(-1, 544), (0, 545), (1, 511)])
    diffs = []
    original_control = h.uc.reg_read(UC_X86_REG_FPCW)
    try:
        for control in (0x7f, 0x27f):
            for x, z, index in cases:
                h.uc.mem_write(vector, struct.pack('<II', x, z))
                h.uc.mem_write(out, b'\xff' * 4)
                for address, args, expected_eax in (
                    (0x004FCCB0, (out, x, z), out),
                    (0x00523440, (x, z), cells + index * 16),
                    (0x00523470, (vector,), cells + index * 16),
                ):
                    label = f'{address:08x} cw={control:x} x={x:08x} z={z:08x}'
                    h.uc.reg_write(UC_X86_REG_FPCW, control)
                    diffs.extend(f'{label}: {diff}' for diff in h.compare(address, args=args, regs=regs))
                    result = h.call(h.to_rebuilt(address), args=args, regs=regs)
                    if result['fault'] or result['eax'] != expected_eax or result['esp'] != 4 * (1 + len(args)):
                        diffs.append(f'{label}: expected eax={expected_eax:08x}, got {result}')
                    if address == 0x004FCCB0 and bytes(h.uc.mem_read(out, 4)) != struct.pack('<I', index):
                        diffs.append(f'{label}: expected cell {index}')
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, original_control)
    return diffs
