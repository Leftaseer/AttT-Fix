"""sub_00420700 (size 160, ECX thiscall, ret 4): allocates 0x254 bytes with operator new (0x005E3EAE, cdecl) and,
when that succeeded, constructs the object with 0x004B0290, passing the floats at this+0, +4, +0x28, the argument,
this+0xC, the byte at this+8, 2, this+0x2C, 1.0f and two zeroes.  Returns the constructor's result, or null when the
allocation failed (the constructor is not called then)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00420700
NEW = 0x005E3EAE
CTOR = 0x004B0290

L_NEW_CALLS = 0x00
L_SIZE = 0x04
L_RESULT = 0x08
L_CTOR_CALLS = 0x0C
L_CTOR_THIS = 0x10
L_ARGS = 0x14
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


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _float_bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def test_00420700(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, NEW,
                     b'\xFF\x05' + _dword(log + L_NEW_CALLS)                 # inc [allocations]
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_SIZE)        # [esp+4] (size) -> log
                     + b'\xA1' + _dword(log + L_RESULT)                      # mov eax, [result]
                     + b'\xC3')                                              # ret
        code = b'\xFF\x05' + _dword(log + L_CTOR_CALLS)                     # inc [constructions]
        code += b'\x89\x0D' + _dword(log + L_CTOR_THIS)                     # ecx (object) -> log
        for i in range(11):
            code += b'\x8B\x44\x24' + bytes([4 + 4 * i])                    # mov eax, [esp+4+4i]
            code += b'\xA3' + _dword(log + L_ARGS + 4 * i)                  # -> arg slot
        code += b'\xB8' + _dword(0x11223344) + b'\xC2\x2C\x00'              # mov eax, result; ret 0x2C
        _patch_thunk(h, CTOR, code)
        self = h.alloc(0x80, bytes(0x80))
        src = h.alloc(0x20, bytes([0xAB] * 0x20))
        buffer = h.alloc(0x254, bytes(0x254))
        h.uc.mem_write(self, struct.pack('<f', 1.5) + struct.pack('<f', -2.25))
        h.uc.mem_write(self + 0x28, struct.pack('<f', 3.75))
        h.uc.mem_write(self + 8, b'\x83')
        want = (_float_bits(1.5), _float_bits(-2.25), _float_bits(3.75), src, self + 0xc, 0x83, 2,
                self + 0x2c, _float_bits(1.0), 0, 0)

        def setup(result):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_RESULT, _dword(result))

        for name, result in (('failed', 0), ('succeeded', buffer)):
            diffs = h.compare(VF, args=[src], regs={UC_X86_REG_ECX: self}, setup=lambda hh, r=result: setup(r),
                              ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(result)
            res = h.call(VF, args=[src], regs={UC_X86_REG_ECX: self})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if _u32(h, log + L_NEW_CALLS) != 1 or _u32(h, log + L_SIZE) != 0x254:
                return ['%s: allocated %d times, %d bytes' % (name, _u32(h, log + L_NEW_CALLS),
                                                              _u32(h, log + L_SIZE))]
            if result == 0:
                if res['eax'] != 0:
                    return ['failed: returned %08X' % res['eax']]
                if _u32(h, log + L_CTOR_CALLS) != 0:
                    return ['failed: constructed the object anyway']
                continue
            if res['eax'] != 0x11223344:
                return ['succeeded: returned %08X' % res['eax']]
            if _u32(h, log + L_CTOR_CALLS) != 1 or _u32(h, log + L_CTOR_THIS) != buffer:
                return ['succeeded: constructed %08X %d times'
                        % (_u32(h, log + L_CTOR_THIS), _u32(h, log + L_CTOR_CALLS))]
            got = tuple(_u32(h, log + L_ARGS + 4 * i) for i in range(11))
            if got != want:
                return ['succeeded: constructed with %r, not %r' % (got, want)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
