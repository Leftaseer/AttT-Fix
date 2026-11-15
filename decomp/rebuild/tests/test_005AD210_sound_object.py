"""sub_005AD210 (size 112, ECX thiscall, ret 4): the sound manager takes the sound object arg 1 (or none): a stream
already held (+0x68) is released (0x00591B80 with 1, then 0x005A2410 with 1 and 0 on the global 0x006C8E70's
manager); an object gives its +0x1A8 stream which is started (0x00591AF0 with 1) and returned, no object drops the
stream and returns the first entry (0x00595030, 0) of item 4 of kind 0x13F (0x00594600, on the global's manager)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x005AD210
RELEASE = 0x00591B80
STOP = 0x005A2410
START = 0x00591AF0
ITEM = 0x00594600
ENTRY = 0x00595030
GLOBAL = 0x006C8E70

REL_N = 0x00
REL_THIS = 0x04
REL_ARG = 0x08
STP_N = 0x10
STP_THIS = 0x14
STP_A = 0x18
STP_B = 0x1C
STA_N = 0x20
STA_THIS = 0x24
STA_ARG = 0x28
ITM_N = 0x30
ITM_THIS = 0x34
ITM_A = 0x38
ITM_B = 0x3C
ENT_N = 0x40
ENT_THIS = 0x44
ENT_ARG = 0x48
LOG_SIZE = 0x50

ITEM_RESULT = 0x33330000
START_RESULT = 0x1A1A1A1A
ENTRY_RESULT = 0x2B2B2B2B

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, log, count, this_off, args, result, pop):
    code = b'\xFF\x05' + _dword(log + count) + b'\x89\x0D' + _dword(log + this_off)
    for i, off in enumerate(args):
        code += b'\x8B\x44\x24' + bytes([4 + 4 * i]) + b'\xA3' + _dword(log + off)
    code += b'\xB8' + _dword(result) + b'\xC2' + struct.pack('<H', pop)
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def test_005AD210_sound_object(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        for address, code in ((RELEASE, _stub(h, log, REL_N, REL_THIS, [REL_ARG], 0x11111111, 4)),
                              (STOP, _stub(h, log, STP_N, STP_THIS, [STP_A, STP_B], 0x12121212, 8)),
                              (START, _stub(h, log, STA_N, STA_THIS, [STA_ARG], START_RESULT, 4)),
                              (ITEM, _stub(h, log, ITM_N, ITM_THIS, [ITM_A, ITM_B], ITEM_RESULT, 8)),
                              (ENTRY, _stub(h, log, ENT_N, ENT_THIS, [ENT_ARG], ENTRY_RESULT, 4))):
            _patch(h, address, b'\xE9' + struct.pack('<i', code - (address + 5)))
        manager = h.alloc(0x40, bytes(0x40))
        stream = h.alloc(0x40, bytes(0x40))
        saved[GLOBAL] = bytes(h.uc.mem_read(GLOBAL, 4))
        h.uc.mem_write(GLOBAL, _dword(manager))
        this = h.alloc(0x80, bytes(0x80))
        obj = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(obj + 0x1a8, _dword(stream))

        def setup(old, with_obj):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(this, bytes(0x80))
            h.uc.mem_write(this + 0x68, _dword(old))
            return [obj] if with_obj else [0]

        cases = [('replace', 0x11110000, 1, 1), ('fresh', 0, 1, 0),
                 ('stop', 0x11110000, 0, 1), ('empty', 0, 0, 0)]
        for name, old, with_obj, want_release in cases:
            args = setup(old, with_obj)
            diffs = h.compare(VF, args=args, regs={UC_X86_REG_ECX: this})
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            args = setup(old, with_obj)
            res = h.call(VF, args=args, regs={UC_X86_REG_ECX: this})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if _u32(h, log + REL_N) != want_release or _u32(h, log + STP_N) != want_release:
                return ['%s: releases %d/%d' % (name, _u32(h, log + REL_N), _u32(h, log + STP_N))]
            if want_release and (_u32(h, log + REL_THIS) != old or _u32(h, log + REL_ARG) != 1):
                return ['%s: release got %08X/%d' % (name, _u32(h, log + REL_THIS), _u32(h, log + REL_ARG))]
            if want_release and (_u32(h, log + STP_THIS) != manager or _u32(h, log + STP_A) != 1 or
                                 _u32(h, log + STP_B) != 0):
                return ['%s: stop got %08X/%d/%d' % (name, _u32(h, log + STP_THIS), _u32(h, log + STP_A),
                                                     _u32(h, log + STP_B))]
            if with_obj:
                if _u32(h, log + STA_N) != 1 or _u32(h, log + STA_THIS) != stream or _u32(h, log + STA_ARG) != 1:
                    return ['%s: start got %d calls, %08X/%d' % (name, _u32(h, log + STA_N), _u32(h, log + STA_THIS),
                                                                _u32(h, log + STA_ARG))]
                if _u32(h, log + ITM_N) != 0 or _u32(h, log + ENT_N) != 0:
                    return ['%s: the item path ran too' % name]
                if _u32(h, this + 0x68) != stream:
                    return ['%s: the stream is %08X' % (name, _u32(h, this + 0x68))]
                if res['eax'] != START_RESULT:
                    return ['%s: returned %08X' % (name, res['eax'])]
                continue
            if _u32(h, log + STA_N) != 0:
                return ['%s: a stream was started' % name]
            if _u32(h, log + ITM_N) != 1 or _u32(h, log + ITM_THIS) != manager or _u32(h, log + ITM_A) != 0x13F or \
                    _u32(h, log + ITM_B) != 4:
                return ['%s: item got %d calls on %08X with %X/%X' % (name, _u32(h, log + ITM_N),
                                                                      _u32(h, log + ITM_THIS), _u32(h, log + ITM_A),
                                                                      _u32(h, log + ITM_B))]
            if _u32(h, log + ENT_N) != 1 or _u32(h, log + ENT_THIS) != ITEM_RESULT or _u32(h, log + ENT_ARG) != 0:
                return ['%s: entry got %d calls on %08X/%d' % (name, _u32(h, log + ENT_N), _u32(h, log + ENT_THIS),
                                                               _u32(h, log + ENT_ARG))]
            if _u32(h, this + 0x68) != 0:
                return ['%s: the stream was not dropped' % name]
            if res['eax'] != ENTRY_RESULT:
                return ['%s: returned %08X' % (name, res['eax'])]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
