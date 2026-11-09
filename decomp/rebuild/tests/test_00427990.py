"""The two singleton accessors: CConfig::Instance (0x00427990) and CConsole::Instance (0x0042F050).  The object is
built on the first request by operator new + its constructor and cached in the CSingleton m_instance global; a
failed allocation throws instead of returning null.  The console's constructor (0x004426E0) is still the original
code, so only the caching and the object's vtables are checked here."""
import struct

CONFIG_INSTANCE = 0x00427990
CONSOLE_INSTANCE = 0x0042F050
CONFIG_SLOT = 0x006C884C
CONSOLE_SLOT = 0x006C88B0
CONFIG_VTABLE = 0x0060A298
CONSOLE_VTABLE = 0x0060A2C0
CONSOLE_CHILD_VTABLE = 0x0060A2C8
CONSOLE_SIZE = 0x1658


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _string(h, addr):
    size, capacity = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    pointer = addr + 4 if capacity < 16 else _u32(h, addr + 4)
    return bytes(h.uc.mem_read(pointer, size))


def _exercise(h, entry, slot, size):
    """first request: the accessor allocates and constructs, then caches; second request returns the same object"""
    def clear(h):
        h.uc.mem_write(slot, bytes(4))

    diffs = h.compare(entry, ret='eax', setup=clear)
    if diffs:
        return diffs
    saved_heap = h.heap_ptr
    try:
        res = h.call(entry)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        object_ = _u32(h, slot)
        if res['eax'] != object_ or not object_:
            return ['returned %08X, m_instance %08X' % (res['eax'], object_)]
        first = object_
        res = h.call(entry)
        if res['fault']:
            return ['second request faulted: %s' % res['fault']]
        if res['eax'] != first or _u32(h, slot) != first:
            return ['second request returned %08X, first %08X' % (res['eax'], first)]
        if size and h.heap_ptr - saved_heap < size:
            return ['allocated %d bytes, want at least %d' % (h.heap_ptr - saved_heap, size)]
    finally:
        h.uc.mem_write(slot, bytes(4))
        h.heap_ptr = saved_heap

    sentinel = 0x11223344

    def preset(h):
        h.uc.mem_write(slot, struct.pack('<I', sentinel))

    diffs = h.compare(entry, ret='eax', setup=preset)
    if diffs:
        return ['preset: %s' % d for d in diffs]
    res = h.call(entry)
    if res['fault']:
        return ['preset: replacement faulted: %s' % res['fault']]
    if res['eax'] != sentinel or _u32(h, slot) != sentinel:
        return ['preset: returned %08X, m_instance %08X' % (res['eax'], _u32(h, slot))]
    h.uc.mem_write(slot, bytes(4))
    return None


def test_config_instance(h):
    diffs = _exercise(h, CONFIG_INSTANCE, CONFIG_SLOT, 0x98)
    if diffs:
        return diffs
    saved_heap = h.heap_ptr
    try:
        h.uc.mem_write(CONFIG_SLOT, bytes(4))
        res = h.call(CONFIG_INSTANCE)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        obj = res['eax']
        if not obj or _u32(h, CONFIG_SLOT) != obj:
            return ['m_instance %08X follows eax %08X' % (_u32(h, CONFIG_SLOT), obj)]
        if _u32(h, obj) != CONFIG_VTABLE:
            return ['vtable %08X' % _u32(h, obj)]
        for off in (0x04, 0x20):
            if _string(h, obj + off):
                return ['string +0x%X is not empty' % off]
    finally:
        h.uc.mem_write(CONFIG_SLOT, bytes(4))
        h.heap_ptr = saved_heap
    return None


def test_console_instance(h):
    diffs = _exercise(h, CONSOLE_INSTANCE, CONSOLE_SLOT, CONSOLE_SIZE)
    if diffs:
        return diffs
    saved_heap = h.heap_ptr
    try:
        h.uc.mem_write(CONSOLE_SLOT, bytes(4))
        res = h.call(CONSOLE_INSTANCE)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        obj = res['eax']
        if not obj or _u32(h, CONSOLE_SLOT) != obj:
            return ['m_instance %08X follows eax %08X' % (_u32(h, CONSOLE_SLOT), obj)]
        if _u32(h, obj) != CONSOLE_VTABLE or _u32(h, obj + 4) != CONSOLE_CHILD_VTABLE:
            return ['vtables %08X / %08X' % (_u32(h, obj), _u32(h, obj + 4))]
        if _string(h, obj + 0x1638):
            return ['the game folder is not empty']
    finally:
        h.uc.mem_write(CONSOLE_SLOT, bytes(4))
        h.heap_ptr = saved_heap
    return None
