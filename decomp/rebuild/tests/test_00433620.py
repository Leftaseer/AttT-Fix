"""CMapHeight::Instance (0x00433620): the singleton is built on the first request by operator new + the
CMapHeight constructor and cached in 0x006C88E4; a preset instance is returned untouched."""
import struct

INSTANCE = 0x00433620
SLOT = 0x006C88E4
VTABLE = 0x0060E764
SIZE = 0x30


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def test_map_height_instance(h):
    def clear(h):
        h.uc.mem_write(SLOT, bytes(4))

    diffs = h.compare(INSTANCE, ret='eax', setup=clear)
    if diffs:
        return diffs
    saved_heap = h.heap_ptr
    try:
        res = h.call(INSTANCE)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        obj = _u32(h, SLOT)
        if res['eax'] != obj or not obj:
            return ['returned %08X, m_instance %08X' % (res['eax'], obj)]
        if _u32(h, obj) != VTABLE or _u32(h, obj + 4) != 0:
            return ['vtable %08X, rows %08X' % (_u32(h, obj), _u32(h, obj + 4))]
        first = obj
        res = h.call(INSTANCE)
        if res['fault'] or res['eax'] != first or _u32(h, SLOT) != first:
            return ['second request returned %08X, first %08X' % (res['eax'], first)]
        if h.heap_ptr - saved_heap < SIZE:
            return ['allocated %d bytes, want at least %d' % (h.heap_ptr - saved_heap, SIZE)]
    finally:
        h.uc.mem_write(SLOT, bytes(4))
        h.heap_ptr = saved_heap

    sentinel = 0x11223344

    def preset(h):
        h.uc.mem_write(SLOT, struct.pack('<I', sentinel))

    diffs = h.compare(INSTANCE, ret='eax', setup=preset)
    if diffs:
        return ['preset: %s' % d for d in diffs]
    res = h.call(INSTANCE)
    if res['fault']:
        return ['preset: replacement faulted: %s' % res['fault']]
    if res['eax'] != sentinel or _u32(h, SLOT) != sentinel:
        return ['preset: returned %08X, m_instance %08X' % (res['eax'], _u32(h, SLOT))]
    h.uc.mem_write(SLOT, bytes(4))
    return []
