"""0x00422E40 (this = the record map's tree view, ret 0xc): erases the nodes of [first, last) from the ring whose
sentinel sits at this+4.  A range that covers the whole map clears it through 0x00422AD0 instead, so no node is
unlinked and the size and the sentinel's links are reset; every other listed node is unlinked, its record (record
destructor 0x004A6740), its key (MSVCP80 string destructor) and the node itself (MSVCP80 operator delete) go away
in that order and the size at this+8 drops by one.  A listed node that is the sentinel only advances.  *out
receives the node the range ended on.  The clear is the same compiled code on both sides (the typed
implementation inlines it), so it stays real and is observed through the destructor stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00422E40
RECORD_DTOR = 0x004A6740
STRING_SLOT = 0x00607330
DELETE_SLOT = 0x006073A8

RECORD_SYM = '??1InterfaceRecord@@QAE@XZ'
STRING_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
DELETE_SYM = '__imp_??3@YAXPAX@Z'

NODE = 0x15C
KEY = 0x08
VALUE = 0x24

L_COUNT = 0x00
L_EVENTS = 0x10
LOG_SIZE = 0x80

EV_BLOCK = 2
EV_KEY = 3
EV_DELETE = 4

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
    """the original entry (or the jump it holds) and the compiled symbol the replacement calls"""
    _patch_thunk(h, address, code)
    target = h.symbols.get(symbol)
    if target is not None and target != address:
        _patch_thunk(h, target, code)


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _event_stub(log, code, value):
    """appends (code, value) to the event list: EAX indexes it, EDX computes the slot, value is read from
    ECX or from the cdecl stack argument"""
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


def _ring(h, arena):
    nodes = [arena + i * NODE for i in range(4)]
    for i, node in enumerate(nodes):
        h.uc.mem_write(node, struct.pack('<II', nodes[(i + 1) % 4], nodes[(i - 1) % 4]))
    return nodes


def _links(h, nodes):
    return [struct.unpack('<II', h.uc.mem_read(node, 8)) for node in nodes]


def test_00422E40(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_symbol(h, RECORD_DTOR, RECORD_SYM, _event_stub(log, EV_BLOCK, b'\x89\x8A' + _dword(4)))
        _patch_import(h, STRING_SLOT, STRING_SYM, _event_stub(log, EV_KEY, b'\x89\x8A' + _dword(4)))
        _patch_import(h, DELETE_SLOT, DELETE_SYM, _event_stub(
            log, EV_DELETE, b'\x8B\x44\x24\x04' + b'\x89\x82' + _dword(4)))  # eax = [esp+4]; [edx+4] = eax
        mapobj = h.alloc(0x40, bytes(0x40))
        arena = h.alloc(4 * NODE, bytes(4 * NODE))
        out = h.alloc(4, b'\xEE' * 4)

        # (name, first index, last index, destroyed indices, links after, size after, out index)
        cases = (
            ('clear', 1, 0, [1, 2, 3],
             ((0, 0, 0), (1, 2, 0), (2, 3, 1), (3, 0, 2)), 0, 0),
            ('one', 1, 2, [1],
             ((0, 2, 3), (1, 2, 0), (2, 3, 0), (3, 0, 2)), 2, 2),
            ('tail', 2, 0, [2, 3],
             ((0, 1, 1), (1, 0, 0), (2, 3, 1), (3, 0, 1)), 1, 0),
            ('wrap', 0, 3, [1, 2],
             ((0, 3, 3), (1, 2, 0), (2, 3, 0), (3, 0, 0)), 1, 3),
        )
        for name, first_i, last_i, damaged, links, size, out_i in cases:
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(mapobj, bytes(0x40))
                h.uc.mem_write(out, b'\xEE' * 4)
                nodes = _ring(h, arena)
                h.uc.mem_write(mapobj + 4, _dword(nodes[0]))
                h.uc.mem_write(mapobj + 8, _dword(3))
                return nodes

            nodes = setup()
            diffs = h.compare(THIS, args=[out, nodes[first_i], nodes[last_i]],
                              regs={UC_X86_REG_ECX: mapobj}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            nodes = setup()
            res = h.call(THIS, args=[out, nodes[first_i], nodes[last_i]], regs={UC_X86_REG_ECX: mapobj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            expected = [event for i in damaged for event in ((EV_BLOCK, nodes[i] + VALUE),
                                                             (EV_KEY, nodes[i] + KEY),
                                                             (EV_DELETE, nodes[i]))]
            got = _events(h, log)
            if got != expected:
                return ['%s: events %r, expected %r' % (name, got, expected)]
            if _u32(h, out) != nodes[out_i]:
                return ['%s: out is %08X, expected %08X' % (name, _u32(h, out), nodes[out_i])]
            if _u32(h, mapobj + 8) != size:
                return ['%s: size is %d, expected %d' % (name, _u32(h, mapobj + 8), size)]
            for node, (idx, nxt, prev) in zip(nodes, links):
                if node != arena + idx * NODE:
                    return ['%s: the nodes moved' % name]
                if (nodes[nxt], nodes[prev]) != (_u32(h, node), _u32(h, node + 4)):
                    return ['%s: node %d links are (%08X, %08X), expected (%08X, %08X)'
                            % (name, idx, _u32(h, node), _u32(h, node + 4), nodes[nxt], nodes[prev])]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
