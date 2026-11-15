"""0x00425290 (ECX = the new C3DControlsManager, ret 0): the constructor.  An empty name string is built and handed
to the CUpdateObject base constructor (0x00424D00 with a null parent) and then destroyed; the vtable 0x00607D88
goes to +0, the ring at +0x3C is constructed (0x004C2F40; its sentinel lands at +0x40, count +0x44 = 0), the
vtable 0x00607D0C and a null picker array (+0x58, count +0x5C = 0) follow, the input/cursor/camera singletons go to
+0x48/+0x4C/+0x50, the hovered control +0x38 clears and a fresh 4000-byte operator new array goes to +0x58.
Returns this.  All callees are stubs that log what they see."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425290
BASE_CTOR = 0x00424D00
RING_CTOR = 0x004C2F40
INPUT = 0x004215D0
CURSOR = 0x00421680
CAMERA = 0x00424E70
NEW = 0x005E3B10
STR_CTOR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
NAME_LITERAL = 0x0060FA8B

STR_CTOR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'

VTABLE = 0x00607D88
ARRAY_VTABLE = 0x00607D0C

L_COUNT = 0x00
L_EVENTS = 0x10
L_SENTINEL = 0x90
L_INPUT = 0x94
L_CURSOR = 0x98
L_CAMERA = 0x9C
L_NEW = 0xA0
L_NEW_SIZE = 0xA4
L_NEW_RESULT = 0xA8
L_NAME = 0xAC
LOG_SIZE = 0x100

EV_STR_CTOR = 1
EV_BASE = 2
EV_STR_DTOR = 3
EV_RING = 4
EV_INPUT = 5
EV_CURSOR = 6
EV_CAMERA = 7
EV_NEW = 8

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
    return (b'\xFF\x05' + _dword(log + L_COUNT)                          # inc [count]
            + b'\xA1' + _dword(log + L_COUNT)                            # mov eax, [count]
            + b'\x48'                                                    # dec eax (event index)
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)                   # lea edx, [eax*8 + events]
            + b'\xC7\x82' + _dword(0) + _dword(code))                    # mov dword [edx], code


def _event_stub(log, code, value, tail=b'\xC3'):
    """appends (code, value) to the event list and returns; tail replaces the plain ret"""
    return _event_head(log, code) + value + tail


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_00425290(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, STR_CTOR_SLOT, STR_CTOR_SYM,
                      _event_stub(log, EV_STR_CTOR,
                                  b'\x8B\x44\x24\x04\x89\x82' + _dword(4)   # literal -> value
                                  + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_NAME)
                                  + b'\x8B\xC1',                            # eax = this
                                  b'\xC2\x04\x00'))                         # ret 4
        _patch_import(h, STR_DTOR_SLOT, STR_DTOR_SYM,
                      _event_stub(log, EV_STR_DTOR, b'\xC7\x82' + _dword(4) + _dword(0)))
        _patch_thunk(h, BASE_CTOR, _event_stub(log, EV_BASE, b'\x89\x8A' + _dword(4), b'\xC2\x08\x00'))
        _patch_thunk(h, RING_CTOR,
                     _event_head(log, EV_RING)
                     + b'\x89\x8A' + _dword(4)                              # this -> value
                     + b'\xA1' + _dword(log + L_SENTINEL)                   # eax = sentinel
                     + b'\xC3')
        for address, value, code in ((INPUT, L_INPUT, EV_INPUT), (CURSOR, L_CURSOR, EV_CURSOR),
                                     (CAMERA, L_CAMERA, EV_CAMERA)):
            _patch_thunk(h, address,
                         _event_head(log, code)
                         + b'\xA1' + _dword(log + value)
                         + b'\x89\x82' + _dword(4)                          # result -> value
                         + b'\xA1' + _dword(log + value)                    # eax = result
                         + b'\xC3')
        _patch_thunk(h, NEW,
                     _event_head(log, EV_NEW)
                     + b'\x8B\x44\x24\x04' + b'\x89\x82' + _dword(4)        # size -> value
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + L_NEW_SIZE)
                     + b'\xA1' + _dword(log + L_NEW_RESULT)                 # eax = result
                     + b'\xC3')
        obj = h.alloc(0x60, b'\xEE' * 0x60)
        sentinel = h.alloc(0x20, b'\x55' * 0x20)
        array = h.alloc(0x40, b'\x66' * 0x40)

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_SENTINEL, _dword(sentinel))
            h.uc.mem_write(log + L_INPUT, _dword(0x11111111))
            h.uc.mem_write(log + L_CURSOR, _dword(0x22222222))
            h.uc.mem_write(log + L_CAMERA, _dword(0x33333333))
            h.uc.mem_write(log + L_NEW_RESULT, _dword(array))
            h.uc.mem_write(obj, b'\xEE' * 0x60)

        setup()
        diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return [str(d) for d in diffs]
        setup()
        res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != obj:
            return ['returned %08X, expected %08X' % (res['eax'], obj)]
        expected = [(EV_STR_CTOR, NAME_LITERAL), (EV_BASE, obj), (EV_STR_DTOR, 0),
                    (EV_RING, obj + 0x3C), (EV_INPUT, 0x11111111), (EV_CURSOR, 0x22222222),
                    (EV_CAMERA, 0x33333333), (EV_NEW, 4000)]
        got = _events(h, log)
        if got != expected:
            return ['events %r, expected %r' % (got, expected)]
        if _u32(h, log + L_NAME) != NAME_LITERAL:
            return ['the name literal is %08X' % _u32(h, log + L_NAME)]
        if _u32(h, log + L_NEW_SIZE) != 4000:
            return ['allocated %d bytes' % _u32(h, log + L_NEW_SIZE)]
        for field, value in ((0x00, VTABLE), (0x38, 0), (0x40, sentinel), (0x44, 0), (0x48, 0x11111111),
                             (0x4C, 0x22222222), (0x50, 0x33333333), (0x54, ARRAY_VTABLE),
                             (0x58, array), (0x5C, 0)):
            if _u32(h, obj + field) != value:
                return ['+%02X is %08X, expected %08X' % (field, _u32(h, obj + field), value)]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
