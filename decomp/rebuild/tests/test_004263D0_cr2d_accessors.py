"""The CRenderObject2D position/size accessors:
0x004263D0 (ECX = object, ret 4): position +0/+4 += v; returns this.
0x004263F0 (ECX, ret 4): out = 0x00608088 - position; returns out.
0x00426450 (ECX, ret 4): +0x58/+0x5C = v[0]/v[1], +0x60 = 1; returns v[1].
0x00426470/90/B0 (ECX,EAX): +0x58/+0x5C set from floats, +0x60 = 1; returns EAX.
0x004264D0 (ECX, ret 4): +0x58/+0x5C += v, +0x60 = 1; returns v.
0x004264F0/510/530 (ECX,EAX): +0x58/+0x5C += floats, +0x60 = 1; returns EAX.
0x00426550 (ECX, ret 0): the address of +0x58.
0x00426560 (ECX, ret 0): the float at +0x58.
0x00426570 (ECX, ret 4): size +0x74/+0x78 += v, +0x7C = 1; returns v.
0x00426590/B0/D0 (ECX,EAX): size +0x74/+0x78 += floats, +0x7C = 1; returns EAX.
"""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

EDGE = 0x00608088


def _f(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


def _g(bits):
    return struct.unpack('<f', struct.pack('<I', bits))[0]


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def test_004263D0(h):
    obj = h.alloc(0x10, struct.pack('<ff', 1.5, -2.5) + bytes(8))
    v = h.alloc(8, struct.pack('<ff', 0.25, 4.0))
    diffs = h.compare(0x004263D0, args=[v], regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, struct.pack('<ff', 1.5, -2.5) + bytes(8))
    res = h.call(0x004263D0, args=[v], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    if res['eax'] != obj:
        return ['returned %08X' % res['eax']]
    got = struct.unpack('<ff', h.uc.mem_read(obj, 8))
    if got != (1.75, 1.5):
        return ['position %r' % (got,)]
    return None


def test_004263F0(h):
    # the edge constant is shared with the number parser's negative branch: restore it for later tests
    saved = bytes(h.uc.mem_read(EDGE, 4))
    try:
        obj = h.alloc(0x10, struct.pack('<ff', 1.5, -2.5) + bytes(8))
        out = h.alloc(8, b'\xEE' * 8)
        h.uc.mem_write(EDGE, struct.pack('<f', 100.0))
        diffs = h.compare(0x004263F0, args=[out], regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return [str(d) for d in diffs]
        h.uc.mem_write(out, b'\xEE' * 8)
        res = h.call(0x004263F0, args=[out], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['faulted: %s' % (res['fault'],)]
        if res['eax'] != out:
            return ['returned %08X' % res['eax']]
        got = struct.unpack('<ff', h.uc.mem_read(out, 8))
        if got != (98.5, 102.5):
            return ['mirror %r' % (got,)]
        return None
    finally:
        h.uc.mem_write(EDGE, saved)


def test_00426450(h):
    obj = h.alloc(0x70, b'\xEE' * 0x70)
    v = h.alloc(8, struct.pack('<II', 0x3F800000, 0x40000000))
    diffs = h.compare(0x00426450, args=[v], regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x70)
    res = h.call(0x00426450, args=[v], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    if res['eax'] != 0x40000000:
        return ['returned %08X' % res['eax']]
    if (_u32(h, obj + 0x58), _u32(h, obj + 0x5c), h.uc.mem_read(obj + 0x60, 1)) != \
            (0x3F800000, 0x40000000, b'\x01'):
        return ['+58/+5C/+60 are %08X/%08X/%02X' % (_u32(h, obj + 0x58), _u32(h, obj + 0x5c),
                                                    h.uc.mem_read(obj + 0x60, 1)[0])]
    return None


def _set_ecx_eax(h, addr, args, fields, ret='eax'):
    """run compare, then call; fields: (offset, expected dword)"""
    obj = h.alloc(0x80, b'\xEE' * 0x80)
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x11223344}
    diffs = h.compare(addr, args=args, regs=regs, ret=ret)
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x80)
    res = h.call(addr, args=args, regs=regs)
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    if ret == 'eax' and res['eax'] != 0x11223344:
        return ['EAX is %08X' % res['eax']]
    for field, value in fields:
        if _u32(h, obj + field) != value:
            return ['+%02X is %08X, expected %08X' % (field, _u32(h, obj + field), value)]
    return None


def test_00426470(h):
    return _set_ecx_eax(h, 0x00426470, [_f(1.5), _f(-2.5)],
                        [(0x58, _f(1.5)), (0x5c, _f(-2.5)), (0x60, 0xEEEEEE01)])


def test_00426490(h):
    return _set_ecx_eax(h, 0x00426490, [_f(1.5)], [(0x58, _f(1.5)), (0x60, 0xEEEEEE01)])


def test_004264B0(h):
    return _set_ecx_eax(h, 0x004264B0, [_f(-2.5)], [(0x5c, _f(-2.5)), (0x60, 0xEEEEEE01)])


def test_004264D0(h):
    obj = h.alloc(0x70, b'\xEE' * 0x70)
    h.uc.mem_write(obj + 0x58, struct.pack('<ff', 1.0, 2.0))
    v = h.alloc(8, struct.pack('<ff', 0.5, 0.25))
    diffs = h.compare(0x004264D0, args=[v], regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x70)
    h.uc.mem_write(obj + 0x58, struct.pack('<ff', 1.0, 2.0))
    res = h.call(0x004264D0, args=[v], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    if res['eax'] != v:
        return ['returned %08X' % res['eax']]
    got = struct.unpack('<ff', h.uc.mem_read(obj + 0x58, 8))
    if got != (1.5, 2.25) or h.uc.mem_read(obj + 0x60, 1) != b'\x01':
        return ['position %r, flag %02X' % (got, h.uc.mem_read(obj + 0x60, 1)[0])]
    return None


def test_004264F0(h):
    obj = h.alloc(0x70, b'\xEE' * 0x70)
    h.uc.mem_write(obj + 0x58, struct.pack('<ff', 1.0, 2.0))
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x11223344}
    diffs = h.compare(0x004264F0, args=[_f(0.5), _f(0.25)], regs=regs, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x70)
    h.uc.mem_write(obj + 0x58, struct.pack('<ff', 1.0, 2.0))
    res = h.call(0x004264F0, args=[_f(0.5), _f(0.25)], regs=regs)
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    if res['eax'] != 0x11223344:
        return ['EAX is %08X' % res['eax']]
    got = struct.unpack('<ff', h.uc.mem_read(obj + 0x58, 8))
    if got != (1.5, 2.25) or h.uc.mem_read(obj + 0x60, 1) != b'\x01':
        return ['position %r, flag %02X' % (got, h.uc.mem_read(obj + 0x60, 1)[0])]
    return None


def test_00426510(h):
    obj = h.alloc(0x70, b'\xEE' * 0x70)
    h.uc.mem_write(obj + 0x58, struct.pack('<ff', 1.0, 2.0))
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x11223344}
    diffs = h.compare(0x00426510, args=[_f(0.5)], regs=regs, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x70)
    h.uc.mem_write(obj + 0x58, struct.pack('<ff', 1.0, 2.0))
    res = h.call(0x00426510, args=[_f(0.5)], regs=regs)
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    got = struct.unpack('<ff', h.uc.mem_read(obj + 0x58, 8))
    if got != (1.5, 2.0) or h.uc.mem_read(obj + 0x60, 1) != b'\x01':
        return ['position %r' % (got,)]
    return None


def test_00426530(h):
    obj = h.alloc(0x70, b'\xEE' * 0x70)
    h.uc.mem_write(obj + 0x58, struct.pack('<ff', 1.0, 2.0))
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x11223344}
    diffs = h.compare(0x00426530, args=[_f(0.5)], regs=regs, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x70)
    h.uc.mem_write(obj + 0x58, struct.pack('<ff', 1.0, 2.0))
    res = h.call(0x00426530, args=[_f(0.5)], regs=regs)
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    got = struct.unpack('<ff', h.uc.mem_read(obj + 0x58, 8))
    if got != (1.0, 2.5) or h.uc.mem_read(obj + 0x60, 1) != b'\x01':
        return ['position %r' % (got,)]
    return None


def test_00426550(h):
    obj = h.alloc(0x70, b'\xEE' * 0x70)
    diffs = h.compare(0x00426550, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    res = h.call(0x00426550, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    if res['eax'] != obj + 0x58:
        return ['returned %08X' % res['eax']]
    return None


def test_00426560(h):
    obj = h.alloc(0x70, struct.pack('<f', 12.5) + bytes(0x6C))
    h.uc.mem_write(obj + 0x58, struct.pack('<f', -3.25))
    diffs = h.compare(0x00426560, regs={UC_X86_REG_ECX: obj}, ret='st0')
    if diffs:
        return [str(d) for d in diffs]
    res = h.call(0x00426560, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    if res['st0'] != -3.25:
        return ['returned %r' % (res['st0'],)]
    return None


def test_00426570(h):
    obj = h.alloc(0x80, b'\xEE' * 0x80)
    h.uc.mem_write(obj + 0x74, struct.pack('<ff', 1.0, 2.0))
    v = h.alloc(8, struct.pack('<ff', 0.5, 0.25))
    diffs = h.compare(0x00426570, args=[v], regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x80)
    h.uc.mem_write(obj + 0x74, struct.pack('<ff', 1.0, 2.0))
    res = h.call(0x00426570, args=[v], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    if res['eax'] != v:
        return ['returned %08X' % res['eax']]
    got = struct.unpack('<ff', h.uc.mem_read(obj + 0x74, 8))
    if got != (1.5, 2.25) or h.uc.mem_read(obj + 0x7c, 1) != b'\x01':
        return ['size %r, flag %02X' % (got, h.uc.mem_read(obj + 0x7c, 1)[0])]
    return None


def test_00426590(h):
    obj = h.alloc(0x80, b'\xEE' * 0x80)
    h.uc.mem_write(obj + 0x74, struct.pack('<ff', 1.0, 2.0))
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x11223344}
    diffs = h.compare(0x00426590, args=[_f(0.5), _f(0.25)], regs=regs, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x80)
    h.uc.mem_write(obj + 0x74, struct.pack('<ff', 1.0, 2.0))
    res = h.call(0x00426590, args=[_f(0.5), _f(0.25)], regs=regs)
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    got = struct.unpack('<ff', h.uc.mem_read(obj + 0x74, 8))
    if got != (1.5, 2.25) or h.uc.mem_read(obj + 0x7c, 1) != b'\x01':
        return ['size %r' % (got,)]
    return None


def test_004265B0(h):
    obj = h.alloc(0x80, b'\xEE' * 0x80)
    h.uc.mem_write(obj + 0x74, struct.pack('<ff', 1.0, 2.0))
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x11223344}
    diffs = h.compare(0x004265B0, args=[_f(0.5)], regs=regs, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x80)
    h.uc.mem_write(obj + 0x74, struct.pack('<ff', 1.0, 2.0))
    res = h.call(0x004265B0, args=[_f(0.5)], regs=regs)
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    got = struct.unpack('<ff', h.uc.mem_read(obj + 0x74, 8))
    if got != (1.5, 2.0) or h.uc.mem_read(obj + 0x7c, 1) != b'\x01':
        return ['size %r' % (got,)]
    return None


def test_004265D0(h):
    obj = h.alloc(0x80, b'\xEE' * 0x80)
    h.uc.mem_write(obj + 0x74, struct.pack('<ff', 1.0, 2.0))
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x11223344}
    diffs = h.compare(0x004265D0, args=[_f(0.5)], regs=regs, ret='eax')
    if diffs:
        return [str(d) for d in diffs]
    h.uc.mem_write(obj, b'\xEE' * 0x80)
    h.uc.mem_write(obj + 0x74, struct.pack('<ff', 1.0, 2.0))
    res = h.call(0x004265D0, args=[_f(0.5)], regs=regs)
    if res['fault']:
        return ['faulted: %s' % (res['fault'],)]
    got = struct.unpack('<ff', h.uc.mem_read(obj + 0x74, 8))
    if got != (1.0, 2.5) or h.uc.mem_read(obj + 0x7c, 1) != b'\x01':
        return ['size %r' % (got,)]
    return None
