"""CCursor::Instance (0x00421680): the singleton accessor builds the 0x284-byte cursor on the first request with
operator new + CCursor::CCursor and caches it in CSingleton<CCursor>::m_instance; a failed allocation throws
instead of returning null.

The real constructor loads the cursor's resources and dies in a callee the harness does not emulate (the resource
manager), so the test patches its entry with a stub - mov [probe],ecx; mov eax,ecx; ret - that records the block it
is handed and returns it.  Only the accessor's own work is under test: the allocation, the caching and the error
check."""
import struct

from difftest import STACK

INSTANCE = 0x00421680
CTOR = 0x00443E80
SLOT = 0x006C8688
SIZE = 0x284
PROBE = STACK + 0x80000          # scratch: below every frame, outside the compared part of the stack
STUB = b'\x89\x0d' + struct.pack('<I', PROBE) + b'\x89\xc8\xc3'


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def test_cursor_instance(h):
    original = bytes(h.uc.mem_read(CTOR, len(STUB)))

    def stubbed(h):
        h.uc.mem_write(SLOT, bytes(4))
        h.uc.mem_write(CTOR, STUB)

    diffs = h.compare(INSTANCE, ret='eax', setup=stubbed)
    if diffs:
        return diffs

    h.uc.mem_write(SLOT, bytes(4))
    saved_heap = h.heap_ptr
    try:
        res = h.call(INSTANCE)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        object_ = _u32(h, SLOT)
        if not object_ or res['eax'] != object_:
            return ['returned %08X, m_instance %08X' % (res['eax'], object_)]
        if h.heap_ptr - saved_heap < SIZE:
            return ['allocated %d bytes, want at least %d' % (h.heap_ptr - saved_heap, SIZE)]
        if _u32(h, PROBE) != object_:
            return ['constructor got %08X, cached %08X' % (_u32(h, PROBE), object_)]
        first = object_
        res = h.call(INSTANCE)
        if res['fault']:
            return ['second request faulted: %s' % res['fault']]
        if res['eax'] != first or _u32(h, SLOT) != first:
            return ['second request returned %08X, first %08X' % (res['eax'], first)]
    finally:
        h.uc.mem_write(SLOT, bytes(4))
        h.uc.mem_write(CTOR, original)
        h.heap_ptr = saved_heap

    sentinel = 0x11223344

    def preset(h):
        h.uc.mem_write(SLOT, struct.pack('<I', sentinel))
        h.uc.mem_write(CTOR, STUB)

    diffs = h.compare(INSTANCE, ret='eax', setup=preset)
    h.uc.mem_write(CTOR, original)
    if diffs:
        return ['preset: %s' % d for d in diffs]
    h.uc.mem_write(CTOR, STUB)
    res = h.call(INSTANCE)
    h.uc.mem_write(CTOR, original)
    if res['fault']:
        return ['preset: replacement faulted: %s' % res['fault']]
    if res['eax'] != sentinel or _u32(h, SLOT) != sentinel:
        return ['preset: returned %08X, m_instance %08X' % (res['eax'], _u32(h, SLOT))]
    h.uc.mem_write(SLOT, bytes(4))
    return None
