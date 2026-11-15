"""0x00425D20 (ECX = the new object, one name argument, ret 4): the constructor.  +4 clears, the vtable 0x00607E94 goes
 * to +0 and +8 receives the low byte of 0x0046F480's result for the name, looked up in the registry at 0x006C873C.
 * Returns this.  The lookup is a stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425D20
LOOKUP = 0x0046F480
REGISTRY = 0x006C873C
VTABLE = 0x00607E94

L_LOOKUP = 0x00
L_RESULT = 0x04
L_NAME = 0x08
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


def _patch_thunk(h, address, code):
    stub = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(stub, stub + len(code))
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def test_00425D20(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, LOOKUP,
                     b'\x89\x0D' + _dword(log + L_LOOKUP)                    # mov [log], ecx (registry)
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_NAME)        # name -> [log+8]
                     + b'\xA1' + _dword(log + L_RESULT)                      # eax = result
                     + b'\xC2\x04\x00')                                      # ret 4
        registry = h.alloc(0x40, bytes(0x40))
        name = h.alloc(0x20, b'Name\0' + bytes(0x1B))
        obj = h.alloc(0x20, b'\xEE' * 0x20)

        for result in (0, 0x5A, 0x1234):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + L_RESULT, _dword(result))
                h.uc.mem_write(REGISTRY, _dword(registry))
                h.uc.mem_write(obj, b'\xEE' * 0x20)

            setup()
            diffs = h.compare(THIS, args=[name], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['result %04X: %s' % (result, d) for d in diffs]
            setup()
            res = h.call(THIS, args=[name], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['result %04X: replacement faulted: %s' % (result, res['fault'])]
            if res['eax'] != obj:
                return ['result %04X: returned %08X, expected %08X' % (result, res['eax'], obj)]
            if _u32(h, obj) != VTABLE:
                return ['result %04X: the vtable is %08X' % (result, _u32(h, obj))]
            if _u32(h, obj + 4) != 0:
                return ['result %04X: +4 is %08X' % (result, _u32(h, obj + 4))]
            if h.uc.mem_read(obj + 8, 1) != bytes([result & 0xFF]):
                return ['result %04X: +8 is %02X' % (result, h.uc.mem_read(obj + 8, 1)[0])]
            if _u32(h, log + L_LOOKUP) != registry:
                return ['result %04X: looked up in %08X' % (result, _u32(h, log + L_LOOKUP))]
            if _u32(h, log + L_NAME) != name:
                return ['result %04X: looked up %08X' % (result, _u32(h, log + L_NAME))]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
