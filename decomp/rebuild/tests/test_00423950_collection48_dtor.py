"""0x00423950 (ECX = an InterfaceCollection of 0x48-byte items, ret 0): the destructor.  Every element in
[begin, end) loses its text string (at +0x1C) and then its name, a non-null begin frees the buffer with the
MSVCP80 operator delete[], the three pointers are zeroed and the title string at +0 empties last.  All callees are
stubs unless the typed implementation inlines the element loop; either way the import calls are observed."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00423950
FREE = 0x005E3E9C
FREE_SYM = '__imp_??_V@YAXPAX@Z'
STRING_SLOT = 0x00607330
STRING_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'

TITLE = 0x00
BEGIN = 0x20
END = 0x24
LIMIT = 0x28
ITEM = 0x48

L_COUNT = 0x00
L_EVENTS = 0x10
LOG_SIZE = 0x100

EV_STRING = 1
EV_FREE = 2

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
    return stub


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


def test_00423950(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, STRING_SLOT, STRING_SYM, _event_stub(log, EV_STRING, b'\x89\x8A' + _dword(4)))
        free = _event_stub(log, EV_FREE, b'\x8B\x44\x24\x04\x89\x82' + _dword(4))
        _patch(h, h.symbols[FREE_SYM], _dword(_patch_thunk(h, FREE, free)))
        coll = h.alloc(0x40, bytes(0x40))
        buf = h.alloc(4 * ITEM, bytes(4 * ITEM))

        # (name, items, begin null)
        cases = (('two', 2, False), ('none', 0, False), ('null', 0, True))

        for name, items, null in cases:
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(coll, bytes(0x40))
                h.uc.mem_write(buf, bytes(4 * ITEM))
                h.uc.mem_write(coll + TITLE, _dword(0x11111111))
                h.uc.mem_write(coll + BEGIN, _dword(0 if null else buf))
                h.uc.mem_write(coll + END, _dword(0x22222222 if null else buf + items * ITEM))
                h.uc.mem_write(coll + LIMIT, _dword(0x33333333 if null else buf + 4 * ITEM))

            setup()
            diffs = h.compare(THIS, regs={UC_X86_REG_ECX: coll}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(THIS, regs={UC_X86_REG_ECX: coll})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            expected = []
            if not null:
                for i in range(items):
                    element = buf + i * ITEM
                    expected.append((EV_STRING, element + 0x1C))
                    expected.append((EV_STRING, element))
                expected.append((EV_FREE, buf))
            expected.append((EV_STRING, coll + TITLE))
            got = _events(h, log)
            if got != expected:
                return ['%s: events %r, expected %r' % (name, got, expected)]
            for field in (BEGIN, END, LIMIT):
                if _u32(h, coll + field) != 0:
                    return ['%s: +%02X is %08X, expected 0' % (name, field, _u32(h, coll + field))]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
