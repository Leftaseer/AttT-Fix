"""0x004251D0 (ECX = C3DControlsManager, ret 0): the destructor.  The vtable goes to +0, the ring whose sentinel
sits at +0x40 empties (the sentinel links to itself, the count at +0x44 becomes 0) and every node is freed with
the MSVCR80 operator delete; the vtable 0x00607D0C goes to +0x54, a non-null array at +0x58 is freed with the
operator delete[], the structure at +0x3C is released (0x0044CFE0) and the CUpdateObject base destructor
(0x00424E00) finishes.  All callees are stubs that log what they see."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004251D0
CFG = 0x0044CFE0
BASE = 0x00424E00
DELETE_SLOT = 0x006073A8
DELETE_SYM = '__imp_??3@YAXPAX@Z'
FREE_SLOT = 0x006075EC
FREE_SYM = '__imp_??_V@YAXPAX@Z'

VTABLE = 0x00607D88
ARRAY_VTABLE = 0x00607D0C
SENTINEL = 0x40
COUNT = 0x44
ARRAY_VTABLE_FIELD = 0x54
ARRAY = 0x58

L_COUNT = 0x00
L_EVENTS = 0x10
LOG_SIZE = 0x100

EV_DELETE = 1
EV_FREE = 2
EV_CFG = 3
EV_BASE = 4

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


def test_004251D0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, DELETE_SLOT, DELETE_SYM,
                      _event_stub(log, EV_DELETE, b'\x8B\x44\x24\x04\x89\x82' + _dword(4)))
        _patch_import(h, FREE_SLOT, FREE_SYM,
                      _event_stub(log, EV_FREE, b'\x8B\x44\x24\x04\x89\x82' + _dword(4)))
        _patch_thunk(h, CFG, _event_stub(log, EV_CFG, b'\x89\x8A' + _dword(4)))
        _patch_thunk(h, BASE, _event_stub(log, EV_BASE, b'\x89\x8A' + _dword(4)))
        obj = h.alloc(0x60, bytes(0x60))
        sentinel = h.alloc(0x20, bytes(0x20))
        nodes = [h.alloc(0x20, bytes(0x20)) for _ in range(3)]
        buf = h.alloc(0x40, bytes(0x40))

        # (name, nodes in the ring, array present)
        cases = (('three', True, True), ('empty', False, True), ('no-array', True, False))

        for name, listed, array in cases:
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(obj, bytes(0x60))
                h.uc.mem_write(sentinel, bytes(0x20))
                for node in nodes:
                    h.uc.mem_write(node, bytes(0x20))
                members = nodes if listed else []
                h.uc.mem_write(sentinel, _dword(members[0] if members else sentinel)
                               + _dword(members[-1] if members else sentinel))
                for i, node in enumerate(members):
                    nxt = members[i + 1] if i + 1 < len(members) else sentinel
                    prev = members[i - 1] if i else sentinel
                    h.uc.mem_write(node, _dword(nxt) + _dword(prev))
                h.uc.mem_write(obj + SENTINEL, _dword(sentinel))
                h.uc.mem_write(obj + COUNT, _dword(len(members)))
                h.uc.mem_write(obj + ARRAY_VTABLE_FIELD, _dword(0xAAAAAAAA))
                h.uc.mem_write(obj + ARRAY, _dword(buf if array else 0))

            setup()
            diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            expected = [(EV_DELETE, node) for node in (nodes if listed else [])]
            if array:
                expected.append((EV_FREE, buf))
            expected.append((EV_CFG, obj + 0x3C))
            expected.append((EV_BASE, obj))
            got = _events(h, log)
            if got != expected:
                return ['%s: events %r, expected %r' % (name, got, expected)]
            if (_u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel
                    or _u32(h, obj + COUNT) != 0):
                return ['%s: the ring did not empty' % name]
            if _u32(h, obj + ARRAY) != 0:
                return ['%s: the array pointer is %08X' % (name, _u32(h, obj + ARRAY))]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
