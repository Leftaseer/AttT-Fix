"""QuestEntry lifetime: the destructor (0x4A86E0) and the deleting destructor (0x4A8760).

The entry owns two refcounted Lua objects (the value table at +1C and its CheckFinish field at +20) and a
std::string name at +0.  A release drops the count and, at zero, calls vtable slot 0 with flag 1; the fake
vtable stub records the flag at object+0x30 so the test can see the call."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

QUEST_ENTRY_DTOR = 0x004A86E0
DELETE_QUEST_ENTRY = 0x004A8760

ENTRY_SIZE = 0x24
ENTRY_TABLE = 0x1C
ENTRY_CHECK = 0x20
OBJECT_SIZE = 0x38
STUB_FLAG = 0x30


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _put_empty_string(h, addr, text=b''):
    """a VC8 std::string: allocator, the inline buffer, the size and the capacity"""
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _release_stub(h):
    """slot 0: record the flag the caller pushed at object+0x30, return nothing (ret 4)"""
    return h.alloc(16, bytes.fromhex('8b442404 884130 c20400'))


def _vtable(h, stub):
    return h.alloc(4, struct.pack('<I', stub))


def _put_object(h, addr, vftable, refcount):
    h.uc.mem_write(addr, bytes(OBJECT_SIZE))
    h.uc.mem_write(addr, struct.pack('<III', vftable, refcount, 0))
    _put_empty_string(h, addr + 0x10)


def _put_entry(h, entry, table, check):
    h.uc.mem_write(entry, bytes(ENTRY_SIZE))
    _put_empty_string(h, entry)
    h.uc.mem_write(entry + ENTRY_TABLE, struct.pack('<I', table))
    h.uc.mem_write(entry + ENTRY_CHECK, struct.pack('<I', check))


def test_quest_entry_dtor_shared_objects(h):
    """0x4A86E0 only drops the two counts when they stay positive; nothing is destroyed."""
    entry = h.alloc(ENTRY_SIZE, bytes(ENTRY_SIZE))
    table = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    check = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        vftable = _vtable(h, stub)
        _put_object(h, table, vftable, 2)
        _put_object(h, check, vftable, 3)
        _put_entry(h, entry, table, check)
        state['heap'] = h.heap_ptr

    diffs = h.compare(QUEST_ENTRY_DTOR, regs={UC_X86_REG_ECX: entry}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(QUEST_ENTRY_DTOR, regs={UC_X86_REG_ECX: entry})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, table + 4) != 1 or _u32(h, check + 4) != 2:
        return ['counts are %d/%d, want 1/2' % (_u32(h, table + 4), _u32(h, check + 4))]
    if h.uc.mem_read(table + STUB_FLAG, 1) != b'\0' or h.uc.mem_read(check + STUB_FLAG, 1) != b'\0':
        return ['a shared object was destroyed']
    return []


def test_quest_entry_dtor_last_reference(h):
    """0x4A86E0 destroys each object whose count reaches zero with vtable slot 0 and flag 1."""
    entry = h.alloc(ENTRY_SIZE, bytes(ENTRY_SIZE))
    table = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    check = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        vftable = _vtable(h, stub)
        _put_object(h, table, vftable, 1)
        _put_object(h, check, vftable, 1)
        _put_entry(h, entry, table, check)
        state['heap'] = h.heap_ptr

    diffs = h.compare(QUEST_ENTRY_DTOR, regs={UC_X86_REG_ECX: entry}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(QUEST_ENTRY_DTOR, regs={UC_X86_REG_ECX: entry})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, table + 4) != 0 or _u32(h, check + 4) != 0:
        return ['counts are %d/%d, want 0/0' % (_u32(h, table + 4), _u32(h, check + 4))]
    if h.uc.mem_read(check + STUB_FLAG, 1) != b'\x01':
        return ['the CheckFinish object was not destroyed with flag 1']
    if h.uc.mem_read(table + STUB_FLAG, 1) != b'\x01':
        return ['the table object was not destroyed with flag 1']
    return []


def test_quest_entry_dtor_null_objects(h):
    """0x4A86E0 tolerates entries whose two object slots are null."""
    entry = h.alloc(ENTRY_SIZE, bytes(ENTRY_SIZE))

    def setup(h):
        _put_entry(h, entry, 0, 0)

    diffs = h.compare(QUEST_ENTRY_DTOR, regs={UC_X86_REG_ECX: entry}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(QUEST_ENTRY_DTOR, regs={UC_X86_REG_ECX: entry})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<II', h.uc.mem_read(entry + ENTRY_TABLE, 8)) != (0, 0):
        return ['the null slots were not left alone']
    return []


def test_delete_quest_entry(h):
    """0x4A8760 destroys the entry, calls operator delete only when flag 1 is set and returns this."""
    diffs = []
    for flags in (0, 1):
        entry = h.alloc(ENTRY_SIZE, bytes(ENTRY_SIZE))
        table = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        check = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        state = {}

        def setup(h):
            stub = _release_stub(h)
            vftable = _vtable(h, stub)
            _put_object(h, table, vftable, 1)
            _put_object(h, check, vftable, 1)
            _put_entry(h, entry, table, check)
            state['heap'] = h.heap_ptr

        diffs += h.compare(DELETE_QUEST_ENTRY, args=[flags], regs={UC_X86_REG_ECX: entry},
                           setup=setup, ret='eax')
        if diffs:
            return diffs
        h.heap_ptr = state['heap']
        res = h.call(DELETE_QUEST_ENTRY, args=[flags], regs={UC_X86_REG_ECX: entry})
        if res['fault']:
            return ['replacement faulted for flag %d: %s' % (flags, res['fault'])]
        if res['eax'] != entry:
            diffs.append('flag %d returned %#x, not this %#x' % (flags, res['eax'], entry))
        if h.uc.mem_read(check + STUB_FLAG, 1) != b'\x01':
            diffs.append('flag %d did not destroy the entry' % flags)
    return diffs
