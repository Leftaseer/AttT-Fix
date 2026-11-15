"""0x42EFF0: releases CEngine (0x006C88B8), CConfig (0x006C884C) and 0x006C88B4 through slot 0 with 1,
clears them and zeroes 0x006C88A8/0x006C88A4; the released objects' slot 0 is stubbed."""
import struct

RELEASE_ALL = 0x0042EFF0
GLOBALS = (0x006C88B8, 0x006C884C, 0x006C88B4)
CLEARED = (0x006C88A8, 0x006C88A4)

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


def _log_this(offset):
    return b'\x89\x0D' + _dword(offset)


def _release_stub(h, log):
    """slot 0 (this in ECX, the flag in [esp+4]): logs the last this, then appends (this, flag) pairs"""
    return _stub(h, _log_this(log) +
                 b'\x8B\xD1' +                                      # mov edx,ecx
                 b'\xFF\x05' + _dword(log + 4) +                    # inc dword [log+4]
                 b'\x8B\x0D' + _dword(log + 4) +                    # mov ecx,[log+4]
                 b'\x49' +                                          # dec ecx
                 b'\x8D\x0C\xCD' + _dword(log + 8) +                # lea ecx,[log+8+ecx*8]
                 b'\x89\x11' +                                      # mov [ecx],edx
                 b'\x8B\x54\x24\x04' + b'\x89\x51\x04' +            # mov edx,[esp+4]; mov [ecx+4],edx
                 b'\xC2\x04\x00')


def _object(h, slot0):
    o = h.alloc(0x40, bytes(0x40))
    vt = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(vt, _dword(slot0))
    h.uc.mem_write(o, _dword(vt))
    return o


def test_release_all(h):
    """all three singletons are released in order and their globals cleared; the paired globals are zeroed"""
    heap0 = h.heap_ptr
    log = h.alloc(0x40, bytes(0x40))
    slot0 = _release_stub(h, log)
    try:
        problems = []
        for glob in GLOBALS:
            _patch(h, glob, _dword(0x11111111))
        for glob in CLEARED:
            _patch(h, glob, _dword(0x22222222))
        objs = []
        for glob in GLOBALS:
            o = _object(h, slot0)
            objs.append(o)
            _patch(h, glob, _dword(o))
        h.uc.mem_write(log, bytes(0x40))
        diffs = h.compare(RELEASE_ALL, ret=None)
        if diffs:
            return ['; '.join(diffs)]
        h.uc.mem_write(log, bytes(0x40))
        res = h.call(RELEASE_ALL)
        if res['fault']:
            return [res['fault']]
        if _u32(h, log + 4) != len(objs):
            problems.append('slot 0 was called %d times' % _u32(h, log + 4))
        pairs = [(_u32(h, log + 8 + i * 8), _u32(h, log + 12 + i * 8)) for i in range(len(objs))]
        if pairs != [(o, 1) for o in objs]:
            problems.append('slot 0 got %s' % ', '.join('(%#x, %#x)' % p for p in pairs))
        for glob in GLOBALS:
            if _u32(h, glob):
                problems.append('%08X is %#x' % (glob, _u32(h, glob)))
        for glob in CLEARED:
            if _u32(h, glob):
                problems.append('%08X is %#x' % (glob, _u32(h, glob)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_release_all_null(h):
    """null singletons are skipped and everything is still cleared"""
    heap0 = h.heap_ptr
    log = h.alloc(0x10, bytes(0x10))
    slot0 = _release_stub(h, log)
    try:
        problems = []
        for glob in GLOBALS:
            _patch(h, glob, _dword(0))
        for glob in CLEARED:
            _patch(h, glob, _dword(0x22222222))
        diffs = h.compare(RELEASE_ALL, ret=None)
        if diffs:
            return ['; '.join(diffs)]
        h.uc.mem_write(log, bytes(0x10))
        res = h.call(RELEASE_ALL)
        if res['fault']:
            return [res['fault']]
        if _u32(h, log + 4):
            problems.append('slot 0 was called')
        for glob in CLEARED:
            if _u32(h, glob):
                problems.append('%08X is %#x' % (glob, _u32(h, glob)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
