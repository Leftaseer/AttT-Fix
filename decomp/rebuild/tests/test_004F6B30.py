"""Frame construction with bounded vectors, a synthetic terrain surface and a NaN surface."""

import struct


def test_frame_builder(h):
    from unicorn.x86_const import UC_X86_REG_FPCW
    diffs = []
    saved = []
    cw = h.uc.reg_read(UC_X86_REG_FPCW)
    # Getter's result is ignored by our thiscall height stub.
    getter = b'\xb8' + struct.pack('<I', h.alloc(16, bytes(16))) + b'\xc3'
    # height(x, z) = x*x + z; the four corners do not lie on one plane.
    surface = bytes.fromhex('d9442404 d84c2404 d8442408 c20800')
    nan = h.alloc(4, struct.pack('<I', 0xffffffff))
    nan_surface = b'\xd9\x05' + struct.pack('<I', nan) + b'\xc2\x08\x00'
    try:
        for address, code in ((0x00433620, getter), (0x00473110, surface)):
            saved.append((address, bytes(h.uc.mem_read(address, max(len(code), len(nan_surface))))))
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        for height in (surface, nan_surface):
            h.uc.mem_write(0x00473110, height)
            h.uc.ctl_remove_cache(0x00473110, 0x00473110 + len(surface))
            for control in (0x27f, 0x7f):
                vectors = h.alloc(48, struct.pack('<12f', 0, 0, 0, 1, 0, 0, 2, 0, 1, 0, 0, 1))
                outputs = [h.alloc(4, bytes(4)) for _ in range(3)]
                fbits = lambda f: struct.unpack('<I', struct.pack('<f', f))[0]
                matrix = [fbits(1.0 if i % 5 == 0 else 0.0) for i in range(16)]
                args = [vectors, fbits(0.25), 0, fbits(0.75), *matrix, *outputs]
                h.uc.reg_write(UC_X86_REG_FPCW, control)
                diffs += ['cw=%x nan=%s: %s' % (control, height == nan_surface, d)
                          for d in h.compare(0x004F6B30, args=args, ret='eax')]
                result = h.call(0x004F6B30, args=args)
                if result['fault']:
                    diffs.append('bounded frame builder faulted: %s' % result['fault'])
    finally:
        for address, code in saved:
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        h.uc.reg_write(UC_X86_REG_FPCW, cw)
    return diffs
