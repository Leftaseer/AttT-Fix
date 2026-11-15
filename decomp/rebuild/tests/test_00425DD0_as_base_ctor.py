"""0x00425DD0 (ECX = the object, ret 0): the ActionScript base's constructor.  +4 clears, the vtable 0x00607E94 goes
to +0, and the registry user count 0x006C8738 is taken; the first user makes the CInput singleton (0x004215D0) the
registry at 0x006C873C.  The byte at +8 clears.  Returns this."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425DD0
INPUT = 0x004215D0
VTABLE = 0x00607E94
REFCOUNT = 0x006C8738
REGISTRY = 0x006C873C

L_CALLS = 0x00
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


def test_00425DD0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, INPUT,
                     b'\xFF\x05' + _dword(log + L_CALLS)                         # inc [calls]
                     + b'\xB8' + _dword(0x5A5A5A5A)                              # eax = the singleton
                     + b'\xC3')
        obj = h.alloc(0x20, b'\xEE' * 0x20)

        for refcount in (0, 2):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(obj, b'\xEE' * 0x20)
                h.uc.mem_write(REFCOUNT, _dword(refcount))
                h.uc.mem_write(REGISTRY, _dword(0x0BADC0DE))

            setup()
            diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['refcount %d: %s' % (refcount, d) for d in diffs]
            setup()
            res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['refcount %d: replacement faulted: %s' % (refcount, res['fault'])]
            if res['eax'] != obj:
                return ['refcount %d: returned %08X' % (refcount, res['eax'])]
            if _u32(h, log + L_CALLS) != (1 if refcount == 0 else 0):
                return ['refcount %d: the input singleton was fetched %d times' % (refcount, _u32(h, log + L_CALLS))]
            if _u32(h, REFCOUNT) != refcount + 1:
                return ['refcount %d: the user count is %X' % (refcount, _u32(h, REFCOUNT))]
            want = 0x5A5A5A5A if refcount == 0 else 0x0BADC0DE
            if _u32(h, REGISTRY) != want:
                return ['refcount %d: the registry is %08X' % (refcount, _u32(h, REGISTRY))]
            if _u32(h, obj) != VTABLE:
                return ['refcount %d: the vtable is %08X' % (refcount, _u32(h, obj))]
            if _u32(h, obj + 4) != 0 or h.uc.mem_read(obj + 8, 1) != b'\x00':
                return ['refcount %d: +4/+8 are %08X/%02X' % (refcount, _u32(h, obj + 4),
                                                              h.uc.mem_read(obj + 8, 1)[0])]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
