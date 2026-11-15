"""0x00425D80 (ECX = the object, ret 0): the ActionScript base's destructor part.  The vtable 0x00607E94 goes to
 *0, the registry user count 0x006C8738 drops by one and the CGameObject destructor 0x00424C70 runs (a tail call
in the original).  The destructor is a stub that logs ECX."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425D80
BASE_DTOR = 0x00424C70
VTABLE = 0x00607E94
REFCOUNT = 0x006C8738

L_COUNT = 0x00
L_EVENTS = 0x10
L_THIS = 0x90
LOG_SIZE = 0xA0

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


def test_00425D80(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, BASE_DTOR,
                     b'\xFF\x05' + _dword(log + L_COUNT)                        # inc [count]
                     + b'\x89\x0D' + _dword(log + L_THIS)                       # this -> log
                     + b'\xC3')
        obj = h.alloc(0x20, b'\xEE' * 0x20)

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(obj, b'\xEE' * 0x20)
            h.uc.mem_write(REFCOUNT, _dword(0x10))

        setup()
        diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return [str(d) for d in diffs]
        setup()
        res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, log + L_COUNT) != 1 or _u32(h, log + L_THIS) != obj:
            return ['base destructor log %08X x%d' % (_u32(h, log + L_THIS), _u32(h, log + L_COUNT))]
        if _u32(h, obj) != VTABLE:
            return ['the vtable is %08X' % _u32(h, obj)]
        if _u32(h, REFCOUNT) != 0x0F:
            return ['the user count is %X' % _u32(h, REFCOUNT)]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
