"""0x00426070 (ECX = the ActionScript object, ret 0): its destructor.  The vtables 0x00607F0C and 0x00607F00, then
the action at +0x6C and the manager at +0x60 released: an intrusive count at +4, the drop to zero calling their
first vtable slot with 1.  Finally the vtable 0x00607ED0 at +0x58 and the CRenderObject base destructor 0x004AB940.
The releases and the base destructor are stubs that log their calls."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00426070
BASE_DTOR = 0x004AB940

L_COUNT = 0x00
L_EVENTS = 0x10
L_THIS = 0x90
L_ARG = 0x94
LOG_SIZE = 0xA0

EV_RELEASE = 1
EV_BASE = 2

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


def _event_head(log, code):
    return (b'\xFF\x05' + _dword(log + L_COUNT)
            + b'\xA1' + _dword(log + L_COUNT)
            + b'\x48'
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)
            + b'\xC7\x82' + _dword(0) + _dword(code))


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_00426070(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        release = _stub(h,
                        _event_head(log, EV_RELEASE)
                        + b'\x89\x8A' + _dword(4)                              # this -> value
                        + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_ARG)        # the flag
                        + b'\xC2\x04\x00')                                     # ret 4
        vtable = h.alloc(0x10, _dword(release) + _dword(0) + _dword(0) + _dword(0))
        _patch_thunk(h, BASE_DTOR,
                     _event_head(log, EV_BASE)
                     + b'\x89\x8A' + _dword(4)                              # this -> value
                     + b'\xC3')
        obj = h.alloc(0x80, b'\xEE' * 0x80)
        action = h.alloc(0x20, bytes(0x20))
        manager = h.alloc(0x20, bytes(0x20))

        def setup(action_count, manager_count, action_obj, manager_obj):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(obj, b'\xEE' * 0x80)
            h.uc.mem_write(obj + 0x6c, _dword(action_obj))
            h.uc.mem_write(obj + 0x60, _dword(manager_obj))
            h.uc.mem_write(action, _dword(vtable) + _dword(action_count) + bytes(0x18))
            h.uc.mem_write(manager, _dword(vtable) + _dword(manager_count) + bytes(0x18))

        for action_count, manager_count, action_obj, manager_obj in ((3, 1, action, manager),
                                                                    (5, 0, action, 0)):
            expected = []
            if action_count == 1:
                expected.append((EV_RELEASE, action))
            if manager_count == 1:
                expected.append((EV_RELEASE, manager))
            expected.append((EV_BASE, obj))
            setup(action_count, manager_count, action_obj, manager_obj)
            diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['%d/%d: %s' % (action_count, manager_count, d) for d in diffs]
            setup(action_count, manager_count, action_obj, manager_obj)
            res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%d/%d: replacement faulted: %s' % (action_count, manager_count, res['fault'])]
            got = _events(h, log)
            if got != expected:
                return ['%d/%d: events %r, expected %r' % (action_count, manager_count, got, expected)]
            if _u32(h, obj) != 0x00607F0C or _u32(h, obj + 0x58) != 0x00607ED0:
                return ['%d/%d: vtables %08X/%08X' % (action_count, manager_count,
                                                       _u32(h, obj), _u32(h, obj + 0x58))]
            if action_obj and _u32(h, action + 4) != action_count - 1:
                return ['%d/%d: the action count is %d' % (action_count, manager_count, _u32(h, action + 4))]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
