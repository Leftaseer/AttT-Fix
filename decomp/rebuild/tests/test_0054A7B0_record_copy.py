"""sub_0054A7B0 (size 48, ECX thiscall, ret 4): the function at +0xC is called on the context at +0x14 with a
12-byte local and this object; the callee fills and returns the record, which is copied to the output and the
output is returned.  The called function is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x0054A7B0

LOG_THIS = 0x00
LOG_OWNER = 0x04
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


def test_record_copy(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        getter = _stub(h, b'\x89\x0D' + _dword(log + LOG_THIS)                     # mov [this], ecx
                          + b'\x8B\x44\x24\x08\xA3' + _dword(log + LOG_OWNER)      # [esp+8] -> owner
                          + b'\x8B\x44\x24\x04'                                    # mov eax, [esp+4]
                          + b'\xC7\x00\xAA\x00\x00\x00'                            # mov [eax], AAh
                          + b'\xC7\x40\x04\xBB\x00\x00\x00'                        # mov [eax+4], BBh
                          + b'\xC7\x40\x08\xCC\x00\x00\x00'                        # mov [eax+8], CCh
                          + b'\x8B\x44\x24\x04'                                    # mov eax, [esp+4]
                          + b'\xC2\x08\x00')                                       # ret 8
        obj = h.alloc(0x40, bytes(0x40))
        context = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(obj + 0xC, _dword(getter))
        h.uc.mem_write(obj + 0x14, _dword(context))
        out = h.alloc(0x10, bytes(0x10))
        diffs = h.compare(FN, args=[out], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(FN, args=[out], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_THIS) != context or _u32(h, log + LOG_OWNER) != obj:
            return ['getter called on %08X with owner %08X' % (_u32(h, log + LOG_THIS), _u32(h, log + LOG_OWNER))]
        got = [_u32(h, out + 4 * i) for i in range(3)]
        if got != [0xAA, 0xBB, 0xCC]:
            return ['record copied is %r' % (got,)]
        if res['eax'] != out:
            return ['returned %08X, want %08X' % (res['eax'], out)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
