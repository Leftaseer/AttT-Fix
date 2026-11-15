"""sub_004212B0 (size 144, ECX + EAX inputs, ret 0, cdecl adapter): releases the object at +0x7C through the deleting
destructor in vtable slot 0 (flag 1) and clears the field, then destroys the entries of the +0x94 array (count +0x98)
and of the +0xA8 array (count +0xAC) from the last entry down the same way.  The EAX input comes back when nothing was
destroyed, otherwise the last destructor's result does."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

VF = 0x004212B0
L_CALLS = 0x00
L_ARGS = 0x08
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


def _negative_object(h, log):
    vtable = h.alloc(0x10, bytes(0x10))
    object = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(object, _dword(vtable))
    h.uc.mem_write(vtable, _dword(_stub(
        h,
        b'\xFF\x05' + _dword(log + L_CALLS)                                # inc [destructions]
        + b'\xA1' + _dword(log + L_CALLS)                                  # mov eax, [destructions]
        + b'\x48'                                                          # dec eax (call index)
        + b'\x89\x0C\xC5' + _dword(log + L_ARGS)                           # ecx -> this[index]
        + b'\x8B\x54\x24\x04'                                              # mov edx, [esp+4] (flag)
        + b'\x89\x14\xC5' + _dword(log + L_ARGS + 4)                       # edx -> flag[index]
        + b'\xB8' + _dword(0x11223344) + b'\xC2\x04\x00')))                # mov eax, result; ret 4
    return object


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def test_004212B0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        self = h.alloc(0x100, bytes(0x100))
        own = _negative_object(h, log)
        a = _negative_object(h, log)
        b = _negative_object(h, log)
        c = _negative_object(h, log)
        d = _negative_object(h, log)
        array1 = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(array1, _dword(a) + _dword(0) + _dword(b) + _dword(0))
        array2 = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(array2, _dword(c) + _dword(d))

        def setup(full):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(self, bytes(0x100))
            if full:
                h.uc.mem_write(self + 0x7c, _dword(own))
                h.uc.mem_write(self + 0x94, _dword(array1))
                h.uc.mem_write(self + 0x98, _dword(3))
                h.uc.mem_write(self + 0xa8, _dword(array2))
                h.uc.mem_write(self + 0xac, _dword(2))

        for name, full, eax in (('empty', False, 0xCAFEBABE), ('full', True, 0xCAFEBABE)):
            diffs = h.compare(VF, regs={UC_X86_REG_ECX: self, UC_X86_REG_EAX: eax},
                              setup=lambda hh, f=full: setup(f), ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(full)
            res = h.call(VF, regs={UC_X86_REG_ECX: self, UC_X86_REG_EAX: eax})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if not full:
                if _u32(h, log + L_CALLS) != 0:
                    return ['empty: the destructors ran']
                if res['eax'] != eax:
                    return ['empty: returned %08X, not the EAX input' % res['eax']]
                continue
            if res['eax'] != 0x11223344:
                return ['full: returned %08X' % res['eax']]
            want = [(own, 1), (b, 1), (a, 1), (d, 1), (c, 1)]
            if _u32(h, log + L_CALLS) != len(want):
                return ['full: the destructors ran %d times' % _u32(h, log + L_CALLS)]
            for i, (object, flag) in enumerate(want):
                got = (_u32(h, log + L_ARGS + 8 * i), _u32(h, log + L_ARGS + 8 * i + 4))
                if got != (object, flag):
                    return ['full: destruction %d was (%08X, %d)' % (i, got[0], got[1])]
            if _u32(h, self + 0x7c) != 0 or _u32(h, self + 0x98) != 0 or _u32(h, self + 0xac) != 0:
                return ['full: the field or the counts were left at %08X, %d, %d'
                        % (_u32(h, self + 0x7c), _u32(h, self + 0x98), _u32(h, self + 0xac))]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
