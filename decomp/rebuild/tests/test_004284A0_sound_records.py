"""The ambient sound record and vector helpers at 0x4284A0..0x428A10: the 12-byte element vector copy-construct
(0x4284A0), the script's UpdateSoundInPoint (0x428570), the entry reset (0x4285F0), the origin update (0x428610),
the three vector destructors (0x428640/0x428670/0x428710), the copy-constructors (0x4286A0/0x4286D0/0x428930/
0x428970), the record destructor with its delete flag (0x4289D0), the Lua method table (0x428740), the global
registration (0x4287C0) and its "AmbientSoundManager" wrapper (0x428A10).

The record layouts are copied as opaque dwords/bytes; the vector is begin/end/cap with 12-byte elements."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

COPY_VECTOR = 0x004284A0
UPDATE_POINT = 0x00428570
CLEAR_ENTRY = 0x004285F0
UPDATE_ORIGIN = 0x00428610
FREE_1C14 = 0x00428640
FREE_1C18 = 0x00428670
COPY_ENTRY = 0x004286A0
COPY_RECORD = 0x004286D0
FREE_1C24 = 0x00428710
REGISTER_TABLE = 0x00428740
REGISTER_GLOBAL = 0x004287C0
MAKE_ENTRY = 0x00428930
MAKE_NODE = 0x00428970
DESTROY_RECORD = 0x004289D0
REGISTER_AMBIENT = 0x00428A10

UPDATE_AT = 0x00428350
FREE_BLOCK = 0x005E3E9C
NEWSTATE = 0x00402870
PUSH_NUMBER = 0x004030A0
CREATETABLE = 0x004033D0
GETFIELD = 0x00403300
RAWGETI = 0x00403390
LUA_STATE_SLOT = 0x008D122C

SOUND_TABLE = 0x006BF528
SOUND_FLAG = 0x006C8850
SOUND_REF = 0x006BF4E4
SOUND_NAME = 0x006C8848

LUA_TTABLE = 5
LUA_TFUNCTION = 6
LUA_TUSERDATA = 7
CALLBACK = 0x00427A70

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


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


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    return stub


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def _call(h, entry, args=(), regs=None):
    res = h.call(entry, args=args, regs=regs)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _bytes(count, seed=11):
    return bytes((i * 37 + seed) & 0xFF for i in range(count))


def _elements(h, count):
    return h.alloc(count * 0xc, _bytes(count * 0xc))


def _vector(h, begin, count):
    return _dword(begin) + _dword(begin + count * 0xc) + _dword(begin + count * 0xc)


def _hook_update_at(h, log, eax=0):
    """stub of 0x00428350 (thiscall, ret 4): records this and the three floats of the place"""
    return _hook(h, UPDATE_AT, b'\xBA' + _dword(log)                   # mov edx, log
                               + b'\x89\x0A'                          # mov [edx], ecx
                               + b'\x8B\x44\x24\x04'                  # mov eax, [esp+4]
                               + b'\x8B\x08'                          # mov ecx, [eax]
                               + b'\x89\x4A\x04'                      # mov [edx+4], ecx
                               + b'\x8B\x48\x04'                      # mov ecx, [eax+4]
                               + b'\x89\x4A\x08'                      # mov [edx+8], ecx
                               + b'\x8B\x48\x08'                      # mov ecx, [eax+8]
                               + b'\x89\x4A\x0C'                      # mov [edx+0xC], ecx
                               + b'\xFF\x05' + _dword(log + 0x10)     # inc dword [log+0x10]
                               + (b'\x33\xC0' if eax == 0 else b'\xB8' + _dword(eax))
                               + b'\xC2\x04\x00')                     # ret 4


def _check_update_log(h, log, where, obj):
    problems = []
    own, count = _u32(h, log), _u32(h, log + 0x10)
    if count != 1:
        problems.append('the update ran %d times' % count)
    elif own != obj:
        problems.append('the update got %08X, want %08X' % (own, obj))
    elif struct.unpack('<3f', h.uc.mem_read(log + 4, 12)) != tuple(where):
        problems.append('the place was %s, want %s' % (
            struct.unpack('<3f', h.uc.mem_read(log + 4, 12)), tuple(where)))
    return problems


def _hook_delete(h, log, count):
    return _hook(h, FREE_BLOCK, b'\x8B\x0D' + _dword(count)            # mov ecx, [count]
                                 + b'\x8B\x44\x24\x04'                 # mov eax, [esp+4]
                                 + b'\x89\x04\x8D' + _dword(log)       # mov [log+ecx*4], eax
                                 + b'\xFF\x05' + _dword(count)         # inc dword [count]
                                 + b'\x33\xC0'                         # xor eax, eax
                                 + b'\xC3')                            # ret


def _state(h):
    state = _call(h, NEWSTATE)['eax']
    h.uc.mem_write(LUA_STATE_SLOT, _dword(state))
    return state


def _pop(h, state, n=1):
    top = _u32(h, state + 8)
    h.uc.mem_write(state + 8, _dword(top - 8 * n))


def _field(h, state, index, name):
    _call(h, GETFIELD, args=(state, index, name))
    top = _u32(h, state + 8)
    value, kind = struct.unpack('<II', h.uc.mem_read(top - 8, 8))
    _pop(h, state)
    return value, kind


def _push_field(h, state, index, name):
    """lua_getfield that leaves the value on the stack"""
    _call(h, GETFIELD, args=(state, index, name))
    top = _u32(h, state + 8)
    return struct.unpack('<II', h.uc.mem_read(top - 8, 8))


def _closure(h, ptr):
    is_c = h.uc.mem_read(ptr + 6, 1)[0]
    nup = h.uc.mem_read(ptr + 7, 1)[0]
    f = _u32(h, ptr + 0x10)
    up_value, up_kind = struct.unpack('<II', h.uc.mem_read(ptr + 0x14, 8))
    return is_c, nup, f, up_value, up_kind


def _sound_state(h):
    return (bytes(h.uc.mem_read(SOUND_TABLE, 0x40)), bytes(h.uc.mem_read(SOUND_FLAG, 4)),
            bytes(h.uc.mem_read(SOUND_REF, 4)), bytes(h.uc.mem_read(SOUND_NAME, 4)))


def _restore_sound(h, state):
    table, flag, ref, name = state
    h.uc.mem_write(SOUND_TABLE, table)
    h.uc.mem_write(SOUND_FLAG, flag)
    h.uc.mem_write(SOUND_REF, ref)
    h.uc.mem_write(SOUND_NAME, name)


def _reset_sound(h):
    h.uc.mem_write(SOUND_TABLE, _dword(0x006082C8) + bytes(0x3C))
    h.uc.mem_write(SOUND_FLAG, bytes(4))
    h.uc.mem_write(SOUND_REF, bytes(4))
    h.uc.mem_write(SOUND_NAME, bytes(4))


def test_copy_vector(h):
    heap0 = h.heap_ptr
    try:
        elems = _elements(h, 2)
        src = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(src + 4, _dword(elems) + _dword(elems + 0x18))
        dst = h.alloc(0x10, b'\xAA' * 0x10)
        diffs = h.compare(COPY_VECTOR, args=(src,), regs={UC_X86_REG_ECX: dst}, ret=None)
        if diffs:
            return diffs
        problems = []
        dst = h.alloc(0x10, b'\xAA' * 0x10)
        res = _call(h, COPY_VECTOR, args=(src,), regs={UC_X86_REG_ECX: dst})
        begin, end, cap = struct.unpack('<III', h.uc.mem_read(dst + 4, 12))
        if begin == 0 or end != begin + 0x18 or cap != begin + 0x18:
            problems.append('the vector is %08X..%08X cap %08X' % (begin, end, cap))
        elif h.uc.mem_read(begin, 0x18) != h.uc.mem_read(elems, 0x18):
            problems.append('the elements were not copied')
        if res['eax'] != dst:
            problems.append('returned %08X, want %08X' % (res['eax'], dst))
        empty = h.alloc(0x10, bytes(0x10))
        dst2 = h.alloc(0x10, b'\xAA' * 0x10)
        _call(h, COPY_VECTOR, args=(empty,), regs={UC_X86_REG_ECX: dst2})
        if h.uc.mem_read(dst2 + 4, 12) != bytes(12):
            problems.append('an empty source left %s' % h.uc.mem_read(dst2 + 4, 12).hex())
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_update_point(h):
    heap0 = h.heap_ptr
    old_slot = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    try:
        log = h.alloc(0x18, bytes(0x18))
        _hook_update_at(h, log)
        args = h.alloc(0x14, bytes(0x14))
        h.uc.mem_write(args + 0x10, struct.pack('<i', -4))
        obj = h.alloc(0x10, bytes(0x10))

        def setup(h):
            state = _state(h)
            for v in (1.25, 2.5, 3.75):
                _call(h, PUSH_NUMBER, args=(state, _bits(v)))

        diffs = h.compare(UPDATE_POINT, args=(args,), regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x18))
        setup(h)
        res = _call(h, UPDATE_POINT, args=(args,), regs={UC_X86_REG_ECX: obj})
        problems = _check_update_log(h, log, (1.25, 2.5, 3.75), obj)
        if res['eax'] != 0:
            problems.append('returned %d' % res['eax'])
        return problems or None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old_slot)
        _restore(h)
        h.heap_ptr = heap0


def test_clear_entry(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x30, b'\xAA' * 0x30)
        diffs = h.compare(CLEAR_ENTRY, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        obj = h.alloc(0x30, b'\xAA' * 0x30)
        res = _call(h, CLEAR_ENTRY, regs={UC_X86_REG_ECX: obj})
        problems = []
        for off in (0, 4, 8, 0x14, 0x18, 0x1C):
            if h.uc.mem_read(obj + off, 4) != bytes(4):
                problems.append('+0x%X is %s' % (off, h.uc.mem_read(obj + off, 4).hex()))
        if h.uc.mem_read(obj + 0xC, 1) != b'\0':
            problems.append('the byte +0xC is %s' % h.uc.mem_read(obj + 0xC, 1).hex())
        if h.uc.mem_read(obj + 0x20, 0x10) != b'\xAA' * 0x10:
            problems.append('the tail was touched')
        if res['eax'] != obj:
            problems.append('returned %08X, want %08X' % (res['eax'], obj))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_update_origin(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x18, bytes(0x18))
        _hook_update_at(h, log, eax=0x1234)
        obj = h.alloc(0x10, bytes(0x10))
        diffs = h.compare(UPDATE_ORIGIN, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x18))
        res = _call(h, UPDATE_ORIGIN, regs={UC_X86_REG_ECX: obj})
        problems = _check_update_log(h, log, (0.0, 0.0, 0.0), obj)
        if res['eax'] != 0x1234:
            problems.append('returned %08X, want the update\'s 00001234' % res['eax'])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_free_vectors(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(16, bytes(16))
        count = h.alloc(4, bytes(4))
        _hook_delete(h, log, count)
        problems = []
        for entry, offset in ((FREE_1C14, 0x14), (FREE_1C18, 0x18), (FREE_1C24, 0x24)):
            obj = h.alloc(0x30, bytes(0x30))
            block = h.alloc(0x10, b'\xCC' * 0x10)
            h.uc.mem_write(obj + offset, _dword(block))
            h.uc.mem_write(obj + offset + 4, _dword(0x11111111))
            h.uc.mem_write(obj + offset + 8, _dword(0x22222222))
            diffs = h.compare(entry, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                problems += ['%08X: %s' % (entry, d) for d in diffs]
                continue
            h.uc.mem_write(count, bytes(4))
            h.uc.mem_write(log, bytes(16))
            _call(h, entry, regs={UC_X86_REG_ECX: obj})
            if _u32(h, count) != 1 or _u32(h, log) != block:
                problems.append('%08X: freed %d blocks, first %08X' % (entry, _u32(h, count), _u32(h, log)))
            if h.uc.mem_read(obj + offset, 12) != bytes(12):
                problems.append('%08X: the vector at +0x%X was not cleared' % (entry, offset))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_copy_entry(h):
    heap0 = h.heap_ptr
    try:
        elems = _elements(h, 2)
        src = h.alloc(0x20, bytes(0x20))
        h.uc.mem_write(src, _dword(0x11223344) + struct.pack('<f', -3.5) + _dword(7) + b'\x05' + bytes(3))
        h.uc.mem_write(src + 0x14, _vector(h, elems, 2))
        dst = h.alloc(0x20, b'\xAA' * 0x20)
        diffs = h.compare(COPY_ENTRY, args=(src,), regs={UC_X86_REG_ECX: dst}, ret=None)
        if diffs:
            return diffs
        dst = h.alloc(0x20, b'\xAA' * 0x20)
        res = _call(h, COPY_ENTRY, args=(src,), regs={UC_X86_REG_ECX: dst})
        problems = []
        if h.uc.mem_read(dst, 0xD) != h.uc.mem_read(src, 0xD):
            problems.append('the head is %s' % h.uc.mem_read(dst, 0xD).hex())
        begin, end, cap = struct.unpack('<III', h.uc.mem_read(dst + 0x14, 12))
        if begin == 0 or end != begin + 0x18 or cap != begin + 0x18:
            problems.append('the vector is %08X..%08X cap %08X' % (begin, end, cap))
        elif h.uc.mem_read(begin, 0x18) != h.uc.mem_read(elems, 0x18):
            problems.append('the elements were not copied')
        if res['eax'] != dst:
            problems.append('returned %08X' % res['eax'])
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_copy_record(h):
    heap0 = h.heap_ptr
    try:
        elems = _elements(h, 1)
        src = h.alloc(0x24, bytes(0x24))
        h.uc.mem_write(src, _dword(0x55667788) + _dword(0x99AABBCC) + struct.pack('<f', 6.25)
                       + _dword(0x42424242) + b'\x07' + bytes(3))
        h.uc.mem_write(src + 0x18, _vector(h, elems, 1))
        dst = h.alloc(0x24, b'\xAA' * 0x24)
        diffs = h.compare(COPY_RECORD, args=(src,), regs={UC_X86_REG_ECX: dst}, ret=None)
        if diffs:
            return diffs
        dst = h.alloc(0x24, b'\xAA' * 0x24)
        res = _call(h, COPY_RECORD, args=(src,), regs={UC_X86_REG_ECX: dst})
        problems = []
        if h.uc.mem_read(dst, 0x11) != h.uc.mem_read(src, 0x11):
            problems.append('the record is %s' % h.uc.mem_read(dst, 0x11).hex())
        begin, end, cap = struct.unpack('<III', h.uc.mem_read(dst + 0x18, 12))
        if begin == 0 or end != begin + 0xc or cap != begin + 0xc:
            problems.append('the vector is %08X..%08X cap %08X' % (begin, end, cap))
        elif h.uc.mem_read(begin, 0xc) != h.uc.mem_read(elems, 0xc):
            problems.append('the element was not copied')
        if res['eax'] != dst:
            problems.append('returned %08X' % res['eax'])
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_make_entry(h):
    heap0 = h.heap_ptr
    try:
        elems = _elements(h, 1)
        key = h.alloc(4, _dword(0xDEADBEEF))
        rec = h.alloc(0x20, bytes(0x20))
        h.uc.mem_write(rec, _dword(3) + struct.pack('<f', 0.5) + _dword(4) + b'\x01' + bytes(3))
        h.uc.mem_write(rec + 0x14, _vector(h, elems, 1))
        dst = h.alloc(0x24, b'\xAA' * 0x24)
        diffs = h.compare(MAKE_ENTRY, args=(key, rec), regs={UC_X86_REG_ECX: dst}, ret=None)
        if diffs:
            return diffs
        dst = h.alloc(0x24, b'\xAA' * 0x24)
        res = _call(h, MAKE_ENTRY, args=(key, rec), regs={UC_X86_REG_ECX: dst})
        problems = []
        if _u32(h, dst) != 0xDEADBEEF:
            problems.append('the key is %08X' % _u32(h, dst))
        if h.uc.mem_read(dst + 4, 0xD) != h.uc.mem_read(rec, 0xD):
            problems.append('the record head is %s' % h.uc.mem_read(dst + 4, 0xD).hex())
        begin, end, cap = struct.unpack('<III', h.uc.mem_read(dst + 0x18, 12))
        if begin == 0 or end != begin + 0xc or cap != begin + 0xc:
            problems.append('the vector is %08X..%08X cap %08X' % (begin, end, cap))
        elif h.uc.mem_read(begin, 0xc) != h.uc.mem_read(elems, 0xc):
            problems.append('the element was not copied')
        if res['eax'] != dst:
            problems.append('returned %08X' % res['eax'])
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_make_node(h):
    heap0 = h.heap_ptr
    try:
        elems = _elements(h, 1)
        rec = h.alloc(0x28, bytes(0x28))
        h.uc.mem_write(rec, _dword(9) + _dword(10) + struct.pack('<f', 1.5) + _dword(11)
                       + b'\x02' + bytes(3))
        h.uc.mem_write(rec + 0x18, _vector(h, elems, 1))
        dst = h.alloc(0x34, b'\xAA' * 0x34)
        diffs = h.compare(MAKE_NODE, args=(0x21, 0x22, 0x23, rec, 0x5A), regs={UC_X86_REG_ECX: dst}, ret=None)
        if diffs:
            return diffs
        dst = h.alloc(0x34, b'\xAA' * 0x34)
        res = _call(h, MAKE_NODE, args=(0x21, 0x22, 0x23, rec, 0x5A), regs={UC_X86_REG_ECX: dst})
        problems = []
        if struct.unpack('<3I', h.uc.mem_read(dst, 12)) != (0x21, 0x22, 0x23):
            problems.append('the head is %s' % h.uc.mem_read(dst, 12).hex())
        if h.uc.mem_read(dst + 0xC, 0x11) != h.uc.mem_read(rec, 0x11):
            problems.append('the record is %s' % h.uc.mem_read(dst + 0xC, 0x11).hex())
        begin, end, cap = struct.unpack('<III', h.uc.mem_read(dst + 0x24, 12))
        if begin == 0 or end != begin + 0xc or cap != begin + 0xc:
            problems.append('the vector is %08X..%08X cap %08X' % (begin, end, cap))
        elif h.uc.mem_read(begin, 0xc) != h.uc.mem_read(elems, 0xc):
            problems.append('the element was not copied')
        if h.uc.mem_read(dst + 0x30, 2) != b'\x5A\x00':
            problems.append('the flags are %s' % h.uc.mem_read(dst + 0x30, 2).hex())
        if res['eax'] != dst:
            problems.append('returned %08X' % res['eax'])
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_destroy_record(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(16, bytes(16))
        count = h.alloc(4, bytes(4))
        _hook_delete(h, log, count)
        problems = []
        for flag, frees in ((0, 1), (1, 2)):
            obj = h.alloc(0x30, bytes(0x30))
            block = h.alloc(0x10, b'\xCC' * 0x10)
            h.uc.mem_write(obj + 0x24, _dword(block))
            h.uc.mem_write(obj + 0x28, _dword(0x12345678))
            h.uc.mem_write(obj + 0x2C, _dword(0x87654321))
            diffs = h.compare(DESTROY_RECORD, args=(flag,), regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                problems += ['flag %d: %s' % (flag, d) for d in diffs]
                continue
            h.uc.mem_write(count, bytes(4))
            h.uc.mem_write(log, bytes(16))
            res = _call(h, DESTROY_RECORD, args=(flag,), regs={UC_X86_REG_ECX: obj})
            got = _u32(h, count)
            if got != frees:
                problems.append('flag %d: the delete ran %d times, want %d' % (flag, got, frees))
            elif _u32(h, log) != block or (frees == 2 and _u32(h, log + 4) != obj):
                problems.append('flag %d: deleted %08X, then %08X' % (flag, _u32(h, log), _u32(h, log + 4)))
            if h.uc.mem_read(obj + 0x24, 12) != bytes(12):
                problems.append('flag %d: the vector at +0x24 was not cleared' % flag)
            if res['eax'] != obj:
                problems.append('flag %d: returned %08X' % (flag, res['eax']))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_register_table(h):
    heap0 = h.heap_ptr
    old_slot = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    sound = _sound_state(h)
    try:
        _reset_sound(h)

        def setup(h):
            _reset_sound(h)
            state = _state(h)
            _call(h, CREATETABLE, args=(state, 0, 0))

        diffs = h.compare(REGISTER_TABLE, setup=setup, ret=None)
        if diffs:
            return diffs
        setup(h)
        state = _u32(h, LUA_STATE_SLOT)
        _call(h, REGISTER_TABLE)
        problems = []
        if not _u32(h, SOUND_FLAG) & 1:
            problems.append('the table flag is %d' % _u32(h, SOUND_FLAG))
        handlers = [(_u32(h, SOUND_TABLE + 8), 0x00427F10), (_u32(h, SOUND_TABLE + 0x18), 0x004278F0),
                    (_u32(h, SOUND_TABLE + 0x28), 0x00428570)]
        for got, want in handlers:
            if got != want:
                problems.append('a handler is %08X, want %08X' % (got, want))
        if _u32(h, SOUND_TABLE + 0x10) != 0x006082BC or _u32(h, SOUND_TABLE + 0x20) != 0x006082A8:
            problems.append('the names are %08X/%08X' % (_u32(h, SOUND_TABLE + 0x10), _u32(h, SOUND_TABLE + 0x20)))
        for name, own in ((0x006082C8, 0), (0x006082BC, 0x10), (0x006082A8, 0x20)):
            value, kind = _field(h, state, -1, name)
            if kind != LUA_TFUNCTION:
                problems.append('%08X is kind %d' % (name, kind))
                continue
            is_c, nup, f, up_value, up_kind = _closure(h, value)
            if is_c != 1 or nup != 1 or f != CALLBACK or up_value != SOUND_TABLE + own or up_kind != 2:
                problems.append('%08X: closure %d/%d %08X up %08X/%d' % (name, is_c, nup, f, up_value, up_kind))
        return problems or None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old_slot)
        _restore_sound(h, sound)
        h.heap_ptr = heap0


def test_register_global(h):
    heap0 = h.heap_ptr
    old_slot = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    sound = _sound_state(h)
    try:
        name = h.alloc(12, b'TestSound\0\0\0')

        def setup(h):
            _reset_sound(h)
            _state(h)

        diffs = h.compare(REGISTER_GLOBAL, args=(name, 0xC0FFEE11), setup=setup, ret=None)
        if diffs:
            return diffs
        setup(h)
        state = _u32(h, LUA_STATE_SLOT)
        _call(h, REGISTER_GLOBAL, args=(name, 0xC0FFEE11))
        problems = []
        if _u32(h, SOUND_NAME) != name:
            problems.append('the kept name is %08X' % _u32(h, SOUND_NAME))
        ref = _u32(h, SOUND_REF)
        if ref < 0:
            problems.append('the registry ref is %d' % ref)
        value, kind = _field(h, state, -10002, name)
        if kind != LUA_TUSERDATA:
            problems.append('the global is kind %d' % kind)
        elif value == 0:
            problems.append('the global userdata is null')
        _call(h, RAWGETI, args=(state, -10000, ref))
        top = _u32(h, state + 8)
        meta, kind = struct.unpack('<II', h.uc.mem_read(top - 8, 8))
        if kind != LUA_TTABLE:
            problems.append('the registry ref holds kind %d' % kind)
        else:
            for field, want in ((0x0068A54C, 0x004273F0), (0x00689840, 0x00563020)):
                ptr, kind = _field(h, state, -1, field)
                if kind != LUA_TFUNCTION:
                    problems.append('%08X is kind %d' % (field, kind))
                    continue
                is_c, nup, f, up_value, up_kind = _closure(h, ptr)
                if is_c != 1 or nup != 0 or f != want:
                    problems.append('%08X: closure %d/%d %08X, want %08X' % (field, is_c, nup, f, want))
            table, kind = _push_field(h, state, -1, 0x00689864)
            if kind != LUA_TTABLE:
                problems.append('__index is kind %d' % kind)
            else:
                for field, own in ((0x006082C8, 0), (0x006082BC, 0x10), (0x006082A8, 0x20)):
                    ptr, kind = _field(h, state, -1, field)
                    if kind != LUA_TFUNCTION:
                        problems.append('__index %08X is kind %d' % (field, kind))
                        continue
                    is_c, nup, f, up_value, up_kind = _closure(h, ptr)
                    if f != CALLBACK or up_value != SOUND_TABLE + own:
                        problems.append('__index %08X: %08X up %08X' % (field, f, up_value))
                _pop(h, state)
        _pop(h, state)
        return problems or None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old_slot)
        _restore_sound(h, sound)
        h.heap_ptr = heap0


def test_register_ambient(h):
    heap0 = h.heap_ptr
    old_slot = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    sound = _sound_state(h)
    try:
        def setup(h):
            _reset_sound(h)
            _state(h)

        diffs = h.compare(REGISTER_AMBIENT, regs={UC_X86_REG_ECX: 0x1234ABCD}, setup=setup, ret=None)
        if diffs:
            return diffs
        setup(h)
        state = _u32(h, LUA_STATE_SLOT)
        _call(h, REGISTER_AMBIENT, regs={UC_X86_REG_ECX: 0x1234ABCD})
        problems = []
        if _u32(h, SOUND_NAME) != 0x006082D4:
            problems.append('the kept name is %08X' % _u32(h, SOUND_NAME))
        value, kind = _field(h, state, -10002, 0x006082D4)
        if kind != LUA_TUSERDATA:
            problems.append('AmbientSoundManager is kind %d' % kind)
        return problems or None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old_slot)
        _restore_sound(h, sound)
        h.heap_ptr = heap0
