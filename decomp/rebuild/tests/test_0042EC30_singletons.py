"""0x42EC30-0x42ECF0 (singleton release/getters and the GamePath base vtable), 0x42EE40 (the GamePath destructor)
and 0x42EEA0 (its deleting form): the released objects' slot 0, the string destructor and operator delete are
stubbed."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

RELEASE = ((0x0042EC30, 0x006C884C), (0x0042EC50, 0x006C88B0),
           (0x0042EC80, 0x006C88B4), (0x0042ECC0, 0x006C88B8))
GETTER = ((0x0042EC70, 0x006C88B4), (0x0042ECE0, 0x006C88BC))
VTBASE = (0x0042ECA0, 0x0042ECB0)
VTBASE_DELETING = 0x0042ECF0
GAMEPATH_DTOR = 0x0042EE40
GAMEPATH_DELETING = 0x0042EEA0
BASE_VTABLE = 0x00608CD4
GAMEPATH_VTABLE = 0x00608CE8
DELETE = 0x005E3E9C
STRING_DTOR_SLOT = 0x00607330
STRING_DTOR_IMPORT = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'

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


def _release_stub(h, log):
    """slot 0: logs (this, flag)"""
    return _stub(h, _log_ecx(log) + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4) + b'\xC2\x04\x00')


def _delete_stub(h, log):
    return _stub(h, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log) + b'\xC3')


def _object(h, slot0):
    o = h.alloc(0x40, bytes(0x40))
    vt = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(vt, _dword(slot0))
    h.uc.mem_write(o, _dword(vt))
    return o


def test_singleton_release(h):
    """the release functions call slot 0 with 1 and clear the pointer; a null pointer is left alone"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    slot0 = _release_stub(h, log)
    try:
        problems = []
        for fn, glob in RELEASE:
            _patch(h, glob, _dword(0))
            o = _object(h, slot0)
            _patch(h, glob, _dword(o))
            h.uc.mem_write(log, bytes(0x10))
            diffs = h.compare(fn, ret=None)
            if diffs:
                problems.append('%08X: %s' % (fn, '; '.join(diffs)))
                continue
            res = h.call(fn)
            if res['fault']:
                problems.append('%08X: %s' % (fn, res['fault']))
                continue
            if _u32(h, log) != o or _u32(h, log + 4) != 1:
                problems.append('%08X: slot 0 got (%#x, %#x)' % (fn, _u32(h, log), _u32(h, log + 4)))
            if _u32(h, glob):
                problems.append('%08X: the pointer is %#x' % (fn, _u32(h, glob)))
            _patch(h, glob, _dword(0))
            h.uc.mem_write(log, bytes(0x10))
            diffs = h.compare(fn, ret=None)
            if diffs:
                problems.append('%08X null: %s' % (fn, '; '.join(diffs)))
                continue
            res = h.call(fn)
            if res['fault']:
                problems.append('%08X null: %s' % (fn, res['fault']))
            elif _u32(h, log):
                problems.append('%08X null: slot 0 was called' % fn)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_singleton_getters(h):
    """the getters return the pointer held in the global"""
    heap0 = h.heap_ptr
    try:
        problems = []
        for fn, glob in GETTER:
            _patch(h, glob, _dword(0x12345678))
            diffs = h.compare(fn, ret='eax')
            if diffs:
                problems.append('%08X: %s' % (fn, '; '.join(diffs)))
                continue
            res = h.call(fn)
            if res['eax'] != 0x12345678:
                problems.append('%08X: returned %#x' % (fn, res['eax']))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_base_vtable(h):
    """0x42ECA0/0x42ECB0 write the Singleton vtable; 0x42ECF0 is the deleting form of the same"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    delete = _delete_stub(h, log)
    _hook(h, DELETE, delete)
    try:
        problems = []
        for fn in VTBASE:
            s = h.alloc(0x20, b'\x11' * 0x20)
            diffs = h.compare(fn, regs={UC_X86_REG_ECX: s}, ret=None)
            if diffs:
                problems.append('%08X: %s' % (fn, '; '.join(diffs)))
                continue
            h.uc.mem_write(s, b'\x11' * 4)
            res = h.call(fn, regs={UC_X86_REG_ECX: s})
            if res['fault']:
                problems.append('%08X: %s' % (fn, res['fault']))
            elif _u32(h, s) != h.to_rebuilt(BASE_VTABLE):
                problems.append('%08X: the vtable is %#x' % (fn, _u32(h, s)))
        for flag in (1, 0, 0x100):
            s = h.alloc(0x20, b'\x11' * 0x20)
            h.uc.mem_write(log, bytes(0x10))
            diffs = h.compare(VTBASE_DELETING, args=(flag,), regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                problems.append('flag %#x: %s' % (flag, '; '.join(diffs)))
                continue
            res = h.call(VTBASE_DELETING, args=(flag,), regs={UC_X86_REG_ECX: s})
            if res['fault']:
                problems.append('flag %#x: %s' % (flag, res['fault']))
                continue
            if res['eax'] != s:
                problems.append('flag %#x: returned %#x' % (flag, res['eax']))
            if _u32(h, s) != h.to_rebuilt(BASE_VTABLE):
                problems.append('flag %#x: the vtable is %#x' % (flag, _u32(h, s)))
            if flag & 1:
                if _u32(h, log) != s:
                    problems.append('flag %#x: operator delete got %#x' % (flag, _u32(h, log)))
            elif _u32(h, log):
                problems.append('flag %#x: operator delete was called' % flag)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_gamepath_dtor(h):
    """0x42EE40: vtable 0x00608CE8, the strings at +0x20 then +4 destroyed, then the base vtable 0x00608CD4"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    str_dtor = _stub(h, b'\xFF\x05' + _dword(log + 8) +                   # inc dword [log+8]
                        b'\x83\x3D' + _dword(log + 8) + b'\x01' +            # cmp dword [log+8],1
                        b'\x75\x07' + b'\x89\x0D' + _dword(log) + b'\xC3' +  # jne second: mov [log],ecx; ret
                        b'\x89\x0D' + _dword(log + 4) + b'\xC3')             # second: mov [log+4],ecx; ret
    _patch(h, STRING_DTOR_SLOT, _dword(str_dtor))
    _patch(h, h.symbols[STRING_DTOR_IMPORT], _dword(str_dtor))
    try:
        problems = []
        s = h.alloc(0x40, b'\x22' * 0x40)
        h.uc.mem_write(s, _dword(0x11111111))
        diffs = h.compare(GAMEPATH_DTOR, regs={UC_X86_REG_ECX: s}, ret=None)
        if diffs:
            return ['%s' % '; '.join(diffs)]
        h.uc.mem_write(log, bytes(0x10))
        res = h.call(GAMEPATH_DTOR, regs={UC_X86_REG_ECX: s})
        if res['fault']:
            return [res['fault']]
        if (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8)) != (s + 0x20, s + 4, 2):
            problems.append('the strings were destroyed at (%#x, %#x) in %d calls'
                            % (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8)))
        if _u32(h, s) != h.to_rebuilt(BASE_VTABLE):
            problems.append('the vtable is %#x' % _u32(h, s))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_gamepath_deleting_dtor(h):
    """0x42EEA0: 0x0042EE40 first (stubbed here), then operator delete when bit 0 of the flag is set"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    dtor = _stub(h, _log_ecx(log) + b'\xC3')
    delete = _delete_stub(h, log + 4)
    _hook(h, GAMEPATH_DTOR, dtor)
    _hook(h, DELETE, delete)
    try:
        problems = []
        for flag in (1, 0, 0x100):
            s = h.alloc(0x40, b'\x22' * 0x40)
            h.uc.mem_write(log, bytes(0x10))
            diffs = h.compare(GAMEPATH_DELETING, args=(flag,), regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                problems.append('flag %#x: %s' % (flag, '; '.join(diffs)))
                continue
            res = h.call(GAMEPATH_DELETING, args=(flag,), regs={UC_X86_REG_ECX: s})
            if res['fault']:
                problems.append('flag %#x: %s' % (flag, res['fault']))
                continue
            if res['eax'] != s:
                problems.append('flag %#x: returned %#x' % (flag, res['eax']))
            if _u32(h, log) != s:
                problems.append('flag %#x: the destructor got %#x' % (flag, _u32(h, log)))
            if flag & 1:
                if _u32(h, log + 4) != s:
                    problems.append('flag %#x: operator delete got %#x' % (flag, _u32(h, log + 4)))
            elif _u32(h, log + 4):
                problems.append('flag %#x: operator delete was called' % flag)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
