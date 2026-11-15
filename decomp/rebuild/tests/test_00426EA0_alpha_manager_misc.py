"""Misc alpha manager members:
0x00426EA0 (ECX, ret 4): the deleting destructor (0x00426D50, then the delete if flag bit 0); returns this.
0x00426EC0 (ECX, ret 4): allocates the node with (head, head->prev, argument), appends it, tells the +0x58 part and
fixes the links.
0x00426F00 (ECX): the dword at +0x1C.
0x00426F10 (ECX, ret 12): the +8 virtual gets (&arg3, arg2, arg3); its result's target is stored through arg1."""
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


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def test_00426EA0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        _hook(h, 0x00426D50, b'\x89\x0D' + _dword(log) + b'\xFF\x05' + _dword(log + 4) + b'\xC3')
        _hook(h, 0x005E3E9C, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 8)
              + b'\xFF\x05' + _dword(log + 0xc) + b'\xC3')
        obj = h.alloc(0x120, b'\xEE' * 0x120)
        for flags in (0, 1, 2, 3):
            h.uc.mem_write(log, bytes(0x40))
            diffs = h.compare(0x00426EA0, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            h.uc.mem_write(log, bytes(0x40))
            res = h.call(0x00426EA0, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['flags %d: returned %08X' % (flags, res['eax'])]
            if _u32(h, log + 4) != 1 or _u32(h, log) != obj:
                return ['flags %d: the destructor got %08X' % (flags, _u32(h, log))]
            want = 1 if flags & 1 else 0
            if _u32(h, log + 0xc) != want:
                return ['flags %d: delete ran %d times' % (flags, _u32(h, log + 0xc))]
            if want and _u32(h, log + 8) != obj:
                return ['flags %d: delete got %08X' % (flags, _u32(h, log + 8))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00426EC0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        node = h.alloc(12, bytes(12))
        _hook(h, 0x005AD6C0, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)
              + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4)
              + b'\x8B\x44\x24\x0c' + b'\x8B\x00' + b'\xA3' + _dword(log + 8)
              + b'\xB8' + _dword(node) + b'\xC2\x0c\x00')
        _hook(h, 0x004E0EF0, b'\x89\x0D' + _dword(log + 0x10) + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 0x14)
              + b'\xC2\x04\x00')
        head = h.alloc(12, bytes(12))
        oldlast = h.alloc(12, bytes(12))
        obj = h.alloc(0x120, b'\xEE' * 0x120)

        def setup():
            h.uc.mem_write(log, bytes(0x40))
            h.uc.mem_write(obj, b'\xEE' * 0x120)
            h.uc.mem_write(obj + 0x5c, _dword(head))
            h.uc.mem_write(head, _dword(head) + _dword(oldlast) + bytes(4))
            h.uc.mem_write(oldlast, _dword(head) + _dword(head) + bytes(4))
            h.uc.mem_write(node, bytes(4) + _dword(oldlast) + bytes(4))

        setup()
        diffs = h.compare(0x00426EC0, args=[0x12345678], regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        setup()
        res = h.call(0x00426EC0, args=[0x12345678], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, log) != head or _u32(h, log + 4) != oldlast or _u32(h, log + 8) != 0x12345678:
            return ['the node allocation got (%08X, %08X, %08X)'
                    % (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8))]
        if _u32(h, log + 0x10) != obj + 0x58 or _u32(h, log + 0x14) != 1:
            return ['the +0x58 part got (%08X, %08X)' % (_u32(h, log + 0x10), _u32(h, log + 0x14))]
        if _u32(h, head + 4) != node:
            return ['head->prev is %08X' % _u32(h, head + 4)]
        if _u32(h, oldlast) != node:
            return ['the old last node next is %08X' % _u32(h, oldlast)]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_00426F00(h):
    obj = h.alloc(0x40, b'\xEE' * 0x40)
    h.uc.mem_write(obj + 0x1c, _dword(0x0BADF00D))
    diffs = h.compare(0x00426F00, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00426F00, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if res['eax'] != 0x0BADF00D:
        return ['returned %08X' % res['eax']]
    return None


def test_00426F10(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        result = h.alloc(4, _dword(0xAABBCCDD))
        call = _stub(h, b'\x89\x0D' + _dword(log)
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4)
                     + b'\x8B\x44\x24\x0c' + b'\xA3' + _dword(log + 8)
                     + b'\x8B\x44\x24\x04' + b'\x8B\x00' + b'\xA3' + _dword(log + 0xc)
                     + b'\xB8' + _dword(result) + b'\xC2\x0c\x00')
        obj = h.alloc(0x10, bytes(8) + _dword(call))
        out = h.alloc(4, b'\xEE\xEE\xEE\xEE')
        diffs = h.compare(0x00426F10, args=[out, 0x11112222, 0x33334444], regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x40))
        h.uc.mem_write(out, b'\xEE\xEE\xEE\xEE')
        res = h.call(0x00426F10, args=[out, 0x11112222, 0x33334444], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, out) != 0xAABBCCDD:
            return ['the output is %08X' % _u32(h, out)]
        if _u32(h, log) != obj:
            return ['the +8 virtual got %08X' % _u32(h, log)]
        if _u32(h, log + 4) != 0x11112222 or _u32(h, log + 8) != 0x33334444:
            return ['the +8 virtual got (%08X, %08X)' % (_u32(h, log + 4), _u32(h, log + 8))]
        if _u32(h, log + 0xc) != 0x33334444:
            return ['the first argument points at %08X' % _u32(h, log + 0xc)]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0
