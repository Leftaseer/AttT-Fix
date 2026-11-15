"""0x00425370 (ECX = C3DControlsManager, ret 4): the deleting destructor.  The destructor 0x004251D0 always runs;
with bit 0 of the flag set the object itself is freed with the MSVCR80 operator delete.  Returns the object.
Both callees are stubs that log what they see."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425370
DTOR = 0x004251D0
DELETE_SLOT = 0x006073A8
DELETE_SYM = '__imp_??3@YAXPAX@Z'

L_COUNT = 0x00
L_EVENTS = 0x10
LOG_SIZE = 0x80

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


def _patch_symbol(h, address, symbol, code):
    """the original entry and the compiled symbol the replacement may jump to"""
    _patch_thunk(h, address, code)
    target = h.symbols.get(symbol)
    if target is not None and target != address:
        _patch_thunk(h, target, code)


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _event_stub(log, code, value):
    """appends (code, value) to the event list: EAX indexes it, EDX computes the slot, value writes [edx+4]"""
    return (b'\xFF\x05' + _dword(log + L_COUNT)                          # inc [count]
            + b'\xA1' + _dword(log + L_COUNT)                            # mov eax, [count]
            + b'\x48'                                                    # dec eax (event index)
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)                   # lea edx, [eax*8 + events]
            + b'\xC7\x82' + _dword(0) + _dword(code)                     # mov dword [edx], code
            + value
            + b'\xC3')                                                   # ret


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_00425370(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_symbol(h, DTOR, 'f_004251D0', _event_stub(log, EV_DTOR, b'\x89\x8A' + _dword(4)))
        _patch_import(h, DELETE_SLOT, DELETE_SYM,
                      _event_stub(log, EV_DELETE, b'\x8B\x44\x24\x04\x89\x82' + _dword(4)))
        obj = h.alloc(0x60, b'\x77' * 0x60)

        for flags in (0, 1, 2, 3):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(obj, b'\x77' * 0x60)

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
            expected = [(EV_DTOR, obj)]
            if flags & 1:
                expected.append((EV_DELETE, obj))
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
