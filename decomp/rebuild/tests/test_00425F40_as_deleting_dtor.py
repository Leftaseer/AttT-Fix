"""0x00425F40 (ECX = the object, ret 4 = the flags byte): the ActionScript singleton's deleting destructor: the
vtable 0x00607ED0, operator delete 0x005E3E9C when the low bit of the flags is set.  Returns this."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425F40
DELETE = 0x005E3E9C
VTABLE = 0x00607ED0

L_COUNT = 0x00
L_DATA = 0x10
LOG_SIZE = 0x20

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


def test_00425F40(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, DELETE,
                     b'\xFF\x05' + _dword(log + L_COUNT)                        # inc [count]
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_DATA)          # the block -> log
                     + b'\xC3')
        obj = h.alloc(0x20, b'\xEE' * 0x20)

        for flags in (0, 1):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(obj, b'\xEE' * 0x20)

            setup()
            diffs = h.compare(THIS, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            setup()
            res = h.call(THIS, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['flags %d: returned %08X' % (flags, res['eax'])]
            if _u32(h, obj) != VTABLE:
                return ['flags %d: the vtable is %08X' % (flags, _u32(h, obj))]
            if _u32(h, log + L_COUNT) != (flags & 1) or _u32(h, log + L_DATA) != (obj if flags & 1 else 0):
                return ['flags %d: deletes %08X x%d' % (flags, _u32(h, log + L_DATA), _u32(h, log + L_COUNT))]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
