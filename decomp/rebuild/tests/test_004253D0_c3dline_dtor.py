"""0x004253D0 (ECX = C3DLine, ret 0): the destructor.  The vtable 0x00607DB4 goes to +0; the shared line effect's
reference count (0x006C8710) drops and reaching zero releases the effect object (0x006C870C through slot 0x6C).  A
non-null object at +0x1C4 is released through the second slot of its vtable (the vtable in ECX, the object on the
stack) and the field clears; the CRenderObject3D base destructor (0x004AD020) finishes.  All callees are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004253D0
BASE = 0x004AD020
REFCOUNT = 0x006C8710
EFFECT = 0x006C870C

L_COUNT = 0x00
L_EVENTS = 0x10
L_VTABLE = 0xA0
L_EFFECT = 0xA4
L_OBJECT = 0xA8
LOG_SIZE = 0xC0

EV_EFFECT = 1
EV_OBJECT = 2
EV_BASE = 3

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
    return stub


def _event_stub(log, code, value, tail=b'\xC3'):
    return (b'\xFF\x05' + _dword(log + L_COUNT)                          # inc [count]
            + b'\xA1' + _dword(log + L_COUNT)                            # mov eax, [count]
            + b'\x48'                                                    # dec eax (event index)
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)                   # lea edx, [eax*8 + events]
            + b'\xC7\x82' + _dword(0) + _dword(code)                     # mov dword [edx], code
            + value
            + tail)


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_004253D0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        effect_release = _stub(h, _event_stub(log, EV_EFFECT, b'\x89\x8A' + _dword(4)))
        object_release = _stub(h, _event_stub(log, EV_OBJECT, b'\x8B\x44\x24\x04\x89\x82' + _dword(4),
                                              b'\xC2\x04\x00'))
        _patch_thunk(h, BASE, _event_stub(log, EV_BASE, b'\x89\x8A' + _dword(4)))
        vtable = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(vtable + 0x6C, _dword(effect_release))
        obj_vtable = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(obj_vtable + 8, _dword(object_release))
        effect = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(effect, _dword(vtable))
        target = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(target, _dword(obj_vtable))
        obj = h.alloc(0x200, b'\xEE' * 0x200)

        # (name, reference count, object at +0x1C4, effect released, object released)
        cases = (
            ('count-2', 2, True, False, True),
            ('last', 1, True, True, True),
            ('no-object', 1, False, True, False),
            ('count-3', 3, False, False, False),
        )
        for name, refcount, has_object, effect_released, object_released in cases:
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(obj, b'\xEE' * 0x200)
                h.uc.mem_write(obj + 0x1c4, _dword(target if has_object else 0))
                h.uc.mem_write(REFCOUNT, _dword(refcount))
                h.uc.mem_write(EFFECT, _dword(effect))

            setup()
            diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            expected = []
            if effect_released:
                expected.append((EV_EFFECT, effect))
            if object_released:
                expected.append((EV_OBJECT, target))
            expected.append((EV_BASE, obj))
            got = _events(h, log)
            if got != expected:
                return ['%s: events %r, expected %r' % (name, got, expected)]
            if _u32(h, REFCOUNT) != refcount - 1:
                return ['%s: the count is %d' % (name, _u32(h, REFCOUNT))]
            if _u32(h, obj) != 0x00607DB4:
                return ['%s: the vtable is %08X' % (name, _u32(h, obj))]
            if _u32(h, obj + 0x1c4) != 0:
                return ['%s: +1C4 is %08X' % (name, _u32(h, obj + 0x1c4))]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
