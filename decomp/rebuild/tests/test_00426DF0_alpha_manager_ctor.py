"""0x00426DF0 (ECX): the alpha control manager constructor: the control base gets the 0x0060FA8B name, then the
0x0060819C vtable, the +0x58 part with its empty list at +0x5C, the pick position (+0x64) and table (+0x68) from
the two builders, a zero +0x70, and the +0x49 flag set."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

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


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    return stub


def test_00426DF0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        # the temporary string lives on the callee's stack: the two frames differ, so compare only with a stub
        # that keeps the address out of memory
        silent = _stub(h, b'\x89\x0D' + _dword(log) + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 8)
                       + b'\xC2\x08\x00')
        verbose = _stub(h, b'\x89\x0D' + _dword(log) + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4)
                        + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 8) + b'\xC2\x08\x00')
        _patch(h, 0x004AB9C0, b'\xE9' + struct.pack('<i', silent - 0x004AB9C5))
        _hook(h, 0x004C2F40, b'\xB8' + _dword(0x40010000) + b'\xC3')
        _hook(h, 0x004215D0, b'\xB8' + _dword(0x40020000) + b'\xC3')
        _hook(h, 0x00421680, b'\xB8' + _dword(0x40030000) + b'\xC3')
        obj = h.alloc(0x120, b'\xEE' * 0x120)
        name = bytes(h.uc.mem_read(0x0060FA8B, 64)).split(b'\0')[0]

        diffs = h.compare(0x00426DF0, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        _patch(h, 0x004AB9C0, b'\xE9' + struct.pack('<i', verbose - 0x004AB9C5))
        h.uc.mem_write(log, bytes(0x40))
        res = h.call(0x00426DF0, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if res['eax'] != obj:
            return ['returned %08X' % res['eax']]
        if _u32(h, obj) != 0x0060819C:
            return ['the vtable is %08X' % _u32(h, obj)]
        if (_u32(h, obj + 0x5c), _u32(h, obj + 0x60)) != (0x40010000, 0):
            return ['the list is %08X, the count %08X' % (_u32(h, obj + 0x5c), _u32(h, obj + 0x60))]
        if _u32(h, obj + 0x68) != 0x40020000 or _u32(h, obj + 0x64) != 0x40030000:
            return ['the table is %08X, the position %08X' % (_u32(h, obj + 0x68), _u32(h, obj + 0x64))]
        if h.uc.mem_read(obj + 0x70, 4) != b'\0\0\0\0':
            return ['+0x70 is %08X' % _u32(h, obj + 0x70)]
        if h.uc.mem_read(obj + 0x49, 1) != b'\x01' or _u32(h, obj + 0x6c) != 0:
            return ['the flag is %02X, the highlight %08X'
                    % (h.uc.mem_read(obj + 0x49, 1)[0], _u32(h, obj + 0x6c))]
        if _u32(h, log) != obj or _u32(h, log + 8) != 0:
            return ['the base ctor got ECX %08X and %08X' % (_u32(h, log), _u32(h, log + 8))]
        sp = _u32(h, log + 4)
        if not 0x30000000 <= sp < 0x30100000:
            return ['the name string is not on the stack: %08X' % sp]
        size = _u32(h, sp + 20)
        res_cap = _u32(h, sp + 24)
        ptr = sp + 4 if res_cap < 16 else _u32(h, sp + 4)
        got = bytes(h.uc.mem_read(ptr, size))
        if got != name:
            return ['the base ctor got the name %r, expected %r' % (got, name)]
        return None
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
