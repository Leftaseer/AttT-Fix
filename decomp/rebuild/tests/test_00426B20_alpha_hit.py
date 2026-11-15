"""The alpha button internals:
0x00426890 (ECX): naked jump through vtable slot +0xD4.
0x00426B10 (ECX, EAX): with +0x49 set, tail-calls the +0x4796D0 virtual; else returns EAX.
0x00426B20 (ECX,EAX, ret 8): with +0x9D set and (x, y) inside the +0xAC/+0xB0 rect (size +0xC8/+0xCC), plays the
current texture slot (virtual slots 4 and 5, texture reloaded between them) and returns AL = 1; otherwise clears AL."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


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


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    return stub


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def test_00426890(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x10, bytes(0x10))
        target = _stub(h, b'\x89\x0D' + _dword(log) + b'\xB8\x44\x33\x22\x11\xC3')
        vt = h.alloc(0xD8, bytes(0xD8))
        h.uc.mem_write(vt + 0xD4, _dword(target))
        obj = h.alloc(0x10, _dword(vt) + bytes(0xC))
        diffs = h.compare(0x00426890, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x10))
        res = h.call(0x00426890, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if res['eax'] != 0x11223344:
            return ['returned %08X' % res['eax']]
        if _u32(h, log) != obj:
            return ['the virtual got ECX %08X' % _u32(h, log)]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00426B10(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x10, bytes(0x10))
        _hook(h, 0x004796D0, b'\x89\x0D' + _dword(log) + b'\xB8\x77\x77\x77\x77\xC3')
        obj = h.alloc(0x60, b'\xEE' * 0x60)
        for flag in (0, 1, 0x80):
            h.uc.mem_write(obj + 0x49, bytes([flag]))
            h.uc.mem_write(log, bytes(0x10))
            diffs = h.compare(0x00426B10, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0xAABBCCDD}, ret='eax')
            if diffs:
                return ['flag %02X: %s' % (flag, d) for d in diffs]
            h.uc.mem_write(obj + 0x49, bytes([flag]))
            h.uc.mem_write(log, bytes(0x10))
            res = h.call(0x00426B10, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0xAABBCCDD})
            if res['fault']:
                return ['flag %02X: replacement faulted: %s' % (flag, res['fault'])]
            if flag:
                if res['eax'] != 0x77777777:
                    return ['flag %02X: returned %08X instead of the update virtual' % (flag, res['eax'])]
                if _u32(h, log) != obj:
                    return ['flag %02X: the update virtual got %08X' % (flag, _u32(h, log))]
            else:
                if res['eax'] != 0xAABBCCDD or _u32(h, log):
                    return ['flag 0: EAX is %08X, the virtual ran %d times' % (res['eax'], _u32(h, log))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


L_A = 0x00
L_B = 0x10
L_THIS = 0x20
RETVAL = 0x12345678


def test_00426B20(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        # slot 1's play virtual retargets +0x98 to texture 2, so the second lookup must reload it
        play = _stub(h, b'\x89\x0D' + _dword(log + L_A) + b'\xA1' + _dword(log + L_THIS)
                     + b'\x8B\x15' + _dword(log + 0x30) + b'\x89\x90\x98\x00\x00\x00' + b'\xC3')
        query = _stub(h, b'\x89\x0D' + _dword(log + L_B) + b'\xB8' + _dword(RETVAL) + b'\xC3')
        vt1 = h.alloc(0x18, bytes(0x18))
        h.uc.mem_write(vt1 + 0x10, _dword(play))
        h.uc.mem_write(vt1 + 0x14, _dword(play))
        vt2 = h.alloc(0x18, bytes(0x18))
        h.uc.mem_write(vt2 + 0x10, _dword(play))
        h.uc.mem_write(vt2 + 0x14, _dword(query))
        slot1 = h.alloc(0x10, _dword(vt1) + bytes(0xC))
        slot2 = h.alloc(0x10, _dword(vt2) + bytes(0xC))
        tex1 = h.alloc(0x60, bytes(0x60))
        slots1 = h.alloc(4, _dword(slot1))
        h.uc.mem_write(tex1 + 0x38, _dword(slots1))
        h.uc.mem_write(tex1 + 0x40, _dword(0))
        tex2 = h.alloc(0x60, bytes(0x60))
        slots2 = h.alloc(4, _dword(slot2))
        h.uc.mem_write(tex2 + 0x38, _dword(slots2))
        h.uc.mem_write(tex2 + 0x40, _dword(0))
        obj = h.alloc(0xD0, b'\xEE' * 0xD0)
        h.uc.mem_write(log + L_THIS, _dword(obj))
        h.uc.mem_write(log + 0x30, _dword(tex2))
        h.uc.mem_write(obj + 0x98, _dword(tex1))
        h.uc.mem_write(obj + 0xac, struct.pack('<f', -10.0))
        h.uc.mem_write(obj + 0xb0, struct.pack('<f', 20.0))
        h.uc.mem_write(obj + 0xc8, struct.pack('<f', 100.0))
        h.uc.mem_write(obj + 0xcc, struct.pack('<f', 60.0))
        h.uc.mem_write(obj + 0x9d, b'\x01')

        cases = [
            ('flag off', 0x00, 50.0, 50.0, 0x00),
            ('px below', 0x01, -10.5, 50.0, 0x00),
            ('px at origin', 0x01, -10.0, 20.0, 0x01),
            ('px at width', 0x01, 90.0, 20.0, 0x01),
            ('px past width', 0x01, 90.5, 20.0, 0x00),
            ('py below', 0x01, 0.0, 19.0, 0x00),
            ('py at height', 0x01, 0.0, 80.0, 0x01),
            ('py past height', 0x01, 0.0, 80.5, 0x00),
        ]

        def setup(flag, x, y, tex_reset):
            h.uc.mem_write(log, bytes(0x40))
            h.uc.mem_write(log + L_THIS, _dword(obj))
            h.uc.mem_write(log + 0x30, _dword(tex2))
            h.uc.mem_write(obj + 0x9d, bytes([flag]))
            if tex_reset:
                h.uc.mem_write(obj + 0x98, _dword(tex1))
            return [ _f(x), _f(y) ]

        for name, flag, x, y, inside in cases:
            args = setup(flag, x, y, True)
            regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0xAABBCCDD}
            diffs = h.compare(0x00426B20, args=args, regs=regs, ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            args = setup(flag, x, y, True)
            res = h.call(0x00426B20, args=args, regs=regs)
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            want = (RETVAL & 0xFFFFFF00) | 1 if inside else 0xAABBCC00
            if res['eax'] != want:
                return ['%s: returned %08X, expected %08X' % (name, res['eax'], want)]
            if not inside:
                if _u32(h, log + L_A) or _u32(h, log + L_B):
                    return ['%s: the texture virtuals ran' % name]
                continue
            if _u32(h, log + L_A) != slot1 or _u32(h, log + L_B) != slot2:
                return ['%s: the slots were %08X / %08X'
                        % (name, _u32(h, log + L_A), _u32(h, log + L_B))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0
