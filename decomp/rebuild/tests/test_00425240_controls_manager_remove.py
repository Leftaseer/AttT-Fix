"""0x00425240 (ECX = C3DControlsManager, ret 4): removes the control whose id (+8) matches.  The ring's sentinel
sits at +0x40; a found node (never the sentinel) is unlinked from its neighbours, freed with the MSVCR80 operator
delete and the count at +0x44 drops by one.  An id nobody has leaves the ring untouched."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425240
DELETE_SLOT = 0x006073A8
DELETE_SYM = '__imp_??3@YAXPAX@Z'

SENTINEL = 0x40
COUNT = 0x44
NODE = 0x0C

L_COUNT = 0x00
L_EVENTS = 0x10
LOG_SIZE = 0x80

EV_DELETE = 1

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


def _links(h, nodes):
    return [struct.unpack('<II', h.uc.mem_read(node, 8)) for node in nodes]


def test_00425240(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, DELETE_SLOT, DELETE_SYM,
                      _event_stub(log, EV_DELETE, b'\x8B\x44\x24\x04\x89\x82' + _dword(4)))
        obj = h.alloc(0x60, bytes(0x60))
        sentinel = h.alloc(0x20, bytes(0x20))
        nodes = [h.alloc(NODE, bytes(NODE)) for _ in range(3)]
        ids = (7, 8, 9)

        # (name, ring member indices, id to remove, removed index, links after (sentinel, nodes), count after)
        cases = (
            ('middle', [0, 1, 2], 8, 1, ((1, 3), (3, 0), (3, 1), (0, 1)), 2),
            ('head', [0, 1, 2], 7, 0, ((2, 3), (2, 0), (3, 0), (0, 2)), 2),
            ('tail', [0, 1, 2], 9, 2, ((1, 2), (2, 0), (0, 1), (0, 2)), 2),
            ('absent', [0, 1, 2], 5, None, ((1, 3), (2, 0), (3, 1), (0, 2)), 3),
            ('empty', [], 5, None, ((0, 0), (0, 0), (0, 0), (0, 0)), 0),
        )
        for name, members, remove_id, removed, links, count in cases:
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(obj, bytes(0x60))
                for i, node in enumerate(nodes):
                    h.uc.mem_write(node, _dword(sentinel) + _dword(sentinel) + _dword(ids[i]))
                ring = [sentinel] + [nodes[i] for i in members]
                for i, node in enumerate(members):
                    n = nodes[node]
                    h.uc.mem_write(n, _dword(ring[(i + 2) % len(ring)])
                                   + _dword(ring[i % len(ring)]) + _dword(ids[node]))
                if len(ring) > 1:
                    h.uc.mem_write(sentinel, _dword(ring[1]) + _dword(ring[-1]))
                else:
                    h.uc.mem_write(sentinel, _dword(sentinel) + _dword(sentinel))
                h.uc.mem_write(obj + SENTINEL, _dword(sentinel))
                h.uc.mem_write(obj + COUNT, _dword(len(members)))

            setup()
            diffs = h.compare(THIS, args=[remove_id], regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(THIS, args=[remove_id], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            expected = [(EV_DELETE, nodes[removed])] if removed is not None else []
            got = _events(h, log)
            if got != expected:
                return ['%s: events %r, expected %r' % (name, got, expected)]
            if _u32(h, obj + COUNT) != count:
                return ['%s: count is %d, expected %d' % (name, _u32(h, obj + COUNT), count)]
            all_nodes = [sentinel] + nodes
            expected_links = [(all_nodes[nxt], all_nodes[prev]) for nxt, prev in links]
            if _links(h, all_nodes) != expected_links:
                return ['%s: links %r, expected %r' % (name, _links(h, all_nodes), expected_links)]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
