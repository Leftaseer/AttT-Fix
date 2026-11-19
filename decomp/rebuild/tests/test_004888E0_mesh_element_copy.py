"""0x004888E0 (ECX = the owning object, one stack argument -- the element container, ret 4): when twice the
element count (0x00427350 on begin/end at +4/+8) less two is not the value at +0x1C8, an assertion string
(0x0060F900, file 0x0060F8EC, line 0x5B) is built and thrown (0x00421220 / 0x005E3EC0 with 0x0069916C).
The object at +0x1CC is locked through table slot 0x2C (offset 0, size 0, no flags) and unlocked through slot
0x30.  With more than one element each step writes element i at the running pointer and element i+1 at pointer
+ 0x10, then advances the pointer by 0x20; the count is queried again after every step.  The lock and unlock
stubs record their arguments and hand back a fixed destination buffer; the throw parts are stubs as well, so
the assertion case continues into the copy like the original does when the throw returns."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004888E0
LOCK_SLOT = 0x2C
UNLOCK_SLOT = 0x30
EXC_CTOR = 0x00421220
THROW = 0x005E3EC0
STR_SLOT = 0x00607324
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
MESSAGE = 0x0060F900
FILE = 0x0060F8EC
LINE = 0x5B
THROW_INFO = 0x0069916C

N_LOCK = 0x00
LOCK_THIS = 0x04
LOCK_OFFSET = 0x08
LOCK_SIZE = 0x0C
LOCK_FLAGS = 0x10
N_UNLOCK = 0x14
UNLOCK_THIS = 0x18
N_STR = 0x1C
STR_ARG = 0x20
STR_THIS = 0x44
N_EXC = 0x24
EXC_MSG = 0x28
EXC_FILE = 0x2C
EXC_LINE = 0x30
N_THROW = 0x34
THROW_OBJ = 0x38
THROW_INFO_SEEN = 0x3C
ORDER = 0x40
LOG_SIZE = 0x50

DELTA = 8

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


def _param_store(offset, slot):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(slot)


def test_004888E0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        dest = h.alloc(0x100, b'\xEE' * 0x100)
        lock = _stub(h, b'\xFF\x05' + _dword(log + N_LOCK)                       # inc lock count
                     + _param_store(0x04, log + LOCK_THIS)
                     + _param_store(0x08, log + LOCK_OFFSET)
                     + _param_store(0x0C, log + LOCK_SIZE)
                     + _param_store(0x14, log + LOCK_FLAGS)
                     + b'\xC7\x05' + _dword(log + ORDER) + _dword(1)             # lock happens first
                     + b'\xB8' + _dword(dest)                                    # eax = destination
                     + b'\x8B\x54\x24\x10'                                       # edx = out slot
                     + b'\x89\x02'                                               # *out = dest
                     + b'\xC2\x14\x00')                                          # ret 20
        unlock = _stub(h, b'\xFF\x05' + _dword(log + N_UNLOCK)
                       + _param_store(0x04, log + UNLOCK_THIS)
                       + b'\xC7\x05' + _dword(log + ORDER) + _dword(2)           # unlock happens last
                       + b'\xC2\x04\x00')                                        # ret 4
        _patch(h, EXC_CTOR, b'\xFF\x05' + _dword(log + N_EXC)
               + _param_store(0x04, log + EXC_MSG)
               + _param_store(0x08, log + EXC_FILE)
               + _param_store(0x0C, log + EXC_LINE)
               + b'\x31\xC0'
               + b'\xC2\x0C\x00')
        _patch(h, THROW, b'\xFF\x05' + _dword(log + N_THROW)
               + _param_store(0x04, log + THROW_OBJ)
               + _param_store(0x08, log + THROW_INFO_SEEN)
               + b'\xC2\x08\x00')
        _patch_import(h, STR_SLOT, STR_SYM,
                      b'\xFF\x05' + _dword(log + N_STR)
                      + b'\x89\x0D' + _dword(log + STR_THIS)                     # ecx = the string
                      + _param_store(0x04, log + STR_ARG)
                      + b'\x8B\xC1'                                              # eax = the string
                      + b'\xC6\x41\x04\x00'                                      # empty SSO string
                      + b'\xC7\x41\x14\x00\x00\x00\x00'
                      + b'\xC7\x41\x18\x0F\x00\x00\x00'
                      + b'\xC2\x04\x00')
        vt = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(vt + LOCK_SLOT, _dword(lock))
        h.uc.mem_write(vt + UNLOCK_SLOT, _dword(unlock))
        mesh = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(mesh, _dword(vt))
        self = h.alloc(0x300, bytes(0x300))
        heap_base = h.heap_ptr

        for label, count, expected in (('five', 5, 8), ('one', 1, 0), ('assert', 5, 4)):
            pattern = bytes(range(count * 0xc))
            source = h.alloc(count * 0xc + 0x10, bytes(count * 0xc + 0x10))
            h.uc.mem_write(source, pattern)
            container = h.alloc(0x10, bytes(0x10))
            h.uc.mem_write(container + 4, _dword(source))
            h.uc.mem_write(container + 8, _dword(source + count * 0xc))
            log0 = bytes(LOG_SIZE)

            def setup():
                h.uc.mem_write(log, log0)
                h.uc.mem_write(dest, b'\xEE' * 0x100)
                h.uc.mem_write(self, b'\xA5' * 0x300)
                h.uc.mem_write(self + 0x1C8, _dword(expected))
                h.uc.mem_write(self + 0x1CC, _dword(mesh))

            setup()
            diffs = h.compare(THIS, args=[container], regs={UC_X86_REG_ECX: self}, ret=None, mem=False)
            if diffs:
                return ['%s: %s' % (label, d) for d in diffs]
            setup()
            res = h.call(THIS, args=[container], regs={UC_X86_REG_ECX: self})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (label, res['fault'])]
            if res['esp'] != DELTA:
                return ['%s: stack delta %d, not %d' % (label, res['esp'], DELTA)]
            if _u32(h, log + N_LOCK) != 1 or _u32(h, log + LOCK_THIS) != mesh \
                    or _u32(h, log + LOCK_OFFSET) != 0 or _u32(h, log + LOCK_SIZE) != 0 \
                    or _u32(h, log + LOCK_FLAGS) != 0:
                return ['%s: lock %d on %08X (%d, %d, flags %d)'
                        % (label, _u32(h, log + N_LOCK), _u32(h, log + LOCK_THIS),
                           _u32(h, log + LOCK_OFFSET), _u32(h, log + LOCK_SIZE), _u32(h, log + LOCK_FLAGS))]
            if _u32(h, log + N_UNLOCK) != 1 or _u32(h, log + UNLOCK_THIS) != mesh:
                return ['%s: unlock %d on %08X' % (label, _u32(h, log + N_UNLOCK), _u32(h, log + UNLOCK_THIS))]
            if _u32(h, log + ORDER) != 2:
                return ['%s: call order marker %d' % (label, _u32(h, log + ORDER))]
            assert_happened = expected != 2 * count - 2
            if _u32(h, log + N_STR) != assert_happened or _u32(h, log + N_EXC) != assert_happened \
                    or _u32(h, log + N_THROW) != assert_happened:
                return ['%s: string/exception/throw calls %d/%d/%d'
                        % (label, _u32(h, log + N_STR), _u32(h, log + N_EXC), _u32(h, log + N_THROW))]
            if assert_happened:
                if _u32(h, log + STR_ARG) != MESSAGE or _u32(h, log + EXC_FILE) != FILE \
                        or _u32(h, log + EXC_LINE) != LINE or _u32(h, log + THROW_INFO_SEEN) != THROW_INFO:
                    return ['%s: threw %08X %08X:%d %08X'
                            % (label, _u32(h, log + STR_ARG), _u32(h, log + EXC_FILE),
                               _u32(h, log + EXC_LINE), _u32(h, log + THROW_INFO_SEEN))]
                if _u32(h, log + EXC_MSG) != _u32(h, log + STR_THIS):
                    return ['%s: exception message %08X, string at %08X'
                            % (label, _u32(h, log + EXC_MSG), _u32(h, log + STR_THIS))]
            want = bytearray(b'\xEE' * 0x100)
            if count != 1:
                for i in range(count - 1):
                    want[0x20 * i:0x20 * i + 0xc] = pattern[i * 0xc:i * 0xc + 0xc]
                    want[0x20 * i + 0x10:0x20 * i + 0x1c] = pattern[(i + 1) * 0xc:(i + 1) * 0xc + 0xc]
            got = bytes(h.uc.mem_read(dest, 0x100))
            if got != bytes(want):
                return ['%s: destination %s, expected %s' % (label, got[:0x50].hex(), bytes(want)[:0x50].hex())]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
