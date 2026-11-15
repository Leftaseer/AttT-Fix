"""0x00424E70 (no arguments): the the camera singleton at 0x006C8708 is returned as is when it exists;
otherwise 0x244 bytes are allocated (0x005E3EAE) and constructed (0x00435E70), and the result becomes the
singleton.  When the construction yields nothing the Singleton.h error is raised: the message string at
0x00607BC8, the exception object (0x00421220 with file 0x00607BAC and line 0x10) and 0x005E3EC0 with the throw
info at 0x0069916C.  The allocator, constructor and throw machinery are stubs that log what they see."""
import struct

THIS = 0x00424E70
GLOBAL = 0x006C8708
NEW = 0x005E3EAE
CTOR = 0x00435E70
EXC_CTOR = 0x00421220
THROW = 0x005E3EC0
STR_SLOT = 0x00607324

STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
MESSAGE = 0x00607BC8
FILE = 0x00607BAC
LINE = 0x10
THROW_INFO = 0x0069916C

N_NEW = 0x00
NEW_SIZE = 0x04
NEW_RESULT = 0x08
N_CTOR = 0x0C
CTOR_THIS = 0x10
CTOR_RESULT = 0x14
N_STR = 0x18
STR_ARG = 0x1C
N_EXC = 0x20
EXC_FILE = 0x24
EXC_LINE = 0x28
N_THROW = 0x2C
THROW_INFO_SEEN = 0x30
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


def _patch_thunk(h, address, code):
    target = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', target - (address + 5)))


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def test_00424E70(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, NEW, b'\xFF\x05' + _dword(log + N_NEW)                 # inc [new]
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + NEW_SIZE)  # size -> [new size]
                     + b'\xA1' + _dword(log + NEW_RESULT)                      # eax = [result]
                     + b'\xC3')
        _patch_thunk(h, CTOR, b'\xFF\x05' + _dword(log + N_CTOR)               # inc [ctor]
                     + b'\x89\x0D' + _dword(log + CTOR_THIS)                   # this -> [ctor this]
                     + b'\xA1' + _dword(log + CTOR_RESULT)                     # eax = [result]
                     + b'\xC3')
        _patch_thunk(h, EXC_CTOR, b'\xFF\x05' + _dword(log + N_EXC)            # inc [exc]
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + EXC_FILE)  # file -> [file]
                     + b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + EXC_LINE)  # line -> [line]
                     + b'\x31\xC0'                                             # xor eax, eax
                     + b'\xC2\x0C\x00')                                        # ret 12
        _patch_thunk(h, THROW, b'\xFF\x05' + _dword(log + N_THROW)             # inc [throw]
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + THROW_INFO_SEEN)  # info -> [info]
                     + b'\x31\xC0'                                             # xor eax, eax
                     + b'\xC2\x08\x00')                                        # ret 8
        _patch_import(h, STR_SLOT, STR_SYM,
                      b'\xFF\x05' + _dword(log + N_STR)                        # inc [str]
                      + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + STR_ARG)  # literal -> [str arg]
                      + b'\x8B\xC1'                                            # eax = ecx
                      + b'\xC2\x04\x00')                                       # ret 4
        existing = h.alloc(0x244, b'\x55' * 0x244)
        block = h.alloc(0x244, b'\x66' * 0x244)

        # name, singleton before, allocator result, constructor result, singleton after, returned
        cases = (
            ('existing', existing, 0, 0, existing, existing),
            ('create', 0, block, block, block, block),
            ('no-memory', 0, 0, 0, 0, 0),
            ('no-object', 0, block, 0, 0, 0),
        )
        for name, before, new_result, ctor_result, after, returned in cases:
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + NEW_RESULT, _dword(new_result))
                h.uc.mem_write(log + CTOR_RESULT, _dword(ctor_result))
                h.uc.mem_write(GLOBAL, _dword(before))

            allocated = 0 if before else 1
            constructed = 1 if not before and new_result else 0
            thrown = 0 if after else 1
            setup()
            diffs = h.compare(THIS, ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(THIS)
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != returned:
                return ['%s: returned %08X, expected %08X' % (name, res['eax'], returned)]
            if _u32(h, GLOBAL) != after:
                return ['%s: the singleton is %08X, expected %08X' % (name, _u32(h, GLOBAL), after)]
            if _u32(h, log + N_NEW) != allocated:
                return ['%s: allocated %d times' % (name, _u32(h, log + N_NEW))]
            if allocated and _u32(h, log + NEW_SIZE) != 0x244:
                return ['%s: allocated %d bytes' % (name, _u32(h, log + NEW_SIZE))]
            if _u32(h, log + N_CTOR) != constructed:
                return ['%s: constructed %d times' % (name, _u32(h, log + N_CTOR))]
            if constructed and _u32(h, log + CTOR_THIS) != block:
                return ['%s: constructor called on %08X' % (name, _u32(h, log + CTOR_THIS))]
            if _u32(h, log + N_STR) != thrown:
                return ['%s: the message built %d times' % (name, _u32(h, log + N_STR))]
            if _u32(h, log + N_EXC) != thrown or _u32(h, log + N_THROW) != thrown:
                return ['%s: %d exceptions and %d throws' % (name, _u32(h, log + N_EXC), _u32(h, log + N_THROW))]
            if thrown:
                if (_u32(h, log + STR_ARG) != MESSAGE or _u32(h, log + EXC_FILE) != FILE
                        or _u32(h, log + EXC_LINE) != LINE or _u32(h, log + THROW_INFO_SEEN) != THROW_INFO):
                    return ['%s: threw with %08X %08X:%d %08X'
                            % (name, _u32(h, log + STR_ARG), _u32(h, log + EXC_FILE),
                               _u32(h, log + EXC_LINE), _u32(h, log + THROW_INFO_SEEN))]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
