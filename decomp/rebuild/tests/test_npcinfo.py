"""NpcInfo lifetime and the action element builder (0x4A7CE0 / 0x4A7BF0 / 0x4A7CC0 / 0x4A0490).

The 0x1EC-byte record holds three refcounted Lua objects (+1E0 value, +1E4 animation, +1E8 unknown) and three
action vectors (+20 / +1C0 / +1D0).  A release drops the count and, at zero, calls vtable slot 0 with flag 1; the
fake vtable stub records the flag at object+0x30 so the test can see the call.  BuildNpcAction reads the
iterator's text (0x55F560) and four numbers (0x55F4A0): the test patches those two callees with stubs so the
replacement is compared without a Lua state."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x004A7CE0
DTOR = 0x004A7BF0
DELETE = 0x004A7CC0
BUILD_ACTION = 0x004A0490

VALUE_TEXT = 0x0055F560
VALUE_NUMBER = 0x0055F4A0

INFO_SIZE = 0x1EC
ACTION_SIZE = 0x2C
OBJECT_SIZE = 0x38
STUB_FLAG = 0x30

INFO_VALUE = 0x1E0
INFO_ANIMATION = 0x1E4
INFO_UNKNOWN = 0x1E8
INFO_ACTIONS = 0x20
INFO_TALKS = 0x1C0
INFO_MOVES = 0x1D0
ACTION_NAME = 0x00
ACTION_A = 0x1C
ACTION_B = 0x20
ACTION_C = 0x24
ACTION_D = 0x28

ACTION_TEXT = b'abcd'


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _put_empty_string(h, addr, text=b''):
    """a VC8 std::string: allocator, the inline buffer, the size and the capacity"""
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _get_string(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    ptr = addr + 4 if cap < 16 else _u32(h, addr + 4)
    return bytes(h.uc.mem_read(ptr, size))


def _release_stub(h):
    """slot 0: record the flag the caller pushed at object+0x30, return nothing (ret 4)"""
    return h.alloc(16, bytes.fromhex('8b442404 884130 c20400'))


def _vtable(h, stub):
    return h.alloc(4, struct.pack('<I', stub))


def _put_object(h, addr, vftable, refcount):
    h.uc.mem_write(addr, bytes(OBJECT_SIZE))
    h.uc.mem_write(addr, struct.pack('<III', vftable, refcount, 0))
    _put_empty_string(h, addr + 0x10)


def _put_info(h, info, value=0, animation=0, unknown=0):
    h.uc.mem_write(info, bytes(INFO_SIZE))
    _put_empty_string(h, info)
    h.uc.mem_write(info + INFO_ACTIONS, bytes(0x10))
    h.uc.mem_write(info + INFO_TALKS, bytes(0x10))
    h.uc.mem_write(info + INFO_MOVES, bytes(0x10))
    h.uc.mem_write(info + INFO_VALUE, struct.pack('<I', value))
    h.uc.mem_write(info + INFO_ANIMATION, struct.pack('<I', animation))
    h.uc.mem_write(info + INFO_UNKNOWN, struct.pack('<I', unknown))


def test_npc_info_ctor(h):
    """0x4A7CE0 builds the name string and nulls the vectors and the three object slots; the view distance and
    the frame array stay as they were."""
    info = h.alloc(INFO_SIZE, bytes([0x5A]) * INFO_SIZE)

    def setup(h):
        info_data = bytes([0x3C]) * INFO_SIZE
        h.uc.mem_write(info, info_data)
        h.uc.mem_write(info + 0x30, bytes([0x5A]) * (INFO_SIZE - 0x30))

    diffs = h.compare(CTOR, regs={UC_X86_REG_ECX: info}, setup=setup, ret='eax')
    if diffs:
        return diffs
    res = h.call(CTOR, regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != info:
        return ['returned %#x, not this %#x' % (res['eax'], info)]
    if _get_string(h, info) != b'' or struct.unpack('<II', h.uc.mem_read(info + 20, 8)) != (0, 15):
        return ['the name string was not built empty']
    for offset in (INFO_ACTIONS, INFO_TALKS, INFO_MOVES):
        if struct.unpack('<III', h.uc.mem_read(info + offset + 4, 12)) != (0, 0, 0):
            return ['the vector at %#x is %r' % (offset, h.uc.mem_read(info + offset, 0x10))]
    if struct.unpack('<III', h.uc.mem_read(info + INFO_VALUE, 12)) != (0, 0, 0):
        return ['the object slots are %r' % (h.uc.mem_read(info + INFO_VALUE, 12),)]
    return []


def test_npc_info_dtor_shared_objects(h):
    """0x4A7BF0 only drops the three counts when they stay positive; nothing is destroyed."""
    info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    value = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    animation = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    unknown = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        vftable = _vtable(h, stub)
        _put_object(h, value, vftable, 2)
        _put_object(h, animation, vftable, 3)
        _put_object(h, unknown, vftable, 4)
        _put_info(h, info, value, animation, unknown)
        state['heap'] = h.heap_ptr

    diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: info}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(DTOR, regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    counts = (_u32(h, value + 4), _u32(h, animation + 4), _u32(h, unknown + 4))
    if counts != (1, 2, 3):
        return ['counts are %r, want (1, 2, 3)' % (counts,)]
    for object_ in (value, animation, unknown):
        if h.uc.mem_read(object_ + STUB_FLAG, 1) != b'\0':
            return ['a shared object was destroyed']
    return []


def test_npc_info_dtor_last_reference(h):
    """0x4A7BF0 destroys each object whose count reaches zero with vtable slot 0 and flag 1, then empties the
    three vectors."""
    info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
    value = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    animation = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    unknown = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
    state = {}

    def setup(h):
        stub = _release_stub(h)
        vftable = _vtable(h, stub)
        for object_ in (value, animation, unknown):
            _put_object(h, object_, vftable, 1)
        _put_info(h, info, value, animation, unknown)
        state['heap'] = h.heap_ptr

    diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: info}, setup=setup, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = state['heap']
    res = h.call(DTOR, regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    for name, object_ in (('value', value), ('animation', animation), ('unknown', unknown)):
        if _u32(h, object_ + 4) != 0:
            return ['the %s count is %d' % (name, _u32(h, object_ + 4))]
        if h.uc.mem_read(object_ + STUB_FLAG, 1) != b'\x01':
            return ['the %s object was not destroyed with flag 1' % name]
    for offset in (INFO_ACTIONS, INFO_TALKS, INFO_MOVES):
        if struct.unpack('<III', h.uc.mem_read(info + offset + 4, 12)) != (0, 0, 0):
            return ['the vector at %#x was not emptied' % offset]
    return []


def test_npc_info_dtor_null_objects(h):
    """0x4A7BF0 tolerates null object slots and empty vectors."""
    info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))

    def setup(h):
        _put_info(h, info)

    diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: info}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(DTOR, regs={UC_X86_REG_ECX: info})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<III', h.uc.mem_read(info + INFO_VALUE, 12)) != (0, 0, 0):
        return ['the null slots were not left alone']
    return []


def test_delete_npc_info(h):
    """0x4A7CC0 destroys the record, calls operator delete only when flag 1 is set and returns this."""
    diffs = []
    for flags in (0, 1):
        info = h.alloc(INFO_SIZE, bytes(INFO_SIZE))
        value = h.alloc(OBJECT_SIZE, bytes(OBJECT_SIZE))
        state = {}

        def setup(h):
            stub = _release_stub(h)
            vftable = _vtable(h, stub)
            _put_object(h, value, vftable, 1)
            _put_info(h, info, value, 0, 0)
            state['heap'] = h.heap_ptr

        diffs += h.compare(DELETE, args=[flags], regs={UC_X86_REG_ECX: info}, setup=setup, ret='eax')
        if diffs:
            return diffs
        h.heap_ptr = state['heap']
        res = h.call(DELETE, args=[flags], regs={UC_X86_REG_ECX: info})
        if res['fault']:
            return ['replacement faulted for flag %d: %s' % (flags, res['fault'])]
        if res['eax'] != info:
            diffs.append('flag %d returned %#x, not this %#x' % (flags, res['eax'], info))
        if h.uc.mem_read(value + STUB_FLAG, 1) != b'\x01':
            diffs.append('flag %d did not destroy the record' % flags)
    return diffs


def _import_call(h, predicate):
    for fake, (_, name) in h.imp_by_addr.items():
        if predicate(name):
            return fake
    raise RuntimeError('import not found')


def test_build_npc_action(h):
    """0x4A0490 fills the name from 0x55F560 and four truncated numbers from 0x55F4A0; ECX holds the action and
    the stack holds a pointer to the iterator slot.  Stubs replace the two Lua accessors."""
    action = h.alloc(ACTION_SIZE, bytes(ACTION_SIZE))
    slot = h.alloc(4, struct.pack('<I', 0x12345678))
    saved_text = bytes(h.uc.mem_read(VALUE_TEXT, 32))
    saved_number = bytes(h.uc.mem_read(VALUE_NUMBER, 16))
    state = {}
    diffs = []
    try:
        def setup(h):
            text = h.alloc(len(ACTION_TEXT) + 1, ACTION_TEXT + b'\0')
            step = h.alloc(4, struct.pack('<f', 0.75))
            ctor_cstr = _import_call(h, lambda n: n.startswith('??0?$basic_string')
                                     and n.endswith('QAE@PBD@Z'))
            text_stub = (b'\x68' + struct.pack('<I', text)      # push the text
                         + b'\x8b\x4c\x24\x08'                  # ecx = [esp+8] = the out string
                         + b'\xb8' + struct.pack('<I', ctor_cstr)  # the import pops its text argument
                         + b'\xff\xd0'                          # call the emulated ctor
                         + b'\x8b\x44\x24\x04'                  # return the out string
                         + b'\xc2\x08\x00')                     # pop the two arguments
            number_stub = (b'\xd9\x44\x24\x04'                  # fld the default
                           + b'\xd8\x05' + struct.pack('<I', step)  # + 0.75
                           + b'\xc2\x04\x00')
            h.uc.mem_write(VALUE_TEXT, text_stub)
            h.uc.ctl_remove_cache(VALUE_TEXT, VALUE_TEXT + len(text_stub))
            h.uc.mem_write(VALUE_NUMBER, number_stub)
            h.uc.ctl_remove_cache(VALUE_NUMBER, VALUE_NUMBER + len(number_stub))
            state['heap'] = h.heap_ptr

        diffs += h.compare(BUILD_ACTION, args=[slot], regs={UC_X86_REG_ECX: action}, setup=setup, ret=None)
        if diffs:
            return diffs
        h.heap_ptr = state['heap']
        res = h.call(BUILD_ACTION, args=[slot], regs={UC_X86_REG_ECX: action})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _get_string(h, action + ACTION_NAME) != ACTION_TEXT:
            return ['the name is %r' % (_get_string(h, action + ACTION_NAME),)]
        numbers = struct.unpack('<IIII', h.uc.mem_read(action + ACTION_A, 16))
        if numbers != (2, 3, 4, 5):
            diffs.append('the numbers are %r, want (2, 3, 4, 5)' % (numbers,))
    finally:
        h.uc.mem_write(VALUE_TEXT, saved_text)
        h.uc.ctl_remove_cache(VALUE_TEXT, VALUE_TEXT + len(saved_text))
        h.uc.mem_write(VALUE_NUMBER, saved_number)
        h.uc.ctl_remove_cache(VALUE_NUMBER, VALUE_NUMBER + len(saved_number))
    return diffs
