"""The animation manager: its constructor (0x4C01B0) and the singleton getter (0x4C0EE0).

The manager is 0x54 bytes - the vtable, then two string maps (FsHashMap, 0x28 each): the loaded models at +04
and the animation clips at +2C.  Both maps start empty: mask and count 1, nine buckets aiming at the self-linked
sentinel.  The getter builds the manager once, keeps it in 0x6CA490 and throws when the 0x54-byte allocation
fails."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x004C01B0
GET = 0x004C0EE0
MANAGER_GLOBAL = 0x006CA490
VFTABLE = 0x00611254


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _check_map(h, mapobj):
    sentinel = _u32(h, mapobj + 8)
    if not sentinel:
        return 'no sentinel'
    if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return 'the sentinel does not link to itself'
    if _u32(h, mapobj + 0xC) != 0:
        return 'size %d' % _u32(h, mapobj + 0xC)
    if struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8)) != (1, 1):
        return 'mask/count %r' % (h.uc.mem_read(mapobj + 0x20, 8),)
    begin = _u32(h, mapobj + 0x14)
    if _u32(h, mapobj + 0x18) - begin != 36:
        return 'bucket vector is %d bytes' % (_u32(h, mapobj + 0x18) - begin)
    for i in range(9):
        if _u32(h, begin + 4 * i) != sentinel:
            return 'bucket slot %d is %08X' % (i, _u32(h, begin + 4 * i))
    return None


def _check_manager(h, manager):
    if _u32(h, manager) != VFTABLE:
        return 'vtable %08X, want %08X' % (_u32(h, manager), VFTABLE)
    for name, base in (('models', manager + 4), ('animations', manager + 0x2C)):
        problem = _check_map(h, base)
        if problem:
            return '%s: %s' % (name, problem)
    return None


def test_manager_ctor(h):
    """Both map constructors only read one byte of the original's uninitialized stack slot, so the memory
    comparison is off (the byte leaks into the map's allocator field); the layout is checked by hand."""
    manager = h.alloc(0x54, bytes(0x54))
    diffs = h.compare(CTOR, regs={UC_X86_REG_ECX: manager}, ret='eax', mem=False)
    if diffs:
        return diffs
    res = h.call(CTOR, regs={UC_X86_REG_ECX: manager})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != manager:
        return ['returned %08X, want %08X' % (res['eax'], manager)]
    problem = _check_manager(h, manager)
    return [problem] if problem else []


def test_manager_getter(h):
    """the first call builds and stores the manager, later calls hand the same one back"""
    saved = bytes(h.uc.mem_read(MANAGER_GLOBAL, 4))
    try:
        h.uc.mem_write(MANAGER_GLOBAL, bytes(4))
        diffs = h.compare(GET, ret='eax')
        if diffs:
            return diffs
        res = h.call(GET)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        manager = _u32(h, MANAGER_GLOBAL)
        if not manager:
            return ['the getter did not store the manager']
        if res['eax'] != manager:
            return ['returned %08X, stored %08X' % (res['eax'], manager)]
        problem = _check_manager(h, manager)
        if problem:
            return [problem]
        again = h.call(GET)
        if again['fault']:
            return ['the second call faulted: %s' % again['fault']]
        if again['eax'] != manager or _u32(h, MANAGER_GLOBAL) != manager:
            return ['the second call returned %08X / stored %08X'
                    % (again['eax'], _u32(h, MANAGER_GLOBAL))]
        return []
    finally:
        h.uc.mem_write(MANAGER_GLOBAL, saved)


def _run_original(h, entry, args=(), regs=None):
    """call the original body the rebuilt entry jumps over (the jump is five bytes)"""
    original = bytes(h.orig.read(entry, 5))
    rebuilt = bytes(h.uc.mem_read(entry, 5))
    h.uc.mem_write(entry, original)
    try:
        return h.call(entry, args=args, regs=regs)
    finally:
        h.uc.mem_write(entry, rebuilt)


def test_manager_getter_throws_without_memory(h):
    """operator new failing (no manager) builds a CGameException and throws; nothing is stored"""
    saved = bytes(h.uc.mem_read(MANAGER_GLOBAL, 4))
    old = h.crt_new

    def fail_new():
        h._ret(0)

    h.crt_new = fail_new
    try:
        h.uc.mem_write(MANAGER_GLOBAL, bytes(4))
        original = _run_original(h, GET)
        if original['fault'] != 'threw':
            return ['the original did not throw: %r' % original['fault']]
        h.uc.mem_write(MANAGER_GLOBAL, bytes(4))
        res = h.call(GET)
        if res['fault'] != 'threw':
            return ['the replacement did not throw: %r' % res['fault']]
        stored = _u32(h, MANAGER_GLOBAL)
        if stored:
            return ['the getter stored %08X' % stored]
        return []
    finally:
        h.crt_new = old
        h.uc.mem_write(MANAGER_GLOBAL, saved)
