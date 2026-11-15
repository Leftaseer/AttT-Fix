"""sub_00420980 (size 160, ECX thiscall, ret 4): the base step 0x004B1B20(this, arg), then a local 0x224-byte checkers
object (0x0043A280 / 0x0043A320 / 0x0043A310) around this->+0x7C (0x00430350, 0x00430430) and the arg's virtual slot
+0x18; finally this->+0x74 goes to the setter 0x004AD530.  The test first runs the replacement with detail-logging
stubs to pin the order and the arguments, then compares against the original with stubs that only stamp the order
(the local's address legitimately differs between the two frames)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00420980
BASE = 0x004B1B20
CTOR = 0x0043A280
FIRST = 0x00430350
MID = 0x0043A320
DTOR = 0x0043A310
SECOND = 0x00430430
SETTER = 0x004AD530

L_SEQ = 0x00
L_STEP_BASE = 0x04
L_STEP_CTOR = 0x08
L_STEP_FIRST = 0x0C
L_STEP_VIRT = 0x10
L_STEP_MID = 0x14
L_STEP_SECOND = 0x18
L_STEP_SETTER = 0x1C
L_STEP_DTOR = 0x20
L_BASE_THIS = 0x24
L_BASE_ARG = 0x28
L_CTOR_THIS = 0x2C
L_FIRST_THIS = 0x30
L_VIRT_THIS = 0x34
L_MID_THIS = 0x38
L_SECOND_THIS = 0x3C
L_SETTER_THIS = 0x40
L_DTOR_THIS = 0x44
LOG_SIZE = 0x60

STEPS = (L_STEP_BASE, L_STEP_CTOR, L_STEP_FIRST, L_STEP_VIRT, L_STEP_MID, L_STEP_SECOND, L_STEP_SETTER, L_STEP_DTOR)

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


def _patch_callee(h, address, code):
    """the original body calls the entry; the rebuilt code may call the glue implementation directly"""
    _patch_thunk(h, address, code)
    target = h.symbols.get('_sub_%08X' % address)
    if target is not None and target != address:
        _patch_thunk(h, target, code)


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def _stamp(log, slot):
    return (b'\xA1' + _dword(log + L_SEQ)                                   # mov eax, [sequence]
            + b'\xFF\x05' + _dword(log + L_SEQ)                             # inc [sequence]
            + b'\xA3' + _dword(log + slot))                                 # mov [slot], eax


def _log_ecx(log, slot):
    return b'\x89\x0D' + _dword(log + slot)                                 # ecx -> log


def test_00420980(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        second_code = b'\xB8' + _dword(0x12345678) + b'\xC3'                 # mov eax, marker; ret
        # detailed stubs: order stamp, the arguments, and the callee's own cleanup
        _patch_callee(h, BASE,
                     _stamp(log, L_STEP_BASE) + _log_ecx(log, L_BASE_THIS)
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_BASE_ARG)     # [esp+4] (arg) -> log
                     + b'\xC2\x04\x00')                                      # ret 4
        _patch_callee(h, CTOR, _stamp(log, L_STEP_CTOR) + _log_ecx(log, L_CTOR_THIS) + b'\xC3')
        _patch_callee(h, FIRST, _stamp(log, L_STEP_FIRST) + _log_ecx(log, L_FIRST_THIS) + b'\xC3')
        _patch_callee(h, MID, _stamp(log, L_STEP_MID) + _log_ecx(log, L_MID_THIS) + b'\xC3')
        _patch_callee(h, DTOR, _stamp(log, L_STEP_DTOR) + _log_ecx(log, L_DTOR_THIS) + b'\xC3')
        _patch_callee(h, SECOND, _stamp(log, L_STEP_SECOND) + _log_ecx(log, L_SECOND_THIS) + second_code)
        _patch_callee(h, SETTER, _stamp(log, L_STEP_SETTER) + _log_ecx(log, L_SETTER_THIS) + b'\xC3')
        self = h.alloc(0x100, bytes(0x100))
        arg = h.alloc(0x20, bytes(0x20))
        vtable = h.alloc(0x40, bytes(0x40))
        first_object = h.alloc(0x10, bytes(0x10))
        setter_value = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(self + 0x7c, _dword(first_object))
        h.uc.mem_write(self + 0x74, _dword(setter_value))
        h.uc.mem_write(arg, _dword(vtable))

        virt_code = _stamp(log, L_STEP_VIRT) + _log_ecx(log, L_VIRT_THIS) + b'\xC3'
        h.uc.mem_write(vtable + 0x18, _dword(_stub(h, virt_code)))

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))

        setup()
        res = h.call(VF, args=[arg], regs={UC_X86_REG_ECX: self})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        steps = tuple(_u32(h, log + slot) for slot in STEPS)
        if steps != (0, 1, 2, 3, 4, 5, 6, 7):
            return ['the steps ran as %r' % (steps,)]
        if _u32(h, log + L_BASE_THIS) != self or _u32(h, log + L_BASE_ARG) != arg:
            return ['the base ran on (%08X, %08X)' % (_u32(h, log + L_BASE_THIS), _u32(h, log + L_BASE_ARG))]
        local = _u32(h, log + L_CTOR_THIS)
        if _u32(h, log + L_MID_THIS) != local or _u32(h, log + L_DTOR_THIS) != local:
            return ['the local went to %08X, %08X, %08X'
                    % (local, _u32(h, log + L_MID_THIS), _u32(h, log + L_DTOR_THIS))]
        if _u32(h, log + L_FIRST_THIS) != first_object or _u32(h, log + L_SECOND_THIS) != first_object:
            return ['the +0x7C field went to %08X, %08X'
                    % (_u32(h, log + L_FIRST_THIS), _u32(h, log + L_SECOND_THIS))]
        if _u32(h, log + L_VIRT_THIS) != arg:
            return ['the virtual ran on %08X' % _u32(h, log + L_VIRT_THIS)]
        if _u32(h, log + L_SETTER_THIS) != setter_value:
            return ['the setter got %08X' % _u32(h, log + L_SETTER_THIS)]

        # the comparison only needs the order: the local's address differs between the two frames
        _restore(h)
        _patch_callee(h, BASE, _stamp(log, L_STEP_BASE) + b'\xC2\x04\x00')
        _patch_callee(h, CTOR, _stamp(log, L_STEP_CTOR) + b'\xC3')
        _patch_callee(h, FIRST, _stamp(log, L_STEP_FIRST) + b'\xC3')
        _patch_callee(h, MID, _stamp(log, L_STEP_MID) + b'\xC3')
        _patch_callee(h, DTOR, _stamp(log, L_STEP_DTOR) + b'\xC3')
        _patch_callee(h, SECOND, _stamp(log, L_STEP_SECOND) + second_code)
        _patch_callee(h, SETTER, _stamp(log, L_STEP_SETTER) + b'\xC3')
        h.uc.mem_write(vtable + 0x18, _dword(_stub(h, _stamp(log, L_STEP_VIRT) + b'\xC3')))
        diffs = h.compare(VF, args=[arg], regs={UC_X86_REG_ECX: self}, setup=lambda hh: setup(), ret=None)
        if diffs:
            return diffs
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return None
