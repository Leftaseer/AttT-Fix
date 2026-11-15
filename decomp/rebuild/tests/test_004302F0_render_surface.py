"""sub_004302F0 (size 96, ECX thiscall, ret): while the render surface handle at +8 is missing, builds it with
D3DXCreateRenderToSurface (0x005B8050) for the device 0x006C8C10, half the screen (0x006C8964 x 0x006C8960), format
0x15, depth-stencil on and the depth-stencil format of the data root +0x5C, storing it at +8; then calls the virtual at
+0x2C of the object at +4, which yields a0, and [a0]+0x48 as a stdcall routine with (a0, 0, this+0xC).  The data root
(0x00427990) is asked for either way."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x004302F0
DATA_ROOT = 0x00427990
D3DX = 0x005B8050
G_HEIGHT = 0x006C8960
G_WIDTH = 0x006C8964
G_DEVICE = 0x006C8C10

L_ROOT = 0x00
L_ROOT_VAL = 0x04
L_D3DX = 0x08
L_DEV = 0x0C
L_W = 0x10
L_H = 0x14
L_FMT = 0x18
L_DEPTH = 0x1C
L_DFMT = 0x20
L_OUT = 0x24
L_VFN = 0x28
L_CTX = 0x2C
L_A0_VAL = 0x30
L_SLOT = 0x34
L_A0 = 0x38
L_ZERO = 0x3C
L_THIRD = 0x40
LOG_SIZE = 0x60

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


def test_004302F0(h):
    heap0 = h.heap_ptr
    globals0 = {a: bytes(h.uc.mem_read(a, 4)) for a in (G_HEIGHT, G_WIDTH, G_DEVICE)}
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, DATA_ROOT,
               b'\xFF\x05' + _dword(log + L_ROOT)                        # inc [data root calls]
               + b'\xA1' + _dword(log + L_ROOT_VAL)                      # mov eax, [root]
               + b'\xC3')                                                # ret
        _patch(h, D3DX,
               b'\xFF\x05' + _dword(log + L_D3DX)                        # inc [create calls]
               + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_DEV)           # [esp+4] -> device
               + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_W)             # [esp+8] -> width
               + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_H)             # [esp+12] -> height
               + b'\x8B\x44\x24\x10\xA3' + _dword(log + L_FMT)           # [esp+16] -> format
               + b'\x8B\x44\x24\x14\xA3' + _dword(log + L_DEPTH)         # [esp+20] -> depth
               + b'\x8B\x44\x24\x18\xA3' + _dword(log + L_DFMT)          # [esp+24] -> ds format
               + b'\x8B\x44\x24\x1C\xA3' + _dword(log + L_OUT)           # [esp+28] -> out
               + b'\x8B\x44\x24\x1C\xC7\x00' + _dword(0x12345678)        # *out = 12345678
               + b'\xB8' + _dword(0x11223344)                            # mov eax, hr
               + b'\xC2\x1C\x00')                                        # ret 0x1C
        stub_vfn = _stub(h, b'\xFF\x05' + _dword(log + L_VFN)             # inc [virtual calls]
                            + b'\x89\x0D' + _dword(log + L_CTX)           # ecx -> this
                            + b'\xA1' + _dword(log + L_A0_VAL)            # mov eax, [a0]
                            + b'\xC3')                                    # ret
        stub_slot = _stub(h, b'\xFF\x05' + _dword(log + L_SLOT)           # inc [slot calls]
                             + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_A0)    # [esp+4] -> a0
                             + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_ZERO)  # [esp+8] -> zero
                             + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_THIRD) # [esp+12] -> third
                             + b'\xC2\x0C\x00')                           # ret 0xC
        vt2 = h.alloc(0x100, bytes(0x100))
        vt3 = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(vt2 + 0x2c, _dword(stub_vfn))
        h.uc.mem_write(vt3 + 0x48, _dword(stub_slot))
        ctx = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(ctx, _dword(vt2))
        a0 = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(a0, _dword(vt3))
        root = h.alloc(0x80, bytes(0x80))
        self = h.alloc(0x20, bytes(0x20))
        DEV = 0x60006000
        WIDTH = 800
        HEIGHT = 600
        DFMT = 0x77770001

        def setup(handle):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_ROOT_VAL, _dword(root))
            h.uc.mem_write(log + L_A0_VAL, _dword(a0))
            h.uc.mem_write(G_HEIGHT, _dword(HEIGHT))
            h.uc.mem_write(G_WIDTH, _dword(WIDTH))
            h.uc.mem_write(G_DEVICE, _dword(DEV))
            h.uc.mem_write(root, b'\x22' * 0x80)
            h.uc.mem_write(root + 0x5c, _dword(DFMT))
            h.uc.mem_write(self, b'\x11' * 0x20)
            h.uc.mem_write(self + 4, _dword(ctx))
            h.uc.mem_write(self + 8, _dword(handle))

        for name, handle in (('missing', 0), ('present', 0xCAFE0000)):
            setup(handle)
            diffs = h.compare(VF, regs={UC_X86_REG_ECX: self}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(handle)
            res = h.call(VF, regs={UC_X86_REG_ECX: self})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if _u32(h, log + L_ROOT) != 1:
                return ['%s: the data root was asked %d times' % (name, _u32(h, log + L_ROOT))]
            if handle:
                if _u32(h, log + L_D3DX) or _u32(h, log + L_VFN) or _u32(h, log + L_SLOT):
                    return ['%s: the surface was rebuilt' % name]
                if _u32(h, self + 8) != handle:
                    return ['%s: the handle is %08X' % (name, _u32(h, self + 8))]
                continue
            if _u32(h, log + L_D3DX) != 1:
                return ['the surface was created %d times' % _u32(h, log + L_D3DX)]
            got = (_u32(h, log + L_DEV), _u32(h, log + L_W), _u32(h, log + L_H),
                   _u32(h, log + L_FMT), _u32(h, log + L_DEPTH), _u32(h, log + L_DFMT))
            want = (DEV, WIDTH >> 1, HEIGHT >> 1, 0x15, 1, DFMT)
            if got != want:
                return ['the surface was created as %r, not %r' % (got, want)]
            if _u32(h, log + L_OUT) != self + 8:
                return ['the surface went to %08X' % _u32(h, log + L_OUT)]
            if _u32(h, self + 8) != 0x12345678:
                return ['the handle is %08X' % _u32(h, self + 8)]
            if _u32(h, log + L_VFN) != 1 or _u32(h, log + L_CTX) != ctx:
                return ['the virtual ran %d times on %08X'
                        % (_u32(h, log + L_VFN), _u32(h, log + L_CTX))]
            if _u32(h, log + L_SLOT) != 1:
                return ['the surface slot ran %d times' % _u32(h, log + L_SLOT)]
            if _u32(h, log + L_A0) != a0 or _u32(h, log + L_ZERO) != 0 \
                    or _u32(h, log + L_THIRD) != self + 0xc:
                return ['the surface slot got (%08X, %08X, %08X)'
                        % (_u32(h, log + L_A0), _u32(h, log + L_ZERO), _u32(h, log + L_THIRD))]
    finally:
        for a, v in globals0.items():
            h.uc.mem_write(a, v)
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
