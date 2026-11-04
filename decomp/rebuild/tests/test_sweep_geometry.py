"""Exercise geometry comparisons and float stores exposed by the v57 sweep."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_FPCW


def bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def test_triangle_side(h):
    points = [h.alloc(8, bytes(8)) for _ in range(3)]
    cases = (
        (((0, 0), (1, 0), (0, 1)), 0),
        (((0, 1), (1, 0), (0, 0)), 1),
        (((0, 0), (1, 0), (0, 0)), 1),
        (((float('nan'), 0), (1, 0), (0, 1)), 1),
        (((1, 3e38), (0, -3e38), (2, 3e38)), 1),
    )
    control = h.uc.reg_read(UC_X86_REG_FPCW)
    diffs = []
    try:
        for cw in (0x27f, 0x7f):
            h.uc.reg_write(UC_X86_REG_FPCW, cw)
            for coords, expected in cases:
                for address, point in zip(points, coords):
                    h.uc.mem_write(address, struct.pack('<ff', *point))
                label = f'cw={cw:x} points={coords}'
                diffs.extend(f'{label}: {diff}' for diff in h.compare(0x0058F2B0, points))
                result = h.call(h.to_rebuilt(0x0058F2B0), points)
                if result['fault'] or result['eax'] != expected:
                    diffs.append(f'{label}: expected {expected}, got {result}')
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, control)
    return diffs


def test_track_delta_scaling(h):
    track = h.alloc(0x1dc, bytes(0x1dc))
    records = h.alloc(24, bytes(24))
    obj = h.alloc(0x78, bytes(0x78))
    out = h.alloc(8, bytes(8))
    h.uc.mem_write(track + 0x1d8, struct.pack('<I', records))
    h.uc.mem_write(obj + 0x6c, struct.pack('<Iff', track, 0.125, -0.125))
    diffs = []
    control = h.uc.reg_read(UC_X86_REG_FPCW)
    try:
        for cw in (0x27f, 0x7f):
            h.uc.reg_write(UC_X86_REG_FPCW, cw)
            for left, right, gain, expected in (
                (1.0, 5.0, 2.0, (1.0, -1.0)),
                (0.0, 2e38, 2.0, (float('inf'), -float('inf'))),
            ):
                h.uc.mem_write(records + 8, struct.pack('<f', left))
                h.uc.mem_write(records + 20, struct.pack('<f', right))
                args = (out, 1, 0, bits(gain))
                regs = {UC_X86_REG_ECX: obj}
                label = f'cw={cw:x} left={left} right={right} gain={gain}'
                diffs.extend(f'{label}: {diff}' for diff in h.compare(0x005201B0, args, regs, ret=None))
                result = h.call(h.to_rebuilt(0x005201B0), args, regs)
                observed = struct.unpack('<ff', h.uc.mem_read(out, 8))
                if result['fault'] or observed != expected:
                    diffs.append(f'{label}: expected {expected}, got {observed}')
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, control)
    return diffs


def test_track_delta_integer_index(h):
    track = h.alloc(0x1dc, bytes(0x1dc))
    records = h.alloc(24, struct.pack('<6f', 1, 0, 0, 5, 0, 0))
    out = h.alloc(8, bytes(8))
    h.uc.mem_write(track + 0x1d8, struct.pack('<I', records))
    regs = {UC_X86_REG_ECX: track}
    diffs = []
    for first, index, expected in ((0, 1, (4.0, -0.0)), (0, 0, (0.0, -0.0)),
                                   (0x7fc00000, 0x7fc00000, (0.0, -0.0))):
        h.uc.mem_write(track + 0x1d0, struct.pack('<I', first))
        args = (out, bits(0), index)
        diffs.extend(f'index={index:08x}: {diff}' for diff in h.compare(0x0042AC80, args, regs))
        result = h.call(h.to_rebuilt(0x0042AC80), args, regs)
        if result['fault'] or bytes(h.uc.mem_read(out, 8)) != struct.pack('<ff', *expected):
            diffs.append(f'index={index:08x}: expected {expected}, got {result}')
    return diffs


def test_plane_height_denominator(h):
    normal = h.alloc(12, bytes(12))
    origin = h.alloc(12, struct.pack('<fff', 0.0, 5.0, 0.0))
    point = h.alloc(12, bytes(12))
    diffs = []
    for y_bits, expected in ((bits(2), bits(3)), (0xffc01234, 0x7fc01234)):
        h.uc.mem_write(normal, struct.pack('<III', bits(1), y_bits, bits(1)))
        h.uc.mem_write(point, struct.pack('<fff', 1.0, 0.0, 3.0))
        args = (normal, origin, point)
        diffs.extend(f'ny={y_bits:08x}: {diff}' for diff in h.compare(0x00456B20, args, ret=None))
        result = h.call(h.to_rebuilt(0x00456B20), args)
        height, = struct.unpack('<I', h.uc.mem_read(point + 4, 4))
        if result['fault'] or height != expected:
            diffs.append(f'ny={y_bits:08x}: expected height {expected:08x}, got {height:08x}')
    return diffs


def test_turn_update(h):
    obj = h.alloc(0x98, bytes(0x98))
    regs = {UC_X86_REG_ECX: obj}
    diffs = []
    for angle_bits, expected in ((bits(90), bits(11.25)), (bits(270), bits(-11.25)),
                                 (0x7fc00000, 0xffc00000)):
        h.uc.mem_write(obj + 0x78, bytes(0x20))
        args = (angle_bits, 8)
        label = f'angle={angle_bits:08x}'
        diffs.extend(f'{label}: {diff}' for diff in h.compare(0x004ACB80, args, regs))
        result = h.call(h.to_rebuilt(0x004ACB80), args, regs)
        observed = struct.unpack('<IIB3xII', h.uc.mem_read(obj + 0x84, 20))
        if result['fault'] or result['eax'] != 8 or observed != (angle_bits, expected, 1, 0, 8):
            diffs.append(f'{label}: unexpected turn update {observed}, eax={result["eax"]:08x}')
    return diffs


def test_terrain_transform_translation(h):
    obj = h.alloc(0x1cc, bytes(0x1cc))
    item = h.alloc(0xbc, bytes(0xbc))
    delta = h.alloc(8, struct.pack('<ff', 2.0, -3.0))
    height = h.alloc(4, struct.pack('<f', 7.0))
    query = h.to_rebuilt(0x00473110)
    cases = (
        (bytes.fromhex('d905') + struct.pack('<I', height) + bytes.fromhex('c20800'), 7.0),
        (bytes.fromhex('d9442404 d8442408 c20800'), 29.0),  # height = x + z
        (bytes.fromhex('d9442408 d8642404 c20800'), 5.0),  # height = z - x
    )
    original = bytes(h.uc.mem_read(query, max(len(stub) for stub, _ in cases)))
    control = h.uc.reg_read(UC_X86_REG_FPCW)
    diffs = []
    try:
        args = (item, delta)
        regs = {UC_X86_REG_ECX: obj}
        for cw in (0x27f, 0x7f):
            h.uc.reg_write(UC_X86_REG_FPCW, cw)
            for stub, y in cases:
                h.uc.mem_write(item + 0x58, struct.pack('<fff', 10.0, 20.0, 1.0))
                h.uc.mem_write(item + 0xac, struct.pack('<fff', 100.0, 0.0, 200.0))
                h.uc.mem_write(query, stub)
                h.uc.ctl_remove_cache(query, query + 16)
                label = f'cw={cw:x} height={y}'
                # EAX contains a pointer into the completed call's temporary matrix.
                diffs.extend(f'{label}: {diff}' for diff in h.compare(0x0052CDF0, args, regs, ret=None))
                result = h.call(h.to_rebuilt(0x0052CDF0), args, regs)
                translation = struct.unpack('<fff', h.uc.mem_read(item + 0xac, 12))
                if result['fault'] or translation != (102.0, y, 197.0):
                    diffs.append(f'{label}: expected translation (102, {y}, 197), got {translation}')
    finally:
        h.uc.mem_write(query, original)
        h.uc.ctl_remove_cache(query, query + 16)
        h.uc.reg_write(UC_X86_REG_FPCW, control)
    return diffs
