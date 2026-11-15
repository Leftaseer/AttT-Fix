"""sub_004F66D0 (size 112, cdecl, ret 0): asks KERNEL32!GetModuleFileNameW for the executable's path into a
0x104-wide-character buffer with no module, forces the terminator when the call filled the buffer or read
nothing, strips the directory with SHLWAPI!PathStripPathW and builds the caller's std::wstring from the result;
the caller's pointer is returned.  All three imports are recording stubs in both IAT copies."""
import struct

VF = 0x004F66D0
IAT_FILE = 0x006070A0
IAT_STRIP = 0x006075F8
IAT_CTOR = 0x00607374

LOG_FILE = 0x00
LOG_MODULE = 0x04
LOG_BUFSIZE = 0x08
LOG_RET = 0x0C
LOG_STRIP = 0x10
LOG_FIRSTW = 0x14
LOG_LASTW = 0x18
LOG_CTOR = 0x1C
LOG_CTOR_THIS = 0x20
LOG_CTOR_STR = 0x24
LOG_BYTES = 0x40

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


def test_module_file_name(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_BYTES, bytes(LOG_BYTES))
        # "C:\GAME.EXE" as wide characters: six dwords
        name = b''
        for i, v in enumerate((0x003A0043, 0x0047005C, 0x004D0041,
                               0x002E0045, 0x00580045, 0x00000045)):
            name += b'\xC7\x00' + _dword(v) if i == 0 else b'\xC7\x40' + bytes([4 * i]) + _dword(v)
        _patch_import(h, IAT_FILE, '__imp__GetModuleFileNameW',
                      b'\x8B\x44\x24\x08'                                          # mov eax, [esp+8] (name)
                      + name
                      + b'\x66\xC7\x80\x06\x02\x00\x00\x45\x00'                     # word [eax+206] = 'E'
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_MODULE)          # [esp+4] (module) -> module
                      + b'\x8B\x44\x24\x0C\xA3' + _dword(log + LOG_BUFSIZE)         # [esp+C] (size) -> size
                      + b'\xFF\x05' + _dword(log + LOG_FILE)                        # inc [file]
                      + b'\x8B\x05' + _dword(log + LOG_RET)                         # mov eax, [ret]
                      + b'\xC2\x0C\x00')                                            # ret C
        _patch_import(h, IAT_STRIP, '__imp__PathStripPathW',
                      b'\x8B\x44\x24\x04'                                          # mov eax, [esp+4]
                      + b'\x0F\xB7\x08\x89\x0D' + _dword(log + LOG_FIRSTW)          # word [eax] -> first
                      + b'\x0F\xB7\x88\x06\x02\x00\x00\x89\x0D' + _dword(log + LOG_LASTW)  # word [eax+206]
                      + b'\xFF\x05' + _dword(log + LOG_STRIP)                       # inc [strip]
                      + b'\xC2\x04\x00')                                            # ret 4
        _patch_import(h, IAT_CTOR,
                      '__imp_??0?$basic_string@_WU?$char_traits@_W@std@@V?$allocator@_W@2@@std@@QAE@PB_W@Z',
                      b'\x89\x0D' + _dword(log + LOG_CTOR_THIS)                     # mov [this], ecx
                      + b'\x8B\x44\x24\x04\x8B\x08\x89\x0D' + _dword(log + LOG_CTOR_STR)  # [[esp+4]] -> str
                      + b'\xFF\x05' + _dword(log + LOG_CTOR)                        # inc [ctor]
                      + b'\xC2\x04\x00')                                            # ret 4
        result = h.alloc(0x40, bytes(0x40))
        for ret, firstw, lastw, start in ((12, 0x0043, 0x0045, 0x003A0043),
                                          (0x104, 0x0043, 0, 0x003A0043),
                                          (0, 0, 0x0045, 0x003A0000)):
            h.uc.mem_write(log, bytes(LOG_BYTES))
            h.uc.mem_write(log + LOG_RET, _dword(ret))
            diffs = h.compare(VF, args=[result])
            if diffs:
                return ['len %d: %s' % (ret, d) for d in diffs]
            h.uc.mem_write(log, bytes(LOG_BYTES))
            h.uc.mem_write(log + LOG_RET, _dword(ret))
            res = h.call(VF, args=[result])
            if res['fault']:
                return ['len %d: replacement faulted: %s' % (ret, res['fault'])]
            tag = 'len %d' % ret
            if _u32(h, log + LOG_FILE) != 1 or _u32(h, log + LOG_STRIP) != 1 or _u32(h, log + LOG_CTOR) != 1:
                return ['%s: imports called %d/%d/%d times' % (tag, _u32(h, log + LOG_FILE),
                                                               _u32(h, log + LOG_STRIP),
                                                               _u32(h, log + LOG_CTOR))]
            if _u32(h, log + LOG_MODULE) != 0 or _u32(h, log + LOG_BUFSIZE) != 0x104:
                return ['%s: GetModuleFileNameW(none, _, %d)' % (tag, _u32(h, log + LOG_BUFSIZE))]
            if _u32(h, log + LOG_FIRSTW) != firstw or _u32(h, log + LOG_LASTW) != lastw:
                return ['%s: stripped name starts %04X ends %04X' % (tag, _u32(h, log + LOG_FIRSTW),
                                                                     _u32(h, log + LOG_LASTW))]
            if _u32(h, log + LOG_CTOR_THIS) != result or _u32(h, log + LOG_CTOR_STR) != start:
                return ['%s: ctor on %08X from %08X' % (tag, _u32(h, log + LOG_CTOR_THIS),
                                                        _u32(h, log + LOG_CTOR_STR))]
            if res['eax'] != result:
                return ['%s: returned %08X' % (tag, res['eax'])]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
