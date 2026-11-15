"""sub_004220A0 (size 128, ECX thiscall, ret 0): the script table's destructor.  Its own vtable 0x00607CC4 goes in
first; a positive count at +8 is released through 0x00402270 with the object held at 0x008D122C, -10000 and the
count, and the field becomes -1; then the base vtable 0x00607CB8 and the base destructor 0x00422000 run, and its
result is returned."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EDX

VF = 0x004220A0
RELEASE = 0x00402270
BASE = 0x00422000
GLOBAL_SLOT = 0x008D122C

OWN_VTABLE = 0x00607CC4
BASE_VTABLE = 0x00607CB8

L_OBJ = 0x00       # the object the release got
L_CODE = 0x04      # the -10000
L_COUNT = 0x08     # the count the release got
L_VTABLE = 0x0C    # the vtable seen at release time
L_SELF = 0x10      # this (written by setup)
L_REL_CALLS = 0x14
L_BASE_CALLS = 0x18
L_BASE_SELF = 0x1C
L_BASE_VTABLE = 0x20
LOG_SIZE = 0x30

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    return h.alloc(len(code), code)


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _patch_callee(h, address, code):
    _patch_thunk(h, address, code)
    target = h.symbols.get('_sub_%08X' % address)
    if target is not None and target != address:
        _patch_thunk(h, target, code)


def _dword(addr):
    return struct.pack('<I', addr)


def _release_stub(log):
    return (b'\xFF\x05' + _dword(log + L_REL_CALLS)                        # inc [calls]
            + b'\x8B\x44\x24\x04'                                          # mov eax, [esp+4] (object)
            + b'\xA3' + _dword(log + L_OBJ)
            + b'\x8B\x44\x24\x08'                                          # mov eax, [esp+8] (-10000)
            + b'\xA3' + _dword(log + L_CODE)
            + b'\x8B\x44\x24\x0C'                                          # mov eax, [esp+12] (count)
            + b'\xA3' + _dword(log + L_COUNT)
            + b'\xA1' + _dword(log + L_SELF)                                # mov eax, [self]
            + b'\x8B\x10'                                                  # mov edx, [eax] (the vtable)
            + b'\x89\x15' + _dword(log + L_VTABLE)
            + b'\xC3')                                                     # ret


def _base_stub(log):
    return (b'\xFF\x05' + _dword(log + L_BASE_CALLS)                       # inc [calls]
            + b'\x89\x0D' + _dword(log + L_BASE_SELF)                      # mov [self], ecx
            + b'\x8B\x01'                                                  # mov eax, [ecx] (the vtable)
            + b'\xA3' + _dword(log + L_BASE_VTABLE)
            + b'\xB8' + _dword(0x11223344)                                 # mov eax, the result
            + b'\xC3')                                                     # ret


def test_004220A0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_callee(h, RELEASE, _release_stub(log))
        _patch_callee(h, BASE, _base_stub(log))
        obj = h.alloc(0x20, bytes(0x20))
        global_value = _u32(h, GLOBAL_SLOT)
        for count, want_release, want_count in ((0, False, 0), (5, True, 5), (-3, False, -3),
                                                (1, True, 1), (0x7FFFFFFF, True, 0x7FFFFFFF)):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + L_SELF, _dword(obj))
                h.uc.mem_write(obj, b'\x99' * 0x20)
                h.uc.mem_write(obj + 8, struct.pack('<i', count))
            diffs = h.compare(VF, regs={UC_X86_REG_ECX: obj}, setup=lambda hh: setup(), ret='eax')
            if diffs:
                return ['count %d: %s' % (count, d) for d in diffs]
            setup()
            res = h.call(VF, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['count %d: replacement faulted: %s' % (count, res['fault'])]
            if res['eax'] != 0x11223344:
                return ['count %d: returned %08X, not the base destructor\'s result' % (count, res['eax'])]
            if _u32(h, log + L_REL_CALLS) != (1 if want_release else 0):
                return ['count %d: released %d times' % (count, _u32(h, log + L_REL_CALLS))]
            if want_release:
                if _u32(h, log + L_OBJ) != global_value:
                    return ['count %d: released to %08X, not the object at %08X'
                            % (count, _u32(h, log + L_OBJ), global_value)]
                if struct.unpack('<i', h.uc.mem_read(log + L_CODE, 4))[0] != -10000:
                    return ['count %d: released with %d' % (count, struct.unpack('<i', h.uc.mem_read(log + L_CODE, 4))[0])]
                if _u32(h, log + L_COUNT) != want_count:
                    return ['count %d: released with count %d' % (count, _u32(h, log + L_COUNT))]
                if _u32(h, log + L_VTABLE) != OWN_VTABLE:
                    return ['count %d: the own vtable was not in place at release time' % count]
                if struct.unpack('<i', h.uc.mem_read(obj + 8, 4))[0] != -1:
                    return ['count %d: the count is %d after the release' % (count, struct.unpack('<i', h.uc.mem_read(obj + 8, 4))[0])]
            elif struct.unpack('<i', h.uc.mem_read(obj + 8, 4))[0] != want_count:
                return ['count %d: the count became %d without a release'
                        % (count, struct.unpack('<i', h.uc.mem_read(obj + 8, 4))[0])]
            if _u32(h, log + L_BASE_CALLS) != 1 or _u32(h, log + L_BASE_SELF) != obj:
                return ['count %d: the base destructor ran %d times on %08X'
                        % (count, _u32(h, log + L_BASE_CALLS), _u32(h, log + L_BASE_SELF))]
            if _u32(h, log + L_BASE_VTABLE) != BASE_VTABLE:
                return ['count %d: the base destructor saw vtable %08X' % (count, _u32(h, log + L_BASE_VTABLE))]
            if _u32(h, obj) != BASE_VTABLE:
                return ['count %d: the object ends with vtable %08X' % (count, _u32(h, obj))]
            if _u32(h, obj + 4) != 0x99999999 or _u32(h, obj + 0xc) != 0x99999999:
                return ['count %d: a field outside +0 and +8 changed' % count]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
