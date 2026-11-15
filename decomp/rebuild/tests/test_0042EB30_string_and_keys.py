"""0x42EB30 (std::string deleting destructor) and 0x42EB50 (GetKeyState chain): the string destructor import,
operator delete and GetKeyState are stubbed."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

STRING_DTOR = 0x0042EB30
KEYS = 0x0042EB50
DELETE = 0x005E3E9C
STRING_DTOR_SLOT = 0x00607330
STRING_DTOR_IMPORT = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
KEY_SLOT = 0x006076D0
KEY_IMPORT = '__imp__GetKeyState'

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


def test_string_deleting_dtor(h):
    """0x42EB30: the string destructor runs first; bit 0 of the flag frees the object; this is returned"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    dtor = _stub(h, _log_ecx(log) + b'\xC3')
    delete = _stub(h, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4) + b'\xC3')
    _patch(h, STRING_DTOR_SLOT, _dword(dtor))
    _patch(h, h.symbols[STRING_DTOR_IMPORT], _dword(dtor))
    _hook(h, DELETE, delete)
    try:
        problems = []
        for flag in (1, 0, 0x100):
            s = h.alloc(0x40, bytes(0x40))
            h.uc.mem_write(log, bytes(0x10))
            diffs = h.compare(STRING_DTOR, args=(flag,), regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                problems.append('flag %#x: %s' % (flag, '; '.join(diffs)))
                continue
            res = h.call(STRING_DTOR, args=(flag,), regs={UC_X86_REG_ECX: s})
            if res['fault']:
                problems.append('flag %#x: %s' % (flag, res['fault']))
                continue
            if res['eax'] != s:
                problems.append('flag %#x: returned %#x' % (flag, res['eax']))
            if _u32(h, log) != s:
                problems.append('flag %#x: the string dtor got %#x' % (flag, _u32(h, log)))
            if flag & 1:
                if _u32(h, log + 4) != s:
                    problems.append('flag %#x: operator delete got %#x' % (flag, _u32(h, log + 4)))
            elif _u32(h, log + 4):
                problems.append('flag %#x: operator delete was called' % flag)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _key_stub(h, log):
    """logs the key and the call count; VK_CONTROL returns -1 when the mode dword at log+0xc is set"""
    code = (b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log) +            # mov eax,[esp+4]; mov [log],eax
            b'\xFF\x05' + _dword(log + 8) +                          # inc dword [log+8]
            b'\x83\x3D' + _dword(log + 0xc) + b'\x00' +              # cmp dword [log+0xc],0
            b'\x74\x0A' +                                            # je done
            b'\x83\xF8\x11' +                                        # cmp eax,0x11
            b'\x75\x05' +                                            # jne done
            b'\xB8\xFF\xFF\xFF\xFF' +                                # mov eax,-1
            b'\xC2\x04\x00')                                         # ret 4
    return _stub(h, code)


def test_getkeystate_chain(h):
    """0x42EB50: VK_HOME is polled only while VK_CONTROL is down"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    stub = _key_stub(h, log)
    _patch(h, KEY_SLOT, _dword(stub))
    _patch(h, h.symbols[KEY_IMPORT], _dword(stub))
    try:
        problems = []
        for name, ctrl_down, calls, last in (('control down', 1, 2, 0x24), ('control up', 0, 1, 0x11)):
            h.uc.mem_write(log, bytes(0x10))
            h.uc.mem_write(log + 0xc, _dword(ctrl_down))
            diffs = h.compare(KEYS, ret=None)
            if diffs:
                problems.append('%s: %s' % (name, '; '.join(diffs)))
                continue
            h.uc.mem_write(log, bytes(0x10))
            h.uc.mem_write(log + 0xc, _dword(ctrl_down))
            res = h.call(KEYS)
            if res['fault']:
                problems.append('%s: %s' % (name, res['fault']))
                continue
            if _u32(h, log + 8) != calls:
                problems.append('%s: GetKeyState was called %d times' % (name, _u32(h, log + 8)))
            if _u32(h, log) != last:
                problems.append('%s: the last key is %#x' % (name, _u32(h, log)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
