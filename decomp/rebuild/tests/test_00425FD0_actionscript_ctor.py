"""0x00425FD0 (ECX = the ActionScript object, ret 0): its constructor.  An empty name string is built and handed to
the CRenderObject base (0x004AB9C0 with no parent) and destroyed; the vtable 0x00607F0C goes to +0 and +0x58 gets
0x00607ED0 and then 0x00607F00; the manager +0x60, the action +0x6C and the byte +0x70 clear.  Returns this.
All callees are stubs that log what they see."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425FD0
BASE_CTOR = 0x004AB9C0
STR_CTOR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
NAME_LITERAL = 0x0060FA8B

STR_CTOR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'

VTABLE = 0x00607F0C
VTABLE_58 = 0x00607F00

L_COUNT = 0x00
L_EVENTS = 0x10
L_NAME = 0x90
L_PARENT = 0x94
LOG_SIZE = 0xA0

EV_STR_CTOR = 1
EV_BASE = 2
EV_STR_DTOR = 3

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


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _event_head(log, code):
    return (b'\xFF\x05' + _dword(log + L_COUNT)
            + b'\xA1' + _dword(log + L_COUNT)
            + b'\x48'
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)
            + b'\xC7\x82' + _dword(0) + _dword(code))


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_00425FD0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, STR_CTOR_SLOT, STR_CTOR_SYM,
                      _event_head(log, EV_STR_CTOR)
                      + b'\x8B\x44\x24\x04\x89\x82' + _dword(4)                  # literal -> value
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_NAME)           # literal -> log
                      + b'\x8B\xC1'                                              # eax = this
                      + b'\xC2\x04\x00')                                         # ret 4
        _patch_import(h, STR_DTOR_SLOT, STR_DTOR_SYM,
                      _event_head(log, EV_STR_DTOR)
                      + b'\xC3')
        _patch_thunk(h, BASE_CTOR,
                     _event_head(log, EV_BASE)
                     + b'\x89\x8A' + _dword(4)                                  # this -> value
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_PARENT)         # the parent
                     + b'\xC2\x08\x00')                                         # ret 8
        obj = h.alloc(0x80, b'\xEE' * 0x80)

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(obj, b'\xEE' * 0x80)

        setup()
        diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return [str(d) for d in diffs]
        setup()
        res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if res['eax'] != obj:
            return ['returned %08X, expected %08X' % (res['eax'], obj)]
        expected = [(EV_STR_CTOR, NAME_LITERAL), (EV_BASE, obj), (EV_STR_DTOR, 0)]
        got = _events(h, log)
        if got != expected:
            return ['events %r, expected %r' % (got, expected)]
        if _u32(h, log + L_NAME) != NAME_LITERAL:
            return ['the name literal is %08X' % _u32(h, log + L_NAME)]
        if _u32(h, log + L_PARENT) != 0:
            return ['the parent is %08X' % _u32(h, log + L_PARENT)]
        for field, value in ((0x00, VTABLE), (0x58, VTABLE_58), (0x60, 0), (0x6c, 0)):
            if _u32(h, obj + field) != value:
                return ['+%02X is %08X, expected %08X' % (field, _u32(h, obj + field), value)]
        if h.uc.mem_read(obj + 0x70, 1) != b'\x00':
            return ['+70 is %02X' % h.uc.mem_read(obj + 0x70, 1)[0]]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
