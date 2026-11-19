"""0x004C1EB0 (cdecl, one stack argument): when the object at 0x6CA4AC exists the argument is returned unchanged;
when it is missing the "..." message (literal 0x611400 through the string constructor at import slot 0x607324) is
put into an exception object (0x00421220 with file 0x6113F0 and line 0x8BB) and thrown (0x005E3EC0, throw info
0x69916C).  Nothing in the image refers to this function.  The exception constructor and throw are stubs that log
what they see; the throw is replaced by a returning one for the comparison and the real one is exercised last.
The memory comparison is off because the log records the stack address of the message string, which by construction
differs between the two frames (a direct replay of both bodies shows every logged field equal otherwise)."""
import struct

THIS = 0x004C1EB0
GLOBAL = 0x006CA4AC
EXC_CTOR = 0x00421220
THROW = 0x005E3EC0
STR_SLOT = 0x00607324

STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
MESSAGE = 0x00611400
FILE = 0x006113F0
LINE = 0x8BB
THROW_INFO = 0x0069916C

N_STR = 0x00
STR_ARG = 0x04
N_EXC = 0x08
EXC_MSG = 0x0C
EXC_FILE = 0x10
EXC_LINE = 0x14
N_THROW = 0x18
THROW_INFO_SEEN = 0x1C
LOG_SIZE = 0x30

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


def test_004C1EB0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, EXC_CTOR, b'\xFF\x05' + _dword(log + N_EXC)            # inc [exc]
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + EXC_MSG)   # msg -> [msg]
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + EXC_FILE)  # file -> [file]
                     + b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + EXC_LINE)  # line -> [line]
                     + b'\x31\xC0'                                             # xor eax, eax
                     + b'\xC2\x0C\x00')                                        # ret 12
        _patch_thunk(h, THROW, b'\xFF\x05' + _dword(log + N_THROW)
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + THROW_INFO_SEEN)
                     + b'\x31\xC0'
                     + b'\xC2\x08\x00')
        _patch_import(h, STR_SLOT, STR_SYM,
                      b'\xFF\x05' + _dword(log + N_STR)                        # inc [str]
                      + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + STR_ARG)  # literal -> [str arg]
                      + b'\x8B\xC1'                                            # eax = ecx (the string)
                      + b'\xC6\x41\x04\x00'                                    # empty SSO string: data[0] = 0
                      + b'\xC7\x41\x14\x00\x00\x00\x00'                        # size = 0
                      + b'\xC7\x41\x18\x0F\x00\x00\x00'                        # capacity = 15
                      + b'\xC2\x04\x00')                                       # ret 4
        value = 0xDEADBEEF

        for label, singleton, thrown in (('live', 0x11223344, 0), ('missing', 0, 1)):
            def setup(glob=singleton):
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(GLOBAL, _dword(glob))

            setup()
            diffs = h.compare(THIS, args=[value], ret='eax', mem=False)
            if diffs:
                return ['%s: %s' % (label, d) for d in diffs]
            setup()
            res = h.call(THIS, args=[value])
            if res['fault']:
                return ['%s: replacement faulted: %s' % (label, res['fault'])]
            if res['eax'] != value:
                return ['%s: returned %08X, expected the argument %08X' % (label, res['eax'], value)]
            if res['esp'] != 4:
                return ['%s: stack delta %d, not 4' % (label, res['esp'])]
            if _u32(h, log + N_STR) != thrown or _u32(h, log + N_EXC) != thrown \
                    or _u32(h, log + N_THROW) != thrown:
                return ['%s: %d/%d/%d string/exc/throw calls'
                        % (label, _u32(h, log + N_STR), _u32(h, log + N_EXC), _u32(h, log + N_THROW))]
            if thrown:
                if (_u32(h, log + STR_ARG) != MESSAGE or _u32(h, log + EXC_FILE) != FILE
                        or _u32(h, log + EXC_LINE) != LINE or _u32(h, log + THROW_INFO_SEEN) != THROW_INFO):
                    return ['%s: threw with %08X %08X:%d %08X'
                            % (label, _u32(h, log + STR_ARG), _u32(h, log + EXC_FILE),
                               _u32(h, log + EXC_LINE), _u32(h, log + THROW_INFO_SEEN))]
                if _u32(h, log + EXC_MSG) == 0:
                    return ['%s: the exception got no message' % label]
        h.uc.mem_write(THROW, saved[THROW])
        h.uc.ctl_remove_cache(THROW, THROW + 6)

        # the real throw must end the run before anything after it
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(GLOBAL, b'\0\0\0\0')
        res = h.call(THIS, args=[value])
        if res['fault'] != 'threw':
            return ['throw: fault %r, not threw' % (res['fault'],)]
        if _u32(h, log + N_STR) != 1 or _u32(h, log + STR_ARG) != MESSAGE:
            return ['throw: the message was not built (%d)' % _u32(h, log + N_STR)]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
