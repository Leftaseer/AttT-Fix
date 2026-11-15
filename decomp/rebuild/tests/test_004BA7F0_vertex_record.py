"""sub_004BA7F0 (size 92, ECX thiscall, ret 4): the vertex buffer looked up at +0xEC (0x004BA550) gets a record from
slot 0x2C of its vtable - the record slot's own address in ECX and as the fourth argument, a 0x2000-byte limit,
the object first - slot 0x30 then finishes it; before that the span (+0xDC..+0xE0, 32-byte entries) is appended as
far as whole entries go.  The finish slot's result is returned.  A null span start appends nothing."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x004BA7F0
LOOKUP = 0x004BA550

LOG_BEGIN = 0x00
LOG_BEGIN_ECX_DIFF = 0x04
LOG_BEGIN_OBJ = 0x08
LOG_BEGIN_Z1 = 0x0C
LOG_BEGIN_Z2 = 0x10
LOG_BEGIN_LIMIT = 0x18
LOG_BEGIN_RET = 0x1C
LOG_END = 0x20
LOG_END_OBJ = 0x24
LOG_END_RET = 0x28
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


def test_vertex_record(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        rec = h.alloc(0x60, bytes(0x60))
        src = h.alloc(0x60, bytes(bytearray((0x40 + i * 7) & 0xff for i in range(0x60))))
        begin = _stub(h, b'\xFF\x05' + _dword(log + LOG_BEGIN)                       # inc [begin]
                      + b'\x8B\x44\x24\x10\x29\xC8\xA3' + _dword(log + LOG_BEGIN_ECX_DIFF)  # [esp+10]-ecx -> diff
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_BEGIN_OBJ)        # [esp+4] -> obj
                      + b'\x8B\x44\x24\x08\xA3' + _dword(log + LOG_BEGIN_Z1)         # [esp+8] -> zero
                      + b'\x8B\x44\x24\x0C\xA3' + _dword(log + LOG_BEGIN_Z2)         # [esp+C] -> zero2
                      + b'\x8B\x44\x24\x14\xA3' + _dword(log + LOG_BEGIN_LIMIT)      # [esp+14] -> limit
                      + b'\x8B\x44\x24\x10'                                          # mov eax, [esp+10]
                      + b'\xC7\x00' + _dword(rec)                                    # mov [eax], rec
                      + b'\x8B\x05' + _dword(log + LOG_BEGIN_RET)                    # mov eax, [begin ret]
                      + b'\xC2\x14\x00')                                             # ret 14
        end = _stub(h, b'\xFF\x05' + _dword(log + LOG_END)                           # inc [end]
                    + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_END_OBJ)            # [esp+4] -> obj
                    + b'\x8B\x05' + _dword(log + LOG_END_RET)                        # mov eax, [end ret]
                    + b'\xC2\x04\x00')                                               # ret 4
        table = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(table + 0x2C, _dword(begin))
        h.uc.mem_write(table + 0x30, _dword(end))
        obj = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(obj, _dword(table))
        lookup = h.alloc(4, _dword(obj))
        lookup_stub = _stub(h, b'\xB8' + _dword(lookup) + b'\xC3')                   # mov eax, lookup; ret
        _patch(h, LOOKUP, b'\xE9' + struct.pack('<i', lookup_stub - (LOOKUP + 5)))
        span = h.alloc(0x10, bytes(0x10))
        this = h.alloc(0x200, bytes(0x200))
        for start, start_ret in ((src, 0x1234), (0, 0x87654321)):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(rec, bytes(0x60))
            h.uc.mem_write(span, _dword(0) + _dword(start) + _dword(src + 0x45) + _dword(0))
            h.uc.mem_write(log + LOG_BEGIN_RET, _dword(start_ret))
            h.uc.mem_write(log + LOG_END_RET, _dword(0x5A5A5A5A))
            diffs = h.compare(VF, args=[span], regs={UC_X86_REG_ECX: this})
            if diffs:
                return ['start %08X: %s' % (start, d) for d in diffs]
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(rec, bytes(0x60))
            h.uc.mem_write(span, _dword(0) + _dword(start) + _dword(src + 0x45) + _dword(0))
            h.uc.mem_write(log + LOG_BEGIN_RET, _dword(start_ret))
            h.uc.mem_write(log + LOG_END_RET, _dword(0x5A5A5A5A))
            res = h.call(VF, args=[span], regs={UC_X86_REG_ECX: this})
            if res['fault']:
                return ['start %08X: replacement faulted: %s' % (start, res['fault'])]
            tag = 'start %08X' % start
            if _u32(h, log + LOG_BEGIN) != 1 or _u32(h, log + LOG_END) != 1:
                return ['%s: slots 2C/30 called %d/%d times' % (tag, _u32(h, log + LOG_BEGIN),
                                                                _u32(h, log + LOG_END))]
            if _u32(h, log + LOG_BEGIN_ECX_DIFF) != 0:
                return ['%s: slot 2C ecx is %d past the out slot' % (tag, _u32(h, log + LOG_BEGIN_ECX_DIFF))]
            want = {LOG_BEGIN_OBJ: obj, LOG_BEGIN_Z1: 0, LOG_BEGIN_Z2: 0, LOG_BEGIN_LIMIT: 0x2000}
            for off, value in want.items():
                if _u32(h, log + off) != value:
                    return ['%s: begin arg at log+%02X is %08X, want %08X' % (tag, off, _u32(h, log + off), value)]
            if _u32(h, log + LOG_END_OBJ) != obj:
                return ['%s: slot 30 got object %08X' % (tag, _u32(h, log + LOG_END_OBJ))]
            copied = 0 if not start else 0x40
            if bytes(h.uc.mem_read(rec, copied)) != bytes(h.uc.mem_read(src, copied)):
                return ['%s: the record did not get the whole-entry span' % tag]
            if any(h.uc.mem_read(rec + copied, 0x60 - copied)):
                return ['%s: the record was written past the span' % tag]
            if res['eax'] != 0x5A5A5A5A:
                return ['%s: returned %08X' % (tag, res['eax'])]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
