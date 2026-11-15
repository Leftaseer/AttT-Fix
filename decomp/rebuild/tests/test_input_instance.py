"""CInput::Instance (0x004215D0): the singleton accessor builds the 0x7CC-byte input object on the first request
with operator new + CInput::CInput and caches it in CSingleton<CInput>::m_instance; a failed allocation throws
instead of returning null.  The constructor is still the original code, so only the caching and the object's two
vtables and buffers are checked."""
import struct

from difftest import STACK, STACK_SIZE

INSTANCE = 0x004215D0
SLOT = 0x006C8684
VTABLE = 0x0060CC4C
UPDATER_VTABLE = 0x0060CC20
KEYS = 0x00660
BUTTONS = 0x0066C
SIZE = 0x7CC


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def test_input_instance(h):
    def clear(h):
        h.uc.mem_write(SLOT, bytes(4))
        # the constructor hands an uninitialised stack character to the input-config object (0x4BE3C0); a zeroed
        # stack makes both runs read the same value
        h.uc.mem_write(STACK + STACK_SIZE - 0x8000, bytes(0x8000))

    diffs = h.compare(INSTANCE, ret='eax', setup=clear)
    if diffs:
        return diffs

    saved_heap = h.heap_ptr
    try:
        h.uc.mem_write(SLOT, bytes(4))
        res = h.call(INSTANCE)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        object_ = _u32(h, SLOT)
        if not object_ or res['eax'] != object_:
            return ['returned %08X, m_instance %08X' % (res['eax'], object_)]
        if h.heap_ptr - saved_heap < SIZE:
            return ['allocated %d bytes, want at least %d' % (h.heap_ptr - saved_heap, SIZE)]
        if _u32(h, object_) != VTABLE or _u32(h, object_ + 4) != UPDATER_VTABLE:
            return ['vtables %08X / %08X' % (_u32(h, object_), _u32(h, object_ + 4))]
        if not _u32(h, object_ + KEYS) or not _u32(h, object_ + BUTTONS):
            return ['the key or button buffer is null']
        first = object_
        res = h.call(INSTANCE)
        if res['fault']:
            return ['second request faulted: %s' % res['fault']]
        if res['eax'] != first or _u32(h, SLOT) != first:
            return ['second request returned %08X, first %08X' % (res['eax'], first)]
    finally:
        h.uc.mem_write(SLOT, bytes(4))
        h.heap_ptr = saved_heap

    sentinel = 0x11223344

    def preset(h):
        h.uc.mem_write(SLOT, struct.pack('<I', sentinel))
        h.uc.mem_write(STACK + STACK_SIZE - 0x8000, bytes(0x8000))

    diffs = h.compare(INSTANCE, ret='eax', setup=preset)
    if diffs:
        return ['preset: %s' % d for d in diffs]
    res = h.call(INSTANCE)
    if res['fault']:
        return ['preset: replacement faulted: %s' % res['fault']]
    if res['eax'] != sentinel or _u32(h, SLOT) != sentinel:
        return ['preset: returned %08X, m_instance %08X' % (res['eax'], _u32(h, SLOT))]
    h.uc.mem_write(SLOT, bytes(4))
    return None
