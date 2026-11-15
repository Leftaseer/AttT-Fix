"""sub_00426750 (size 96, ECX thiscall, ret 4): hands the point arg 1 to two virtuals of the object: the slot at
+0x7c receives the point negated and multiplied by the double at 0x00607CE0 (0.5), then the slot at +0xa8 receives
the original point; the vtable is reloaded for the second call."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00426750
SCALE = 0x00607CE0
SLOT_A = 0x7c
SLOT_B = 0xa8

L_C7 = 0x00
L_C7_THIS = 0x04
L_C7_X = 0x08
L_C7_Y = 0x0C
L_CA = 0x10
L_CA_THIS = 0x14
L_CA_PTR = 0x18
L_CB = 0x1C
L_CB_THIS = 0x20
L_CB_PTR = 0x24
L_MODE = 0x28
LOG_SIZE = 0x40

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


def test_00426750(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        vt1 = h.alloc(0x100, bytes(0x100))
        vt2 = h.alloc(0x100, bytes(0x100))
        stub7 = _stub(h, b'\xFF\x05' + _dword(log + L_C7)                     # inc [scaled calls]
                         + b'\x89\x0D' + _dword(log + L_C7_THIS)              # ecx -> this
                         + b'\x8B\x44\x24\x04'                             # eax = [esp+4] (point)
                         + b'\x8B\x10\x89\x15' + _dword(log + L_C7_X)         # [point] -> x
                         + b'\x8B\x50\x04\x89\x15' + _dword(log + L_C7_Y)     # [point+4] -> y
                         + b'\xA1' + _dword(log + L_MODE)                     # mov eax, [mode]
                         + b'\x85\xC0'                                        # test eax, eax
                         + b'\x74\x06'                                        # jz skip
                         + b'\xC7\x01' + _dword(vt2)                          # mov [ecx], vt2
                         + b'\xC2\x04\x00')                                   # skip: ret 4
        stubA = _stub(h, b'\xFF\x05' + _dword(log + L_CA)                     # inc [original calls]
                         + b'\x89\x0D' + _dword(log + L_CA_THIS)              # ecx -> this
                         + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_CA_PTR)   # [esp+4] -> point
                         + b'\xC2\x04\x00')                                   # ret 4
        stubB = _stub(h, b'\xFF\x05' + _dword(log + L_CB)                     # inc [retargeted calls]
                         + b'\x89\x0D' + _dword(log + L_CB_THIS)              # ecx -> this
                         + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_CB_PTR)   # [esp+4] -> point
                         + b'\xC2\x04\x00')                                   # ret 4
        h.uc.mem_write(vt1 + SLOT_A, _dword(stub7))
        h.uc.mem_write(vt1 + SLOT_B, _dword(stubA))
        h.uc.mem_write(vt2 + SLOT_B, _dword(stubB))
        obj = h.alloc(0x10, bytes(0x10))
        point = h.alloc(0x10, bytes(0x10))
        scale = struct.unpack('<d', h.uc.mem_read(SCALE, 8))[0]

        def setup(mode, x, y):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_MODE, _dword(mode))
            h.uc.mem_write(obj, b'\x11' * 0x10)
            h.uc.mem_write(obj, _dword(vt1))
            h.uc.mem_write(point, struct.pack('<ff', x, y) + b'\xAA' * 8)

        cases = [('point', 0, 1.5, -2.25),
                 ('zeros', 0, 0.0, 0.0),
                 ('retarget', 1, 3.25, 0.75)]
        for name, mode, x, y in cases:
            setup(mode, x, y)
            diffs = h.compare(VF, args=[point], regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(mode, x, y)
            res = h.call(VF, args=[point], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            want_x = _bits(-(float(x)) * scale)
            want_y = _bits(-(float(y)) * scale)
            if _u32(h, log + L_C7) != 1:
                return ['%s: the scaled point arrived %d times' % (name, _u32(h, log + L_C7))]
            if _u32(h, log + L_C7_THIS) != obj:
                return ['%s: the scaled point went to %08X' % (name, _u32(h, log + L_C7_THIS))]
            if _u32(h, log + L_C7_X) != want_x or _u32(h, log + L_C7_Y) != want_y:
                return ['%s: the scaled point is (%08X, %08X)'
                        % (name, _u32(h, log + L_C7_X), _u32(h, log + L_C7_Y))]
            if mode:
                if _u32(h, log + L_CB) != 1 or _u32(h, log + L_CA) != 0:
                    return ['%s: the retargeted slot ran %d times (old %d)'
                            % (name, _u32(h, log + L_CB), _u32(h, log + L_CA))]
                if _u32(h, log + L_CB_THIS) != obj or _u32(h, log + L_CB_PTR) != point:
                    return ['%s: the retargeted call got (%08X, %08X)'
                            % (name, _u32(h, log + L_CB_THIS), _u32(h, log + L_CB_PTR))]
                if _u32(h, obj) != vt2:
                    return ['%s: the vtable is %08X' % (name, _u32(h, obj))]
            else:
                if _u32(h, log + L_CA) != 1 or _u32(h, log + L_CB) != 0:
                    return ['%s: the original slot ran %d times (new %d)'
                            % (name, _u32(h, log + L_CA), _u32(h, log + L_CB))]
                if _u32(h, log + L_CA_THIS) != obj or _u32(h, log + L_CA_PTR) != point:
                    return ['%s: the original call got (%08X, %08X)'
                            % (name, _u32(h, log + L_CA_THIS), _u32(h, log + L_CA_PTR))]
                if _u32(h, obj) != vt1:
                    return ['%s: the vtable is %08X' % (name, _u32(h, obj))]
            if bytes(h.uc.mem_read(point + 8, 8)) != b'\xAA' * 8:
                return ['%s: bytes past the point changed' % name]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
