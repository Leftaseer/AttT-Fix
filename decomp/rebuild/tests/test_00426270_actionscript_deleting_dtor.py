"""0x00426270 (ECX = the ActionScript object, ret 4 = the flags byte): its deleting destructor: 0x00426070, then
operator delete 0x005E3E9C when the low bit of the flags is set.  Returns this.  Both callees are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00426270
DTOR = 0x00426070
DELETE = 0x005E3E9C

L_COUNT = 0x00
L_EVENTS = 0x10
LOG_SIZE = 0x90

EV_DTOR = 1
EV_DELETE = 2

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
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _event_head(log, code):
    return (b'\xFF\x05' + _dword(log + L_COUNT)
            + b'\xA1' + _dword(log + L_COUNT)
            + b'\x48'
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)
            + b'\xC7\x82' + _dword(0) + _dword(code))


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_00426270(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, DTOR,
                     _event_head(log, EV_DTOR)
                     + b'\x89\x8A' + _dword(4)                                  # ecx -> value
                     + b'\xC3')
        _patch_thunk(h, DELETE,
                     _event_head(log, EV_DELETE)
                     + b'\x8B\x44\x24\x04\x89\x82' + _dword(4)                  # the block -> value
                     + b'\xC3')
        obj = h.alloc(0x20, b'\xEE' * 0x20)

        for flags in (0, 1):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(obj, b'\xEE' * 0x20)

            expected = [(EV_DTOR, obj)]
            if flags & 1:
                expected.append((EV_DELETE, obj))
            setup()
            diffs = h.compare(THIS, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            setup()
            res = h.call(THIS, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['flags %d: returned %08X' % (flags, res['eax'])]
            got = _events(h, log)
            if got != expected:
                return ['flags %d: events %r, expected %r' % (flags, got, expected)]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
