"""Small helpers of an ambient-sound/manager class and its map templates:
0x00427330 / 0x00427340 (ECX): vtable 0x00608250 at +0 (0x427330 returns this).
0x00427350 (ECX): (end - begin) / 12, 0 when begin is null.
0x00427370 (ECX, ret 4): the 12-byte element at the index.
0x004273C0 (ECX, ret 4): deleting destructor (vtable 0x00608250, delete on bit 0); returns this.
0x004273E0 (cdecl): node + 0x31.  0x00427460: node + 0x30.  0x00427470: node + 4.
0x00427440 (ECX, ret 8): copies a dword and a byte; returns this.
0x00427480: 0x071C71C7.  0x004274D0: swaps two bytes."""
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


def test_00427330(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        diffs = h.compare(0x00427330, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        res = h.call(0x00427330, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, obj) != 0x00608250 or res['eax'] != obj:
            return ['vtable %08X, returned %08X' % (_u32(h, obj), res['eax'])]
        if bytes(h.uc.mem_read(obj + 4, 0x1c)) != b'\xEE' * 0x1c:
            return ['bytes past the vtable changed']
        return None
    finally:
        h.heap_ptr = heap0


def test_00427340(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        diffs = h.compare(0x00427340, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        res = h.call(0x00427340, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if _u32(h, obj) != 0x00608250:
            return ['the vtable is %08X' % _u32(h, obj)]
        return None
    finally:
        h.heap_ptr = heap0


def test_00427350(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, bytes(0x20))
        base = h.alloc(0x80, b'\xEE' * 0x80)
        for first, delta in ((0, 0), (base, 36), (base, 13), (base, -12), (base, 1)):
            def setup(first=first, delta=delta):
                h.uc.mem_write(obj + 4, _dword(first))
                h.uc.mem_write(obj + 8, _dword((first + delta) & 0xffffffff if first else 0))
            setup()
            diffs = h.compare(0x00427350, regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['%08X+%d: %s' % (first, delta, d) for d in diffs]
            setup()
            res = h.call(0x00427350, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%08X+%d: replacement faulted: %s' % (first, delta, res['fault'])]
            want = 0 if not first else int(delta / 12)
            if res['eax'] != want & 0xffffffff:
                return ['%08X+%d: returned %d' % (first, delta, res['eax'])]
        return None
    finally:
        h.heap_ptr = heap0


def test_00427370(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, bytes(0x20))
        base = h.alloc(0x80, b'\xEE' * 0x80)
        h.uc.mem_write(obj + 4, _dword(base))
        for index in (0, 1, 5, -1):
            diffs = h.compare(0x00427370, args=[index & 0xffffffff], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['index %d: %s' % (index, d) for d in diffs]
            res = h.call(0x00427370, args=[index & 0xffffffff], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['index %d: replacement faulted: %s' % (index, res['fault'])]
            if res['eax'] != (base + index * 0xc) & 0xffffffff:
                return ['index %d: returned %08X' % (index, res['eax'])]
        return None
    finally:
        h.heap_ptr = heap0


def test_004273C0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        _hook(h, 0x005E3E9C, b'\xFF\x05' + _dword(log) + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4) + b'\xC3')
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        for flags in (0, 1, 2, 3):
            def setup():
                h.uc.mem_write(log, bytes(0x20))
                h.uc.mem_write(obj, b'\xEE' * 0x20)
            setup()
            diffs = h.compare(0x004273C0, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            setup()
            res = h.call(0x004273C0, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj or _u32(h, obj) != 0x00608250:
                return ['flags %d: returned %08X, vtable %08X' % (flags, res['eax'], _u32(h, obj))]
            want = 1 if flags & 1 else 0
            if _u32(h, log) != want or (want and _u32(h, log + 4) != obj):
                return ['flags %d: the delete ran %d times for %08X' % (flags, _u32(h, log), _u32(h, log + 4))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_004273E0_00427460_00427470(h):
    node = h.alloc(0x80, b'\xEE' * 0x80)
    for entry, offset in ((0x004273E0, 0x31), (0x00427460, 0x30), (0x00427470, 4)):
        diffs = h.compare(entry, args=[node], ret='eax')
        if diffs:
            return ['%08X: %s' % (entry, d) for d in diffs]
        res = h.call(entry, args=[node])
        if res['fault']:
            return ['%08X: replacement faulted: %s' % (entry, res['fault'])]
        if res['eax'] != node + offset:
            return ['%08X: returned %08X' % (entry, res['eax'])]
    return None


def test_00427440(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        value = h.alloc(4, _dword(0x12345678))
        byte = h.alloc(4, b'\x9A\x00\x00\x00')
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        diffs = h.compare(0x00427440, args=[value, byte], regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        res = h.call(0x00427440, args=[value, byte], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if res['eax'] != obj:
            return ['returned %08X' % res['eax']]
        if _u32(h, obj) != 0x12345678 or bytes(h.uc.mem_read(obj + 4, 1)) != b'\x9A':
            return ['the pair is %08X %02X' % (_u32(h, obj), h.uc.mem_read(obj + 4, 1)[0])]
        if bytes(h.uc.mem_read(obj + 5, 0x1b)) != b'\xEE' * 0x1b:
            return ['bytes past the copy changed']
        return None
    finally:
        h.heap_ptr = heap0


def test_00427480(h):
    diffs = h.compare(0x00427480, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x00427480)
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if res['eax'] != 0x71c71c7:
        return ['returned %08X' % res['eax']]
    return None


def test_004274D0(h):
    heap0 = h.heap_ptr
    try:
        a = h.alloc(4, b'\x12\x00\x00\x00')
        b = h.alloc(4, b'\x34\x00\x00\x00')
        diffs = h.compare(0x004274D0, args=[a, b], ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(a, b'\x12')
        h.uc.mem_write(b, b'\x34')
        res = h.call(0x004274D0, args=[a, b])
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if bytes(h.uc.mem_read(a, 1)) != b'\x34' or bytes(h.uc.mem_read(b, 1)) != b'\x12':
            return ['the bytes are %02X and %02X' % (h.uc.mem_read(a, 1)[0], h.uc.mem_read(b, 1)[0])]
        return None
    finally:
        h.heap_ptr = heap0
