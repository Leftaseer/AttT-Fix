"""0x42E420 (deleting destructor), 0x42E3F0 (range copy), 0x42E740/0x42E760 (field getters) and 0x42E750
(_time64 with EAX); the destructor, operator delete and the _time64 import are stubbed."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

DTOR = 0x0042E420
PROJECTILE_DTOR = 0x0042E330
DELETE = 0x005E3E9C
RANGE_COPY = 0x0042E3F0
GET_40 = 0x0042E740
TIME64 = 0x0042E750
TIME64_SLOT = 0x006073EC               # __imp___time64
GET_70 = 0x0042E760

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, stub):
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    h.uc.ctl_remove_cache(target, target + 5)


def _log_ecx(offset):
    return b'\x89\x0D' + _dword(offset)


def test_deleting_dtor(h):
    """0x42E330 runs first; bit 0 of the flag frees the object; this is returned"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    dtor = _stub(h, _log_ecx(log) + b'\xC3')
    delete = _stub(h, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4) + b'\xC3')
    _hook(h, PROJECTILE_DTOR, dtor)
    _hook(h, DELETE, delete)
    try:
        problems = []
        for name, flag, freed in (('free', 1, True), ('keep', 0, False), ('keep, other bits', 0x100, False)):
            s = h.alloc(0x40, bytes(0x40))
            h.uc.mem_write(log, bytes(0x10))
            diffs = h.compare(DTOR, args=[flag], regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                problems.append('%s: %s' % (name, '; '.join(diffs)))
                continue
            res = h.call(DTOR, args=[flag], regs={UC_X86_REG_ECX: s})
            if _u32(h, log) != s:
                problems.append('%s: the destructor got %#x' % (name, _u32(h, log)))
            if freed and _u32(h, log + 4) != s:
                problems.append('%s: operator delete got %#x' % (name, _u32(h, log + 4)))
            if not freed and _u32(h, log + 4):
                problems.append('%s: the object was freed' % name)
            if res['eax'] != s:
                problems.append('%s: result %#x' % (name, res['eax']))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_range_copy(h):
    """dst is filled with *src count times and dst + count is returned"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for count in (0, 1, 5):
            dst = h.alloc(0x40, b'\xAA' * 0x40)
            src = h.alloc(0x40, bytes(range(0x40)))
            diffs = h.compare(RANGE_COPY, args=[dst, count, src], ret='eax')
            if diffs:
                problems.append('count %d: %s' % (count, '; '.join(diffs)))
                continue
            res = h.call(RANGE_COPY, args=[dst, count, src])
            if bytes(h.uc.mem_read(dst, 4 * count)) != _u32(h, src).to_bytes(4, 'little') * count:
                problems.append('count %d: the fill is %r' % (count, bytes(h.uc.mem_read(dst, 4 * count))))
            if bytes(h.uc.mem_read(dst + 4 * count, 4)) != b'\xAA' * 4:
                problems.append('count %d: it wrote past the end' % count)
            if res['eax'] != dst + 4 * count:
                problems.append('count %d: result %#x, want %#x' % (count, res['eax'], dst + 4 * count))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_getters(h):
    """+0x40 and +0x70 are returned"""
    heap0 = h.heap_ptr
    try:
        problems = []
        o = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(o + 0x40, _dword(0x40004000))
        h.uc.mem_write(o + 0x70, _dword(0x70007000))
        for addr, field in ((GET_40, 0x40), (GET_70, 0x70)):
            diffs = h.compare(addr, regs={UC_X86_REG_ECX: o}, ret='eax')
            if diffs:
                problems.append('+%#x: %s' % (field, '; '.join(diffs)))
                continue
            res = h.call(addr, regs={UC_X86_REG_ECX: o})
            if res['eax'] != _u32(h, o + field):
                problems.append('+%#x: result %#x' % (field, res['eax']))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_time64(h):
    """EAX is what _time64 receives; its 64-bit result is returned"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    code = b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)          # mov eax, [esp+4]; mov [log], eax
    code += b'\x85\xC0\x74\x0D'                                 # test eax,eax; jz skip
    code += b'\xC7\x00' + _dword(0x90ABCDEF)
    code += b'\xC7\x40\x04' + _dword(0x12345678)
    code += b'\xB8' + _dword(0x90ABCDEF) + b'\xBA' + _dword(0x12345678) + b'\xC3'
    stub = _stub(h, code)
    for slot in (TIME64_SLOT, h.symbols['__imp___time64']):    # the original table and the rebuilt one
        _patch(h, slot, _dword(stub))
    try:
        problems = []
        t = h.alloc(0x10, b'\xEE' * 0x10)
        h.uc.mem_write(log, bytes(0x10))
        diffs = h.compare(TIME64, regs={UC_X86_REG_EAX: t}, ret='eax:edx')
        if diffs:
            return ['time: %s' % '; '.join(diffs)]
        res = h.call(TIME64, regs={UC_X86_REG_EAX: t})
        if _u32(h, log) != t:
            problems.append('time: _time64 got %#x' % _u32(h, log))
        if res['eax'] != 0x90ABCDEF or res['edx'] != 0x12345678:
            problems.append('time: result %08x:%08x' % (res['edx'], res['eax']))
        if (_u32(h, t), _u32(h, t + 4)) != (0x90ABCDEF, 0x12345678):
            problems.append('time: the argument buffer is (%#x, %#x)' % (_u32(h, t), _u32(h, t + 4)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
