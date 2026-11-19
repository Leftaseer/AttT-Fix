"""sub_00589200 (size 304, ECX thiscall, ret 12): the TroopIconDragDroper constructor.  The base at 0x0058A3E0 gets
the two arguments, the vtables 0x0061ED2C/+0x214 0x0061ED20 are stored, +0x2B8 is cleared, argument 1 +0x74 goes to
0x004AC380 and the object string (+0x238) is assigned "TroopIconDragDroper".  The third argument (+0x2C0) creates the
child at +0x2B8 through 0x00587BF0 (context in ECX, returns an object whose +4 counts references): the count is
incremented and the previous child (always 0 here) released.  Then the context updates (vtable +0x50), the child's
+0x90 value less this +0x5C is stored at +0x2BC, and the child is told (vtable +0x68) that value plus this +0x5C and
half this +0x74 plus this +0x58.  The object is returned.  The three callees are stubbed (they need a live game)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00589200
BASE = 0x0058A3E0
AC = 0x004AC380
FAC = 0x00587BF0

L_SEQ = 0x00
L_TAGS = 0x04
L_BASE = 0x40
L_AC = 0x50
L_FAC = 0x60
L_UPD = 0x70
L_GET = 0x78
L_SET = 0x80
LOG_SIZE = 0x100

VTB_STD = 0x0061ED2C
VTB_SUB = 0x0061ED20

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(v):
    return struct.pack('<I', v & 0xFFFFFFFF)


def _f32(v):
    return struct.pack('<f', v)


def _f32u(v):
    return struct.unpack('<I', _f32(v))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _tag(seq, tag):
    return (b'\xA1' + _dword(seq)                                          # mov eax, [seq]
            + b'\xFF\x05' + _dword(seq)                                    # inc dword [seq]
            + b'\xC7\x04\x85' + _dword(seq + 4) + _dword(tag))             # mov dword [seq+4+eax*4], tag


def test_00589200(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        flt = h.alloc(4, _f32(0.0))
        # a stub that keeps a code page free of the tag/counter writes done at its own heap address
        s_this = h.alloc(0x300, bytes(0x300))
        s_arg1 = h.alloc(0x80, bytes(0x80))
        s_arg2 = h.alloc(0x20, bytes([0x5A] * 0x20))
        s_ctx = h.alloc(8, bytes(8))
        s_p = h.alloc(8, bytes(8))
        vt_ctx = h.alloc(0x54, bytes(0x54))
        vt_p = h.alloc(0x94, bytes(0x94))

        # 0x0058A3E0: base constructor (this, arg1, arg2); also lays out the empty object string at +0x238
        code = _tag(log + L_SEQ, 1)
        code += b'\x89\x0D' + _dword(log + L_BASE)                         # mov [log], ecx
        code += b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + L_BASE + 4)   # arg1
        code += b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + L_BASE + 8)   # arg2
        code += b'\xC7\x81' + _dword(0x24C) + _dword(0)                    # mov dword [ecx+0x24C], 0  (size)
        code += b'\xC7\x81' + _dword(0x250) + _dword(15)                   # mov dword [ecx+0x250], 15 (capacity)
        code += b'\xC2\x08\x00'
        _patch_thunk(h, BASE, code)

        # 0x004AC380: (this, arg1 + 0x74)
        code = _tag(log + L_SEQ, 2)
        code += b'\x89\x0D' + _dword(log + L_AC)
        code += b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + L_AC + 4)
        code += b'\xC2\x04\x00'
        _patch_thunk(h, AC, code)

        # 0x00587BF0: context in ECX, returns the child object
        code = _tag(log + L_SEQ, 3)
        code += b'\x89\x0D' + _dword(log + L_FAC)
        code += b'\xB8' + _dword(s_p)                                      # mov eax, child
        code += b'\xC3'
        _patch_thunk(h, FAC, code)

        # context vtable +0x50: update
        code = _tag(log + L_SEQ, 4)
        code += b'\x89\x0D' + _dword(log + L_UPD)
        code += b'\xC3'
        upd = _stub(h, code)
        # child vtable +0x90: float getter
        code = _tag(log + L_SEQ, 5)
        code += b'\x89\x0D' + _dword(log + L_GET)
        code += b'\xD9\x05' + _dword(flt)                                  # flds [value]
        code += b'\xC3'
        get = _stub(h, code)
        # child vtable +0x68: (float, float) setter
        code = _tag(log + L_SEQ, 6)
        code += b'\x89\x0D' + _dword(log + L_SET)
        code += b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + L_SET + 4)
        code += b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + L_SET + 8)
        code += b'\xC2\x08\x00'
        setter = _stub(h, code)

        h.uc.mem_write(vt_ctx + 0x50, _dword(upd))
        h.uc.mem_write(vt_ctx, _dword(0))
        h.uc.mem_write(s_ctx, _dword(vt_ctx))
        h.uc.mem_write(vt_p + 0x68, _dword(setter))
        h.uc.mem_write(vt_p + 0x90, _dword(get))
        h.uc.mem_write(s_p, _dword(vt_p))

        def setup(vals):
            f58, f5c, f74, get_value = vals
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(flt, _f32(get_value))
            h.uc.mem_write(s_this, bytes(0x300))
            h.uc.mem_write(s_this + 0x58, _f32(f58))
            h.uc.mem_write(s_this + 0x5c, _f32(f5c))
            h.uc.mem_write(s_this + 0x74, _f32(f74))
            h.uc.mem_write(s_arg1, bytes(0x80))
            h.uc.mem_write(s_arg1 + 0x74, _dword(0x77665544))
            h.uc.mem_write(s_p + 4, _dword(0))

        # base 1.0/2.0/4.0, child reports 10.0; then -1.5/0.25/8.0 and 4.0
        for name, vals in (('first', (1.0, 2.0, 4.0, 10.0)), ('second', (-1.5, 0.25, 8.0, 4.0))):
            f58, f5c, f74, get_value = vals
            v = get_value - f5c
            want_up = (f74 * 0.5 + f58, v + f5c)
            diffs = h.compare(VF, args=[s_arg1, s_arg2, s_ctx], regs={UC_X86_REG_ECX: s_this},
                              setup=lambda hh, vv=vals: setup(vv), ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(vals)
            res = h.call(VF, args=[s_arg1, s_arg2, s_ctx], regs={UC_X86_REG_ECX: s_this})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != s_this:
                return ['%s: returned %08X' % (name, res['eax'])]
            if res['esp'] != 16:
                return ['%s: stack delta %d, not 16' % (name, res['esp'])]
            tags = [_u32(h, log + L_TAGS + 4 * i) for i in range(_u32(h, log + L_SEQ))]
            if tags != [1, 2, 3, 4, 5, 6]:
                return ['%s: tag sequence %r' % (name, tags)]
            if (_u32(h, log + L_BASE) != s_this or _u32(h, log + L_BASE + 4) != s_arg1
                    or _u32(h, log + L_BASE + 8) != s_arg2):
                return ['%s: base got %08X %08X %08X' % ((name,) + tuple(
                    _u32(h, log + L_BASE + 4 * i) for i in range(3)))]
            if _u32(h, log + L_AC) != s_this or _u32(h, log + L_AC + 4) != s_arg1 + 0x74:
                return ['%s: 0x4AC380 got %08X %08X' % (name, _u32(h, log + L_AC),
                                                        _u32(h, log + L_AC + 4))]
            if _u32(h, log + L_FAC) != s_ctx:
                return ['%s: 0x587BF0 got ECX %08X' % (name, _u32(h, log + L_FAC))]
            if _u32(h, log + L_UPD) != s_ctx:
                return ['%s: update got %08X' % (name, _u32(h, log + L_UPD))]
            if _u32(h, log + L_GET) != s_p or _u32(h, log + L_SET) != s_p:
                return ['%s: child calls got %08X %08X' % (name, _u32(h, log + L_GET),
                                                           _u32(h, log + L_SET))]
            if _u32(h, log + L_SET + 4) != _f32u(want_up[0]) or _u32(h, log + L_SET + 8) != _f32u(want_up[1]):
                return ['%s: setter got %08X %08X, not %08X %08X'
                        % (name, _u32(h, log + L_SET + 4), _u32(h, log + L_SET + 8),
                           _f32u(want_up[0]), _f32u(want_up[1]))]
            if _u32(h, s_this) != VTB_STD or _u32(h, s_this + 0x214) != VTB_SUB:
                return ['%s: vtables %08X %08X' % (name, _u32(h, s_this), _u32(h, s_this + 0x214))]
            if _u32(h, s_this + 0x2b8) != s_p or _u32(h, s_this + 0x2c0) != s_ctx:
                return ['%s: members %08X %08X' % (name, _u32(h, s_this + 0x2b8),
                                                   _u32(h, s_this + 0x2c0))]
            if _u32(h, s_this + 0x2bc) != _f32u(v):
                return ['%s: +0x2BC %08X, not %08X' % (name, _u32(h, s_this + 0x2bc), _f32u(v))]
            if _u32(h, s_p + 4) != 1:
                return ['%s: child reference count %d' % (name, _u32(h, s_p + 4))]
            size = _u32(h, s_this + 0x238 + 0x14)
            res_cap = _u32(h, s_this + 0x238 + 0x18)
            ptr = _u32(h, s_this + 0x238 + 4) if res_cap >= 16 else s_this + 0x238 + 4
            if size != 19 or bytes(h.uc.mem_read(ptr, size)) != b'TroopIconDragDroper':
                return ['%s: name %r' % (name, bytes(h.uc.mem_read(ptr, size)))]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
