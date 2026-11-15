"""0x42EEC0: the vararg form of 0x004208B0 - the size above 0x7FFFFFFF is E_INVALIDARG, everything else goes to
0x004208B0 with a pointer to the first vararg; 0x004208B0 is stubbed."""
import struct

FORMAT = 0x0042EEC0
IMPL = 0x004208B0

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


def _impl_stub(h, log):
    """logs the four arguments; returns 0x2222"""
    code = b''
    for i in range(4):
        code += b'\x8B\x44\x24' + bytes([4 + 4 * i]) + b'\xA3' + _dword(log + 4 * i)
    return _stub(h, code + b'\xB8\x22\x22\x00\x00' + b'\xC2\x10\x00')


def _setup(h):
    buf = h.alloc(0x40, bytes(0x40))
    fmt = h.alloc(0x10, b'abc\0' + bytes(0xc))
    return buf, fmt


def test_checked_format(h):
    """the size check runs before the call; the vararg pointer is the first argument slot after the format"""
    heap0 = h.heap_ptr
    log = h.alloc(0x20, bytes(0x20))
    stub = _impl_stub(h, log)
    _hook(h, IMPL, stub)
    try:
        problems = []
        for name, size, calls, eax in (('fits', 0x40, True, 0x2222),
                                       ('max', 0x7FFFFFFF, True, 0x2222),
                                       ('above max', 0x80000000, False, 0x80070057)):
            buf, fmt = _setup(h)
            h.uc.mem_write(log, bytes(0x20))
            args = (buf, size, fmt, 0xAAA, 0xBBB)
            diffs = h.compare(FORMAT, args=args, ret='eax')
            if diffs:
                problems.append('%s: %s' % (name, '; '.join(diffs)))
                continue
            h.uc.mem_write(log, bytes(0x20))
            res = h.call(FORMAT, args=args)
            if res['fault']:
                problems.append('%s: %s' % (name, res['fault']))
                continue
            if res['eax'] != eax:
                problems.append('%s: returned %#x' % (name, res['eax']))
            if not calls:
                if _u32(h, log):
                    problems.append('%s: 004208B0 was called' % name)
                continue
            got = (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8))
            if got != (buf, size, fmt):
                problems.append('%s: 004208B0 got (%#x, %#x, %#x)' % ((name,) + got))
            if _u32(h, _u32(h, log + 0xc)) != 0xAAA:
                problems.append('%s: the vararg pointer does not point at the first vararg' % name)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
