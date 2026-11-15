"""0x00425F60 (no arguments): the ActionScript singleton at 0x006C8EF8 is returned as is when it exists; otherwise the
Singleton.h error is raised: the message string at 0x00607EE8, the exception object (0x00421220 with file 0x00607ED4
and line 0x3D) and 0x005E3EC0 with the throw info at 0x0069916C.  The string constructor and the throw machinery
are stubs that log what they see."""
import struct

THIS = 0x00425F60
GLOBAL = 0x006C8EF8
EXC_CTOR = 0x00421220
THROW = 0x005E3EC0
STR_SLOT = 0x00607324

STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
MESSAGE = 0x00607EE8
FILE = 0x00607ED4
LINE = 0x3D
THROW_INFO = 0x0069916C

L_EXC = 0x00
L_EXC_FILE = 0x04
L_EXC_LINE = 0x08
L_THROW = 0x0C
L_THROW_INFO = 0x10
L_STR = 0x14
L_STR_ARG = 0x18
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


def _patch_thunk(h, address, code):
    target = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', target - (address + 5)))


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def test_00425F60(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, EXC_CTOR, b'\xFF\x05' + _dword(log + L_EXC)            # inc [exc]
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + L_EXC_FILE)  # file
                     + b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + L_EXC_LINE)  # line
                     + b'\x31\xC0' + b'\xC2\x0C\x00')                            # xor eax, eax; ret 12
        _patch_thunk(h, THROW, b'\xFF\x05' + _dword(log + L_THROW)             # inc [throw]
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + L_THROW_INFO)  # info
                     + b'\x31\xC0' + b'\xC2\x08\x00')                            # xor eax, eax; ret 8
        _patch_import(h, STR_SLOT, STR_SYM,
                      b'\xFF\x05' + _dword(log + L_STR)                        # inc [str]
                      + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + L_STR_ARG)  # literal
                      + b'\x8B\xC1'                                            # eax = ecx
                      + b'\xC2\x04\x00')                                       # ret 4
        existing = h.alloc(0x20, b'\x55' * 0x20)

        for before, returned in ((existing, existing), (0, 0)):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(GLOBAL, _dword(before))

            thrown = 0 if returned else 1
            setup()
            diffs = h.compare(THIS, ret='eax')
            if diffs:
                return ['before %08X: %s' % (before, d) for d in diffs]
            setup()
            res = h.call(THIS)
            if res['fault']:
                return ['before %08X: replacement faulted: %s' % (before, res['fault'])]
            if res['eax'] != returned:
                return ['before %08X: returned %08X, expected %08X' % (before, res['eax'], returned)]
            if _u32(h, GLOBAL) != returned:
                return ['before %08X: the singleton is %08X' % (before, _u32(h, GLOBAL))]
            if _u32(h, log + L_STR) != thrown:
                return ['before %08X: the message built %d times' % (before, _u32(h, log + L_STR))]
            if _u32(h, log + L_EXC) != thrown or _u32(h, log + L_THROW) != thrown:
                return ['before %08X: %d exceptions and %d throws'
                        % (before, _u32(h, log + L_EXC), _u32(h, log + L_THROW))]
            if thrown:
                if (_u32(h, log + L_STR_ARG) != MESSAGE or _u32(h, log + L_EXC_FILE) != FILE
                        or _u32(h, log + L_EXC_LINE) != LINE or _u32(h, log + L_THROW_INFO) != THROW_INFO):
                    return ['before %08X: threw with %08X %08X:%d %08X'
                            % (before, _u32(h, log + L_STR_ARG), _u32(h, log + L_EXC_FILE),
                               _u32(h, log + L_EXC_LINE), _u32(h, log + L_THROW_INFO))]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
