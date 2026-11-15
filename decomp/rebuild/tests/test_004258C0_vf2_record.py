"""sub_004258C0 (size 80, ECX thiscall, ret 0xC): slot 0x2C of the vtable of the object at +0x1C4, called with
(vtable in ECX, object, 0, 0x18, &local, 0), yields a 24-byte record whose local receives its address; the three
arguments land at record+0xC, +0x10 and +0x14, slot 0x30 (object) finishes and its result is returned.  A
negative result from slot 0x2C returns immediately without the stores.  Both slots are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x004258C0

LOG_BEGIN = 0x00
LOG_BEGIN_VT = 0x04
LOG_BEGIN_OBJ = 0x08
LOG_BEGIN_ZERO = 0x0C
LOG_BEGIN_SIZE = 0x10
LOG_BEGIN_ZERO2 = 0x18
LOG_END = 0x1C
LOG_END_OBJ = 0x20
LOG_BEGIN_RET = 0x28
LOG_END_RET = 0x2C
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


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def test_vf2_record(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        rec = h.alloc(0x18, bytes(0x18))
        begin = _stub(h, b'\xFF\x05' + _dword(log + LOG_BEGIN)                       # inc [begin]
                      + b'\x89\x0D' + _dword(log + LOG_BEGIN_VT)                     # mov [vt], ecx
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_BEGIN_OBJ)        # [esp+4] -> obj
                      + b'\x8B\x44\x24\x08\xA3' + _dword(log + LOG_BEGIN_ZERO)       # [esp+8] -> zero
                      + b'\x8B\x44\x24\x0C\xA3' + _dword(log + LOG_BEGIN_SIZE)       # [esp+C] -> size
                      + b'\x8B\x44\x24\x14\xA3' + _dword(log + LOG_BEGIN_ZERO2)      # [esp+14] -> zero2
                      + b'\x8B\x44\x24\x10'                                          # mov eax, [esp+10]
                      + b'\xC7\x00' + _dword(rec)                                    # mov [eax], rec
                      + b'\x8B\x05' + _dword(log + LOG_BEGIN_RET)                    # mov eax, [begin ret]
                      + b'\xC2\x14\x00')                                             # ret 14
        end = _stub(h, b'\xFF\x05' + _dword(log + LOG_END)                           # inc [end]
                    + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_END_OBJ)              # [esp+4] -> obj
                    + b'\x8B\x05' + _dword(log + LOG_END_RET)                        # mov eax, [end ret]
                    + b'\xC2\x04\x00')                                               # ret 4
        table = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(table + 0x2C, _dword(begin))
        h.uc.mem_write(table + 0x30, _dword(end))
        renderer = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(renderer, _dword(table))
        obj = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(obj + 0x1C4, _dword(renderer))
        for begin_ret, end_ret in ((7, 0x12345678), (0xFFFFFFFB, 0)):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(rec, bytes(0x18))
            h.uc.mem_write(log + LOG_BEGIN_RET, _dword(begin_ret))
            h.uc.mem_write(log + LOG_END_RET, _dword(end_ret))
            diffs = h.compare(VF, args=[0xA1, 0xB2, 0xC3], regs={UC_X86_REG_ECX: obj})
            if diffs:
                return ['begin %08X: %s' % (begin_ret, d) for d in diffs]
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(rec, bytes(0x18))
            h.uc.mem_write(log + LOG_BEGIN_RET, _dword(begin_ret))
            h.uc.mem_write(log + LOG_END_RET, _dword(end_ret))
            res = h.call(VF, args=[0xA1, 0xB2, 0xC3], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['begin %08X: replacement faulted: %s' % (begin_ret, res['fault'])]
            tag = 'begin %08X' % begin_ret
            if _u32(h, log + LOG_BEGIN) != 1:
                return ['%s: slot 2C called %d times' % (tag, _u32(h, log + LOG_BEGIN))]
            want = {LOG_BEGIN_VT: table, LOG_BEGIN_OBJ: renderer, LOG_BEGIN_ZERO: 0, LOG_BEGIN_SIZE: 0x18,
                    LOG_BEGIN_ZERO2: 0}
            for off, value in want.items():
                if _u32(h, log + off) != value:
                    return ['%s: begin arg at log+%02X is %08X, want %08X' % (tag, off, _u32(h, log + off), value)]
            if begin_ret & 0x80000000:
                if _u32(h, log + LOG_END) or any(_u32(h, rec + 4 * i) for i in range(6)):
                    return ['%s: the record was written anyway' % tag]
                if res['eax'] != begin_ret:
                    return ['%s: returned %08X' % (tag, res['eax'])]
                continue
            if _u32(h, log + LOG_END) != 1 or _u32(h, log + LOG_END_OBJ) != renderer:
                return ['%s: slot 30 called %d times on %08X' % (tag, _u32(h, log + LOG_END),
                                                                 _u32(h, log + LOG_END_OBJ))]
            got = [_u32(h, rec + 0xC), _u32(h, rec + 0x10), _u32(h, rec + 0x14)]
            if got != [0xA1, 0xB2, 0xC3]:
                return ['%s: record holds %r' % (tag, got)]
            if res['eax'] != end_ret:
                return ['%s: returned %08X, want %08X' % (tag, res['eax'], end_ret)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
