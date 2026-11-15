"""0x4205A0 (two-float store), 0x4205C0 (a call forwarded to a member's function pointer) and 0x4205E0 (the
std::bad_alloc constructor: the MSVC80 exception constructor is stubbed, its vtable must be overwritten)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

POINT_CTOR = 0x004205A0
THUNK = 0x004205C0
EXCEPTION_CTOR = 0x004205E0
BAD_ALLOC_VTABLE = 0x00607B0C
EXCEPTION_IMPORT = '__imp_??0exception@std@@QAE@ABQBD@Z'
EXCEPTION_SLOT = 0x006073B4

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


def test_point_ctor(h):
    """0x4205A0 stores the two float arguments at +0 and +4 and returns this"""
    heap0 = h.heap_ptr
    try:
        p = h.alloc(0x10, b'\xAA' * 0x10)
        x = struct.unpack('<I', struct.pack('<f', 1.5))[0]
        y = struct.unpack('<I', struct.pack('<f', -2.25))[0]
        diffs = h.compare(POINT_CTOR, args=(x, y), regs={UC_X86_REG_ECX: p}, ret='eax')
        if diffs:
            return ['; '.join(diffs)]
        res = h.call(POINT_CTOR, args=(x, y), regs={UC_X86_REG_ECX: p})
        if res['fault']:
            return [res['fault']]
        problems = []
        fx, fy = struct.unpack('<ff', h.uc.mem_read(p, 8))
        if (fx, fy) != (1.5, -2.25):
            problems.append('stored (%r, %r)' % (fx, fy))
        if res['eax'] != p:
            problems.append('returned %#x' % res['eax'])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_forward_thunk(h):
    """0x4205C0 jumps to [ [this+4] + 4 ] with ECX = this+4"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    target = _stub(h, b'\x89\x0D' + _dword(log) + b'\xC3')             # mov [log],ecx; ret
    try:
        problems = []
        obj = h.alloc(0x20, bytes(0x20))
        holder = h.alloc(0x20, bytes(0x20))
        h.uc.mem_write(obj + 4, _dword(holder))
        h.uc.mem_write(holder + 4, _dword(target))
        diffs = h.compare(THUNK, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return ['; '.join(diffs)]
        h.uc.mem_write(log, bytes(0x10))
        res = h.call(THUNK, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return [res['fault']]
        if _u32(h, log) != obj + 4:
            problems.append('the callee got %#x' % _u32(h, log))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_bad_alloc_ctor(h):
    """0x4205E0: the exception constructor gets this and the message pointer, the vtable is then 0x00607B0C"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    ctor = _stub(h, b'\x89\x0D' + _dword(log) +                       # mov [log],ecx
                    b'\x8B\x44\x24\x04' + b'\x8B\x00' +               # mov eax,[esp+4]; mov eax,[eax]
                    b'\xA3' + _dword(log + 4) +                       # mov [log+4],eax
                    b'\xC7\x01\xEF\xBE\xAD\xDE' +                     # mov dword [ecx],0xDEADBEEF
                    b'\xC2\x04\x00')                                  # ret 4
    _patch(h, EXCEPTION_SLOT, _dword(ctor))
    _patch(h, h.symbols[EXCEPTION_IMPORT], _dword(ctor))
    try:
        problems = []
        obj = h.alloc(0x20, b'\x33' * 0x20)
        msgptr = h.alloc(0x10, b'message\0' + bytes(8))
        diffs = h.compare(EXCEPTION_CTOR, args=(msgptr,), regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return ['; '.join(diffs)]
        h.uc.mem_write(log, bytes(0x10))
        res = h.call(EXCEPTION_CTOR, args=(msgptr,), regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return [res['fault']]
        if _u32(h, log) != obj:
            problems.append('the constructor got %#x' % _u32(h, log))
        if _u32(h, log + 4) != msgptr:
            problems.append('the message pointer is %#x' % _u32(h, log + 4))
        if _u32(h, obj) != h.to_rebuilt(BAD_ALLOC_VTABLE):
            problems.append('the vtable is %#x' % _u32(h, obj))
        if res['eax'] != obj:
            problems.append('returned %#x' % res['eax'])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
