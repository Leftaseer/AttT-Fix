"""Triangular-grid lookup with bounded cells and signed conversion overflow cases."""
import struct


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
                bits = lambda v: struct.unpack('<I', struct.pack('<f', v))[0]
                h.uc.reg_write(UC_X86_REG_FPCW, control)
                args = [out, bits(x), bits(z)]
                diffs += ['cw=%x x=%r z=%r: %s' % (control, x, z, d)
                          for d in h.compare(0x004FCCB0, args=args, regs={UC_X86_REG_ECX: obj})]
                result = h.call(0x004FCCB0, args=args, regs={UC_X86_REG_ECX: obj})
                if result['fault']:
                    diffs.append('grid fixture faulted: %s' % result['fault'])
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, cw)
    return diffs
