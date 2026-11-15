"""sub_004207C0 (size 112, ECX thiscall, ret 4): constructs the object in three steps logged by this test - the base
constructor 0x004DF7D0, the vtable at +0 (0x00607B30), and the texture from 0x00443D00(arg) handed to
0x004DF020(this, texture, 1) - then copies the texture's +0x1C and +0x20 fields to +0x54 and +0x58 and returns this."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x004207C0
BASE = 0x004DF7D0
FACTORY = 0x00443D00
METHOD = 0x004DF020
VTABLE = 0x00607B30

L_SEQ = 0x00
L_SLOT_BASE = 0x04
L_SLOT_FACTORY = 0x08
L_SLOT_METHOD = 0x0C
L_BASE_CALLS = 0x10
L_FACTORY_CALLS = 0x14
L_METHOD_CALLS = 0x18
L_BASE_THIS = 0x1C
L_FACTORY_ARG = 0x20
L_FACTORY_RESULT = 0x24
L_METHOD_THIS = 0x28
L_METHOD_ARG0 = 0x2C
L_METHOD_ARG1 = 0x30
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


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _stamp(log, slot):
    return (b'\xA1' + _dword(log + L_SEQ)                                   # mov eax, [sequence]
            + b'\xFF\x05' + _dword(log + L_SEQ)                             # inc [sequence]
            + b'\xA3' + _dword(log + slot))                                 # mov [slot], eax


def test_004207C0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, BASE,
                     _stamp(log, L_SLOT_BASE)
                     + b'\xFF\x05' + _dword(log + L_BASE_CALLS)              # inc [base calls]
                     + b'\x89\x0D' + _dword(log + L_BASE_THIS)               # ecx -> log
                     + b'\xC3')                                              # ret
        _patch_thunk(h, FACTORY,
                     _stamp(log, L_SLOT_FACTORY)
                     + b'\xFF\x05' + _dword(log + L_FACTORY_CALLS)           # inc [factory calls]
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_FACTORY_ARG) # [esp+4] -> log
                     + b'\xA1' + _dword(log + L_FACTORY_RESULT)              # mov eax, [result]
                     + b'\xC3')                                              # ret
        _patch_thunk(h, METHOD,
                     _stamp(log, L_SLOT_METHOD)
                     + b'\xFF\x05' + _dword(log + L_METHOD_CALLS)            # inc [method calls]
                     + b'\x89\x0D' + _dword(log + L_METHOD_THIS)             # ecx -> log
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_METHOD_ARG0) # [esp+4] -> log
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_METHOD_ARG1) # [esp+8] -> log
                     + b'\xC2\x08\x00')                                      # ret 8
        self = h.alloc(0x80, bytes(0x80))
        arg = h.alloc(0x20, bytes([0xCD] * 0x20))
        texture = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(texture + 0x1c, _dword(0xAAAA1111))
        h.uc.mem_write(texture + 0x20, _dword(0xBBBB2222))

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_FACTORY_RESULT, _dword(texture))
            h.uc.mem_write(self, bytes(0x80))

        diffs = h.compare(VF, args=[arg], regs={UC_X86_REG_ECX: self}, setup=lambda hh: setup(), ret='eax')
        if diffs:
            return diffs
        setup()
        res = h.call(VF, args=[arg], regs={UC_X86_REG_ECX: self})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != self:
            return ['returned %08X' % res['eax']]
        if tuple(_u32(h, log + L_SLOT_BASE + 4 * i) for i in range(3)) != (0, 1, 2):
            return ['the construction steps ran as %r'
                    % (_u32(h, log + L_SLOT_BASE), _u32(h, log + L_SLOT_FACTORY), _u32(h, log + L_SLOT_METHOD))]
        if _u32(h, log + L_BASE_CALLS) != 1 or _u32(h, log + L_BASE_THIS) != self:
            return ['the base ran %d times on %08X' % (_u32(h, log + L_BASE_CALLS), _u32(h, log + L_BASE_THIS))]
        if _u32(h, log + L_FACTORY_CALLS) != 1 or _u32(h, log + L_FACTORY_ARG) != arg:
            return ['the factory ran %d times on %08X'
                    % (_u32(h, log + L_FACTORY_CALLS), _u32(h, log + L_FACTORY_ARG))]
        if _u32(h, log + L_METHOD_CALLS) != 1 or _u32(h, log + L_METHOD_THIS) != self:
            return ['the method ran %d times on %08X' % (_u32(h, log + L_METHOD_CALLS), _u32(h, log + L_METHOD_THIS))]
        if _u32(h, log + L_METHOD_ARG0) != texture or _u32(h, log + L_METHOD_ARG1) != 1:
            return ['the method got (%08X, %08X)' % (_u32(h, log + L_METHOD_ARG0), _u32(h, log + L_METHOD_ARG1))]
        if _u32(h, self) != VTABLE:
            return ['the vtable is %08X' % _u32(h, self)]
        if _u32(h, self + 0x54) != 0xAAAA1111 or _u32(h, self + 0x58) != 0xBBBB2222:
            return ['the texture fields copied as (%08X, %08X)'
                    % (_u32(h, self + 0x54), _u32(h, self + 0x58))]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
