"""NSound::Sound2D vf3 (0x004C1710): with +8 clear the input EAX passes through and nothing happens; otherwise
+9 is set, the sample handle at +0x38 gets the loop count and is either started (milliseconds 0) or seeked to
the millisecond position and resumed.  The four AIL imports are replaced by recording stubs in the IAT."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

VF = 0x004C1710
IAT_LOOP = 0x006078A4
IAT_START = 0x00607890
IAT_POS = 0x0060788C
IAT_RESUME = 0x00607888
HANDLE = 0x1234ABCD

LOG_LOOP = 0x00
LOG_LOOP_HANDLE = 0x04
LOG_LOOP_ARG = 0x08
LOG_START = 0x0C
LOG_START_HANDLE = 0x10
LOG_POS = 0x14
LOG_POS_HANDLE = 0x18
LOG_POS_ARG = 0x1C
LOG_RESUME = 0x20
LOG_RESUME_HANDLE = 0x24
LOG_SEQ_COUNT = 0x28
LOG_SEQ = 0x2C
LOG_SIZE = 0x60

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _dword(addr):
    return struct.pack('<I', addr)


def _seq(code, log, ident):
    return (b'\x8B\x05' + _dword(log + LOG_SEQ_COUNT)                    # mov eax, [seq count]
            + b'\xC7\x04\x85' + _dword(log + LOG_SEQ) + _dword(ident)    # mov [eax*4+seq], ident
            + b'\xFF\x05' + _dword(log + LOG_SEQ_COUNT)                  # inc [seq count]
            + code)


def _patch_import(h, original_slot, symbol, code):
    """the original body reads the IAT copy at its own address, the rebuilt code the relinked slot"""
    stub = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(stub, stub + len(code))
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _install_stubs(h, log):
    loop = _seq(b'\xC7\x05' + _dword(log + LOG_LOOP) + _dword(1)          # mov [loop], 1
                + b'\x8B\x44\x24\x04'                                     # mov eax, [esp+4]
                + b'\xA3' + _dword(log + LOG_LOOP_HANDLE)                 # mov [loop handle], eax
                + b'\x8B\x44\x24\x08'                                     # mov eax, [esp+8]
                + b'\xA3' + _dword(log + LOG_LOOP_ARG)                    # mov [loop arg], eax
                + b'\xB8\x11\x11\x11\x11'                                 # mov eax, 11111111h
                + b'\xC2\x08\x00', log, 1)                                # ret 8
    start = _seq(b'\xFF\x05' + _dword(log + LOG_START)                    # inc [start]
                 + b'\x8B\x44\x24\x04'                                    # mov eax, [esp+4]
                 + b'\xA3' + _dword(log + LOG_START_HANDLE)               # mov [start handle], eax
                 + b'\xB8\x22\x22\x22\x22'                                # mov eax, 22222222h
                 + b'\xC2\x04\x00', log, 2)                               # ret 4
    pos = _seq(b'\xFF\x05' + _dword(log + LOG_POS)                        # inc [pos]
               + b'\x8B\x44\x24\x04'                                      # mov eax, [esp+4]
               + b'\xA3' + _dword(log + LOG_POS_HANDLE)                   # mov [pos handle], eax
               + b'\x8B\x44\x24\x08'                                      # mov eax, [esp+8]
               + b'\xA3' + _dword(log + LOG_POS_ARG)                      # mov [pos arg], eax
               + b'\xB8\x33\x33\x33\x33'                                  # mov eax, 33333333h
               + b'\xC2\x08\x00', log, 3)                                 # ret 8
    resume = _seq(b'\xFF\x05' + _dword(log + LOG_RESUME)                  # inc [resume]
                  + b'\x8B\x44\x24\x04'                                   # mov eax, [esp+4]
                  + b'\xA3' + _dword(log + LOG_RESUME_HANDLE)             # mov [resume handle], eax
                  + b'\xB8\x44\x44\x44\x44'                               # mov eax, 44444444h
                  + b'\xC2\x04\x00', log, 4)                              # ret 4
    _patch_import(h, IAT_LOOP, '__imp___AIL_set_sample_loop_count@8', loop)
    _patch_import(h, IAT_START, '__imp___AIL_start_sample@4', start)
    _patch_import(h, IAT_POS, '__imp___AIL_set_sample_ms_position@8', pos)
    _patch_import(h, IAT_RESUME, '__imp___AIL_resume_sample@4', resume)


def test_sound2d_vf3(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _install_stubs(h, log)
        for flag in (0, 1):
            for milliseconds, want_eax, want_seq in (
                    (0, 0x22222222, [1, 2]),
                    (0x1000, 0x44444444, [1, 3, 4])):
                h.uc.mem_write(log, bytes(LOG_SIZE))
                obj = h.alloc(0x100, bytes(0x100))
                h.uc.mem_write(obj + 8, bytes([flag]))
                h.uc.mem_write(obj + 0x38, _dword(HANDLE))
                in_eax = 0xFEEDFACE
                diffs = h.compare(VF, args=[3, milliseconds],
                                  regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
                if diffs:
                    return ['flag %d ms %#x: %s' % (flag, milliseconds, d) for d in diffs]
                h.uc.mem_write(log, bytes(LOG_SIZE))
                res = h.call(VF, args=[3, milliseconds],
                             regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
                if res['fault']:
                    return ['flag %d ms %#x: replacement faulted: %s' % (flag, milliseconds, res['fault'])]
                tag = 'flag %d ms %#x' % (flag, milliseconds)
                seq = [_u32(h, log + LOG_SEQ + 4 * i) for i in range(_u32(h, log + LOG_SEQ_COUNT))]
                if not flag:
                    if seq:
                        return ['%s: imports called %r' % (tag, seq)]
                    if res['eax'] != in_eax:
                        return ['%s: returned %08X, want %08X' % (tag, res['eax'], in_eax)]
                    if h.uc.mem_read(obj + 9, 1)[0] != 0:
                        return ['%s: marked started' % tag]
                    continue
                if seq != want_seq:
                    return ['%s: called %r, want %r' % (tag, seq, want_seq)]
                if res['eax'] != want_eax:
                    return ['%s: returned %08X, want %08X' % (tag, res['eax'], want_eax)]
                if h.uc.mem_read(obj + 9, 1)[0] != 1:
                    return ['%s: not marked started' % tag]
                if _u32(h, log + LOG_LOOP_HANDLE) != HANDLE or _u32(h, log + LOG_LOOP_ARG) != 3:
                    return ['%s: loop count on %08X with %d' % (tag, _u32(h, log + LOG_LOOP_HANDLE),
                                                                _u32(h, log + LOG_LOOP_ARG))]
                if not milliseconds:
                    if _u32(h, log + LOG_START_HANDLE) != HANDLE:
                        return ['%s: started %08X' % (tag, _u32(h, log + LOG_START_HANDLE))]
                else:
                    if (_u32(h, log + LOG_POS_HANDLE) != HANDLE
                            or _u32(h, log + LOG_POS_ARG) != milliseconds):
                        return ['%s: seek on %08X to %d' % (tag, _u32(h, log + LOG_POS_HANDLE),
                                                            _u32(h, log + LOG_POS_ARG))]
                    if _u32(h, log + LOG_RESUME_HANDLE) != HANDLE:
                        return ['%s: resumed %08X' % (tag, _u32(h, log + LOG_RESUME_HANDLE))]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
