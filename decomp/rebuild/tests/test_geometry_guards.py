"""Bounded collision/frustum fixtures, including stored-float overflow and NaNs."""
import struct


def _borders(h, address, helper, pop):
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_FPCW
    saved = bytes(h.uc.mem_read(helper, 8))
    cw = h.uc.reg_read(UC_X86_REG_FPCW)
    diffs = []
    try:
        for control in (0x27f, 0x7f):
            for x, radius, polygon, found in [(1.0, 1.0, False, False),
                                              (3.0, 1.0, False, False),
                                              (1e30, 1e29, False, False),
                                              (float('nan'), 1.0, False, False),
                                              (1.0, 1.0, True, False),
                                              (1.0, 1.0, True, True)]:
                code = b'\xb8' + struct.pack('<I', int(found)) + (bytes([0xc2, pop, 0]) if pop else b'\xc3')
                h.uc.mem_write(helper, code)
                h.uc.ctl_remove_cache(helper, helper + 8)
                obj = h.alloc(0x420, bytes(0x420))
                other = h.alloc(0x420, bytes(0x420))
                owner = h.alloc(8, bytes(8))
                head = h.alloc(12, bytes(12))
                node = h.alloc(12, struct.pack('<III', head, head, h.alloc(16, bytes(16))))
                h.uc.mem_write(head, struct.pack('<I', node))
                h.uc.mem_write(owner + 4, struct.pack('<I', head))
                h.uc.mem_write(obj + 8, struct.pack('<I', owner))
                h.uc.mem_write(obj + 0x20, bytes([int(polygon), 1]))
                h.uc.mem_write(obj + 0x410, struct.pack('<f', radius))
                h.uc.mem_write(other + 0x3fc, struct.pack('<f', x))
                h.uc.reg_write(UC_X86_REG_FPCW, control)
                regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x12345678}
                diffs += h.compare(address, args=[other], regs=regs, ret='al')
                result = h.call(address, args=[other], regs=regs)
                if result['fault']:
                    diffs.append('bounded border check faulted: %s' % result['fault'])
    finally:
        h.uc.mem_write(helper, saved)
        h.uc.ctl_remove_cache(helper, helper + len(saved))
        h.uc.reg_write(UC_X86_REG_FPCW, cw)
    return diffs


def test_border_circle(h):
    return _borders(h, 0x004402A0, 0x0047FEF0, 0)


def test_border_shape(h):
    return _borders(h, 0x00440390, 0x0043FB20, 16)


def test_frustum_unordered(h):
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX
    planes = [(1, 0, 0, 1), (-1, 0, 0, 1), (0, 1, 0, 1),
              (0, -1, 0, 1), (0, 0, 1, 1), (0, 0, -1, 1)]
    obj = h.alloc(4 + 6 * 16, bytes(4) + b''.join(struct.pack('<4f', *p) for p in planes))
    matrix = h.alloc(64, struct.pack('<16f', *[1.0 if i % 5 == 0 else 0.0 for i in range(16)]))
    diffs = []
    for values, expected in [([], False), ([(0, 0, 0)], True), ([(3, 3, 3)], False),
                              ([(-3, 0, 0), (3, 0, 0)], True), ([(float('nan'), 0, 0)], False)]:
        data = b''.join(struct.pack('<8f', *v, 0, 0, 0, 0, 0) for v in values)
        vertices = h.alloc(max(32, len(data)), data or bytes(32))
        args = [vertices, len(values), matrix]
        regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x12345678}
        diffs += h.compare(0x00458380, args=args, regs=regs, ret='al')
        result = h.call(0x00458380, args=args, regs=regs)
        if result['fault'] or (result['eax'] & 0xff) != int(expected):
            diffs.append('frustum result for %r: %r' % (values, result))
    return diffs
