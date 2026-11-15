"""The CRenderObject2D virtual-forwarding wrappers:
0x004265F0 (ECX, ret 4): slot +0x7c gets -(point - size(+0x74/+0x78)) / 2, slot +0x98 gets the point.
0x00426660 (ECX, ret 8): slot +0x78 gets (x, y) - size scaled by 0x00608090 (-0.5), slot +0x94 gets (x, y).
0x004266D0 (ECX, ret 4): slot +0x80 gets (x - size_x) scaled by -0.5, slot +0x9c gets x.
0x00426710 (ECX, ret 4): slot +0x84 gets (y - size_y) scaled by -0.5, slot +0xa0 gets y.
0x004267B0 (ECX, ret 8): slot +0x78 gets -(x, y) / 2, slot +0xa4 gets (x, y).
0x00426810 (ECX, ret 4): slot +0x80 gets -x / 2, slot +0xac gets x.
0x00426850 (ECX, ret 4): slot +0x84 gets -y / 2, slot +0xb0 gets y.
Each reloads the vtable before the second call."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

L1 = 0x00           # the scaled call: count, this, arg 1, arg 2
L2 = 0x10           # the forwarding call
L2B = 0x20          # the forwarding call through the retargeted vtable
L_MODE = 0x40
LOG_SIZE = 0x80
RETVAL = 0x5A5A

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _stub_code(log, ret, nargs, indirect=False, retarget=None):
    code = b'\xFF\x05' + _dword(log)                       # inc [count]
    code += b'\x89\x0D' + _dword(log + 4)                  # ecx -> this
    if nargs >= 1 and indirect:
        code += b'\x8B\x44\x24\x04'                        # eax = [esp+4] (point)
        code += b'\x8B\x10\x89\x15' + _dword(log + 8)      # [point] -> arg 1
        code += b'\x8B\x50\x04\x89\x15' + _dword(log + 12)  # [point+4] -> arg 2
    elif nargs >= 1:
        code += b'\x8B\x44\x24\x04\xA3' + _dword(log + 8)  # [esp+4] -> arg 1
    if nargs >= 2 and not indirect:
        code += b'\x8B\x44\x24\x08\xA3' + _dword(log + 12)  # [esp+8] -> arg 2
    if retarget is not None:
        code += b'\xA1' + _dword(log + L_MODE)             # eax = [mode]
        code += b'\x85\xC0'                                # test eax, eax
        code += b'\x74\x06'                                # jz skip
        code += b'\xC7\x01' + _dword(retarget)             # mov [ecx], vt2
    code += b'\xB8' + _dword(RETVAL)                       # mov eax, RETVAL
    code += b'\xC2' + struct.pack('<H', ret)               # ret N
    return code


FIRST = {0x78: (2, False), 0x7c: (1, True), 0x80: (1, False), 0x84: (1, False)}
SECOND = {0x94: (2, False), 0x98: (1, True), 0x9c: (1, False), 0xa0: (1, False),
          0xa4: (2, False), 0xac: (1, False), 0xb0: (1, False)}


def test_wrappers(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        vt1 = h.alloc(0x200, b'\xCC' * 0x200)
        vt2 = h.alloc(0x200, b'\xCC' * 0x200)
        for slot, (nargs, indirect) in FIRST.items():
            h.uc.mem_write(vt1 + slot, _dword(_stub(h, _stub_code(log + L1, 4 * nargs, nargs, indirect, vt2))))
        for slot, (nargs, indirect) in SECOND.items():
            h.uc.mem_write(vt1 + slot, _dword(_stub(h, _stub_code(log + L2, 4 * nargs, nargs, indirect))))
            h.uc.mem_write(vt2 + slot, _dword(_stub(h, _stub_code(log + L2B, 4 * nargs, nargs, indirect))))
        obj = h.alloc(0x80, b'\xEE' * 0x80)
        point = h.alloc(0x10, bytes(0x10))

        X, Y = 1.5, -2.25
        SX, SY = 0.25, 0.5

        def setup(mode, x, y):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_MODE, _dword(mode))
            h.uc.mem_write(obj, b'\xEE' * 0x80)
            h.uc.mem_write(obj, _dword(vt1))
            h.uc.mem_write(obj + 0x74, struct.pack('<ff', SX, SY))
            h.uc.mem_write(point, struct.pack('<ff', x, y) + b'\xAA' * 8)

        def scaled_half(delta):
            return _bits(-0.5 * delta)

        def scaled_half_f32(delta):
            return _bits(_f32(delta * -0.5))

        cases = (
            # addr, args, expected scaled call, expected forwarded call
            (0x004265F0, [point], (scaled_half(_f32(X - SX)), scaled_half(_f32(Y - SY))), (_bits(X), _bits(Y))),
            (0x00426660, [_bits(X), _bits(Y)], (scaled_half_f32(X - SX), scaled_half_f32(Y - SY)), (_bits(X), _bits(Y))),
            (0x004266D0, [_bits(X)], scaled_half_f32(X - SX), _bits(X)),
            (0x00426710, [_bits(Y)], scaled_half_f32(Y - SY), _bits(Y)),
            (0x004267B0, [_bits(X), _bits(Y)], (scaled_half(X), scaled_half(Y)), (_bits(X), _bits(Y))),
            (0x00426810, [_bits(X)], scaled_half(X), _bits(X)),
            (0x00426850, [_bits(Y)], scaled_half(Y), _bits(Y)),
        )
        for addr, args, want1, want2 in cases:
            want1 = want1 if isinstance(want1, tuple) else (want1,)
            want2 = want2 if isinstance(want2, tuple) else (want2,)
            for mode in (0, 1):
                setup(mode, X, Y)
                diffs = h.compare(addr, args=args, regs={UC_X86_REG_ECX: obj}, ret='eax')
                if diffs:
                    return ['%08X mode %d: %s' % (addr, mode, d) for d in diffs]
                setup(mode, X, Y)
                res = h.call(addr, args=args, regs={UC_X86_REG_ECX: obj})
                if res['fault']:
                    return ['%08X mode %d: replacement faulted: %s' % (addr, mode, res['fault'])]
                if res['eax'] != RETVAL:
                    return ['%08X mode %d: returned %08X' % (addr, mode, res['eax'])]
                if _u32(h, log + L1) != 1:
                    return ['%08X mode %d: the scaled call ran %d times' % (addr, mode, _u32(h, log + L1))]
                if _u32(h, log + L1 + 4) != obj:
                    return ['%08X mode %d: the scaled call got this %08X' % (addr, mode, _u32(h, log + L1 + 4))]
                got = tuple(_u32(h, log + L1 + 8 + 4 * i) for i in range(len(want1)))
                if got != want1:
                    return ['%08X mode %d: the scaled args are (%s), want (%s)'
                            % (addr, mode, ', '.join('%08X' % v for v in got), ', '.join('%08X' % v for v in want1))]
                dst = L2B if mode else L2
                other = L2 if mode else L2B
                if _u32(h, log + dst) != 1 or _u32(h, log + other) != 0:
                    return ['%08X mode %d: the forwarded call ran %d times in its slot (other %d)'
                            % (addr, mode, _u32(h, log + dst), _u32(h, log + other))]
                if _u32(h, log + dst + 4) != obj:
                    return ['%08X mode %d: the forwarded call got this %08X' % (addr, mode, _u32(h, log + dst + 4))]
                got = tuple(_u32(h, log + dst + 8 + 4 * i) for i in range(len(want2)))
                if got != want2:
                    return ['%08X mode %d: the forwarded args are (%s), want (%s)'
                            % (addr, mode, ', '.join('%08X' % v for v in got), ', '.join('%08X' % v for v in want2))]
                if _u32(h, obj) != (vt2 if mode else vt1):
                    return ['%08X mode %d: the vtable is %08X' % (addr, mode, _u32(h, obj))]
                if bytes(h.uc.mem_read(point + 8, 8)) != b'\xAA' * 8:
                    return ['%08X mode %d: bytes past the point changed' % (addr, mode)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
