"""Distance keys must keep the original x/y/z sum order at the game's x87 precision."""
import struct


def test_distance_keys(h):
    from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_FPCW
    world = h.alloc(0x60, bytes(0x60))
    h.uc.mem_write(world + 0x5c, struct.pack('<I', 1))
    level = h.alloc(4, struct.pack('<I', 2))
    camera = h.alloc(0x90, bytes(0x90))
    h.uc.mem_write(camera + 0x5c, struct.pack('<f', 8.0))
    pulled = h.alloc(4, bytes(4))
    container = h.alloc(16, bytes(16))
    stubs = [(0x0042F160, b'\xb8' + struct.pack('<I', world) + b'\xc3'),
             (0x00432260, b'\xa1' + struct.pack('<I', level) + b'\xc3'),
             (0x004F9ED0, b'\xb8' + struct.pack('<I', camera) + b'\xc3'),
             (0x00558440, b'\xff\x05' + struct.pack('<I', pulled) + bytes.fromhex('c20400')),
             (0x00556100, b'\xc3'), (0x00556020, bytes.fromhex('c20800'))]
    saved = []
    cw = h.uc.reg_read(UC_X86_REG_FPCW)
    diffs = []
    try:
        for address, code in stubs:
            saved.append((address, bytes(h.uc.mem_read(address, max(5, len(code))))))
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        for control in (0x27f, 0x7f):
            for matched, pull in ((False, False), (True, False), (True, True)):
                h.uc.mem_write(level, struct.pack('<I', 1 if matched else 2))
                for count in (0, 1, 4, 17):
                    points = [(1.0, 1.0, 4096.0), (3.0, -2.0, 0.5),
                              (4096.0, 1.0, 1.0), (-0.25, 7.0, -3.0)]
                    data = b''.join(struct.pack('<6f', *points[i % 4], 0, 0, 0) for i in range(count))
                    positions = h.alloc(max(24, len(data)), data or bytes(24))
                    keys = h.alloc(max(8, count * 8), bytes(max(8, count * 8)))
                    obj = h.alloc(0x40, bytes(0x40))
                    h.uc.mem_write(obj + 0x10, struct.pack('<I', count))
                    actors = h.alloc(max(0x48, count * 0x48), bytes(max(0x48, count * 0x48)))
                    for i in range(count):
                        coordinate = 0.0 if pull else 100.0
                        h.uc.mem_write(actors + i * 0x48 + 0x38, struct.pack('<f', coordinate))
                        h.uc.mem_write(actors + i * 0x48 + 0x40, struct.pack('<f', coordinate))
                    h.uc.mem_write(obj + 0x18, struct.pack('<I', actors))
                    h.uc.mem_write(obj + 0x24, struct.pack('<I', count))
                    h.uc.mem_write(pulled, bytes(4))
                    h.uc.mem_write(obj + 0x2c, struct.pack('<I', positions))
                    h.uc.mem_write(obj + 0x38, struct.pack('<I', keys))
                    origin = h.alloc(12, bytes(12))
                    h.uc.reg_write(UC_X86_REG_FPCW, control)
                    diffs += ['cw=%x n=%d: %s' % (control, count, d)
                              for d in h.compare(0x00558520, args=[origin, container],
                                                 regs={UC_X86_REG_ECX: obj}, ret=None)]
                    result = h.call(0x00558520, args=[origin, container], regs={UC_X86_REG_ECX: obj})
                    if result['fault']:
                        diffs.append('bounded distance buffer faulted: %s' % result['fault'])
                    if count and control == 0x7f:
                        key = struct.unpack('<I', h.uc.mem_read(keys + 4, 4))[0]
                        if key != 0x4b800001:
                            diffs.append('single-precision (1+1)+4096^2 key %08X, expected 4B800001' % key)
                    expected = count if matched and pull else 0
                    if struct.unpack('<I', h.uc.mem_read(pulled, 4))[0] != expected:
                        diffs.append('actor-radius callback count mismatch')
                    if struct.unpack('<I', h.uc.mem_read(obj + 0x24, 4))[0] != count - expected:
                        diffs.append('active instance count mismatch')
    finally:
        for address, data in saved:
            h.uc.mem_write(address, data)
            h.uc.ctl_remove_cache(address, address + len(data))
        h.uc.reg_write(UC_X86_REG_FPCW, cw)
    return diffs
