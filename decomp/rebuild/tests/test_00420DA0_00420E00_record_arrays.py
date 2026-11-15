"""sub_00420DA0 / sub_00420E00 (size 96, cdecl, one argument): the same record allocator as 0x00420D40 for records of
0x118 and 0x15C bytes - operator new (0x005E3EAE) for the count times the record size, and when the count would
overflow the size (0xFFFFFFFF / count below the record size) a message-less std::bad_alloc built by MSVCR80's
exception constructor (IAT 0x6073B4), given the vtable 0x00607B0C and thrown with 0x006990C4, instead of an
allocation."""
import struct

NEW = 0x005E3EAE
THROW = 0x005E3EC0
IAT_EXC = 0x006073B4

L_NEW = 0x00
L_SIZE = 0x04
L_CTOR = 0x08
L_CTOR_MSG = 0x0C
L_THROW = 0x10
L_VT = 0x14
L_MSG = 0x18
L_TI = 0x1C
LOG_SIZE = 0x30

EXC_SYM = '__imp_??0exception@std@@QAE@ABQBD@Z'
VTABLE = 0x00607B0C
THROW_INFO = 0x006990C4

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


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _check(h, vf, elem):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        mem = h.alloc(0x1000, bytes(0x1000))
        _patch_thunk(h, NEW,
                     b'\xFF\x05' + _dword(log + L_NEW)                        # inc [allocations]
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_SIZE)         # [esp+4] -> size
                     + b'\xB8' + _dword(mem)                                  # mov eax, mem
                     + b'\xC3')                                               # ret
        _patch_import(h, IAT_EXC, EXC_SYM,
                      b'\xFF\x05' + _dword(log + L_CTOR)                      # inc [exception builds]
                      + b'\xC7\x01' + _dword(0x11223344)                      # mov [ecx], 11223344
                      + b'\xC7\x41\x04' + _dword(0x55667788)                  # mov [ecx+4], 55667788
                      + b'\x8B\x44\x24\x04\x8B\x00\xA3' + _dword(log + L_CTOR_MSG)  # *[esp+4] -> message
                      + b'\xC2\x04\x00')                                      # ret 4
        _patch_thunk(h, THROW,
                     b'\xFF\x05' + _dword(log + L_THROW)                      # inc [throws]
                     + b'\x8B\x44\x24\x04'                                    # mov eax, [esp+4]
                     + b'\x8B\x10\x89\x15' + _dword(log + L_VT)               # [exception] -> vtable
                     + b'\x8B\x50\x04\x89\x15' + _dword(log + L_MSG)          # [exception+4] -> message
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_TI)           # [esp+8] -> throw info
                     + b'\x33\xC0\x89\x00')                                   # fault at address 0

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))

        for name, count in (('none', 0), ('one', 1), ('sixteen', 0x10)):
            setup()
            diffs = h.compare(vf, args=[count])
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(vf, args=[count])
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != mem:
                return ['%s: the allocation came back as %08X' % (name, res['eax'])]
            if _u32(h, log + L_NEW) != 1:
                return ['%s: operator new ran %d times' % (name, _u32(h, log + L_NEW))]
            if _u32(h, log + L_SIZE) != count * elem:
                return ['%s: operator new got %d bytes' % (name, _u32(h, log + L_SIZE))]
            if _u32(h, log + L_CTOR) or _u32(h, log + L_THROW):
                return ['%s: the overflow was thrown' % name]

        setup()
        res = h.call(vf, args=[0xFFFFFFFF // elem + 1])
        if not res['fault']:
            return ['the overflowing count did not throw']
        if _u32(h, log + L_NEW) != 0:
            return ['the overflowing count was allocated']
        if _u32(h, log + L_CTOR) != 1:
            return ['the exception was built %d times' % _u32(h, log + L_CTOR)]
        if _u32(h, log + L_CTOR_MSG) != 0:
            return ['the exception message is %08X' % _u32(h, log + L_CTOR_MSG)]
        if _u32(h, log + L_THROW) != 1:
            return ['the exception was thrown %d times' % _u32(h, log + L_THROW)]
        if _u32(h, log + L_VT) != VTABLE:
            return ['the thrown vtable is %08X' % _u32(h, log + L_VT)]
        if _u32(h, log + L_MSG) != 0x55667788:
            return ['the thrown message is %08X' % _u32(h, log + L_MSG)]
        if _u32(h, log + L_TI) != THROW_INFO:
            return ['the throw info is %08X' % _u32(h, log + L_TI)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None


def test_00420DA0(h):
    return _check(h, 0x00420DA0, 0x118)


def test_00420E00(h):
    return _check(h, 0x00420E00, 0x15C)
