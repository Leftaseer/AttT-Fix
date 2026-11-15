"""0x004263A0 (ECX = the new alpha button, ret 12 = three arguments): its constructor: the control base
0x00426A00 with the three arguments, then the vtable 0x00608078 at +0 and the 2D part's vtable 0x00607F8C at +0x54.
Returns this.  The base is a stub that logs what it sees."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004263A0
BASE_CTOR = 0x00426A00

VTABLE = 0x00608078
VTABLE_54 = 0x00607F8C

L_THIS = 0x00
L_A = 0x04
L_B = 0x08
L_C = 0x0C
LOG_SIZE = 0x10

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


def test_004263A0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, BASE_CTOR,
                     b'\x89\x0D' + _dword(log + L_THIS)                         # this -> log
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_A)
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_B)
                     + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_C)
                     + b'\xC2\x0C\x00')                                         # ret 12
        obj = h.alloc(0x80, b'\xEE' * 0x80)
        args = [0x0A0A0A0A, 0x0B0B0B0B, 0x0C0C0C0C]

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(obj, b'\xEE' * 0x80)

        setup()
        diffs = h.compare(THIS, args=args, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return [str(d) for d in diffs]
        setup()
        res = h.call(THIS, args=args, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if res['eax'] != obj:
            return ['returned %08X, expected %08X' % (res['eax'], obj)]
        if (_u32(h, log + L_THIS), _u32(h, log + L_A), _u32(h, log + L_B), _u32(h, log + L_C)) != \
                (obj, args[0], args[1], args[2]):
            return ['the base got %08X %08X %08X %08X' % (_u32(h, log + L_THIS), _u32(h, log + L_A),
                                                          _u32(h, log + L_B), _u32(h, log + L_C))]
        if _u32(h, obj) != VTABLE or _u32(h, obj + 0x54) != VTABLE_54:
            return ['vtables %08X/%08X' % (_u32(h, obj), _u32(h, obj + 0x54))]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
