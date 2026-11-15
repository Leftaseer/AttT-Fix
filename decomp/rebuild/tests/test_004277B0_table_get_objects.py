"""nScript script reads and handle objects: nScript::TableGet (0x4277B0 construction, 0x427820 destruction,
0x4278A0 deleting destructor) and the handle base behind 0x4278C0 (construction) / 0x4278E0 (destruction).

The read records the Lua stack depth above its values through lua_gettop (0x402A60) and gives the owned depth
back through lua_settop (0x402A70), so the tests create a real Lua state and install it in the engine global
0x008D122C.  A read whose +4 is set makes the _Object destructor throw; the fixtures keep +4 clear."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C

NEWSTATE = 0x00402870
GETTOP = 0x00402A60
TABLE_GET = 0x004277B0
TABLE_GET_DTOR = 0x00427820
TABLE_GET_DELETE = 0x004278A0
HANDLE_CTOR = 0x004278C0
HANDLE_DTOR = 0x004278E0
FREE_BLOCK = 0x005E3E9C

TABLE_GET_VTABLE = 0x00608260
BASE_VTABLE = 0x00607CB8
OBJECT_VTABLE = 0x00607C88
HANDLE_VTABLE = 0x0060826C

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


def _fields(h, addr, count):
    return struct.unpack('<%dI' % count, h.uc.mem_read(addr, 4 * count))


def _state(h):
    """a fresh Lua state installed in the engine's global"""
    state = _call(h, NEWSTATE)['eax']
    h.uc.mem_write(LUA_STATE_SLOT, _dword(state))
    return state


def _top(h, state):
    return _call(h, GETTOP, args=(state,))['eax']


def _push_numbers(h, state, count):
    """count number TValues, so the stack top ends up count entries above the base"""
    top = _u32(h, state + 8)
    for i in range(count):
        h.uc.mem_write(top, struct.pack('<fI', float(i), 3))
        top += 8
    h.uc.mem_write(state + 8, _dword(top))


def test_constructor(h):
    heap0 = h.heap_ptr
    old = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    try:
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        for table, count, owns in ((0x0061D90C, 2, 1), (0x1234, 0, 0), (0x5678, 3, 0x100)):
            def setup(h):
                state = _state(h)
                _push_numbers(h, state, count)
                _push_numbers(h, state, 2)
                h.uc.mem_write(obj, b'\xEE' * 0x20)

            diffs = h.compare(TABLE_GET, args=(table, count, owns), regs={UC_X86_REG_ECX: obj},
                              setup=setup, ret=None)
            if diffs:
                return ['count %d: %s' % (count, d) for d in diffs]
            setup(h)
            res = h.call(TABLE_GET, args=(table, count, owns), regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['count %d: replacement faulted: %s' % (count, res['fault'])]
            if res['eax'] != obj:
                return ['count %d: returned %08X' % (count, res['eax'])]
            got = _fields(h, obj, 6)
            want = (TABLE_GET_VTABLE, 0, table, count, 2, owns & 0xFF)
            if got[:5] != want[:5] or (got[5] & 0xFF) != want[5]:
                return ['count %d: fields (%08X, %08X, %08X, %d, %d, %02X), want '
                        '(%08X, 0, %08X, %d, 2, %02X)'
                        % ((count,) + got + (want[0], want[2], want[3], want[5]))]
            if _u32(h, obj + 0x18) != 0xEEEEEEEE:
                return ['count %d: bytes past +0x14 changed' % count]
        return None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old)
        _restore(h)
        h.heap_ptr = heap0


def test_destructor(h):
    heap0 = h.heap_ptr
    old = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    try:
        obj = h.alloc(0x20, bytes(0x20))
        state = [None]

        def write(obj_count, owns, extra):
            h.uc.mem_write(obj, struct.pack('<6I', TABLE_GET_VTABLE, 0, 0x1234, obj_count & 0xFFFFFFFF,
                                            extra, owns))

        for count, owns, extra in ((2, 1, 0), (2, 0, 0), (1, 1, 3), (0, 1, 0), (-1, 1, 0)):
            def setup(h):
                state[0] = _state(h)
                _push_numbers(h, state[0], max(count, 0) + 2)
                write(count, owns, extra)

            diffs = h.compare(TABLE_GET_DTOR, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
            if diffs:
                return ['count %d owns %d: %s' % (count, owns, d) for d in diffs]
            setup(h)
            res = h.call(TABLE_GET_DTOR, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['count %d: replacement faulted: %s' % (count, res['fault'])]
            pops = count if count > 0 and owns else 0
            top = _top(h, state[0])
            if top != max(count, 0) + 2 - pops:
                return ['count %d owns %d: top %d after the release' % (count, owns, top)]
            got = _fields(h, obj, 6)
            want_count = 0 if count > 0 else count & 0xFFFFFFFF
            if got[0] != OBJECT_VTABLE or got[1] != 0 or got[2] != 0x1234:
                return ['count %d: released as (%08X, %08X, %08X)'
                        % (count, got[0], got[1], got[2])]
            if got[3] != want_count or got[4] != extra:
                return ['count %d: (%d, %d) left at +0xC/+0x10, want (%d, %d)'
                        % (count, got[3], got[4], want_count, extra)]
        return None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old)
        _restore(h)
        h.heap_ptr = heap0


def test_deleting_destructor(h):
    heap0 = h.heap_ptr
    old = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    try:
        log = h.alloc(0x20, bytes(0x20))
        _hook(h, FREE_BLOCK, b'\xFF\x05' + _dword(log)
              + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4) + b'\xC3')
        obj = h.alloc(0x20, bytes(0x20))
        state = [None]

        def write():
            h.uc.mem_write(obj, struct.pack('<6I', TABLE_GET_VTABLE, 0, 0x1234, 1, 0, 1))

        for flags in (0, 1, 2, 3):
            def setup(h):
                state[0] = _state(h)
                _push_numbers(h, state[0], 3)
                h.uc.mem_write(log, bytes(0x20))
                write()

            diffs = h.compare(TABLE_GET_DELETE, args=(flags,), regs={UC_X86_REG_ECX: obj},
                              setup=setup, ret=None)
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            setup(h)
            res = h.call(TABLE_GET_DELETE, args=(flags,), regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['flags %d: returned %08X' % (flags, res['eax'])]
            if _u32(h, obj) != OBJECT_VTABLE or _u32(h, obj + 0xc) != 0:
                return ['flags %d: the read was not released (vtable %08X, count %d)'
                        % (flags, _u32(h, obj), _u32(h, obj + 0xc))]
            if _top(h, state[0]) != 2:
                return ['flags %d: top %d after the release' % (flags, _top(h, state[0]))]
            want = 1 if flags & 1 else 0
            if _u32(h, log) != want or (want and _u32(h, log + 4) != obj):
                return ['flags %d: the delete ran %d times for %08X'
                        % (flags, _u32(h, log), _u32(h, log + 4))]
        return None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old)
        _restore(h)
        h.heap_ptr = heap0


def test_handle_constructor(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, b'\xEE' * 0x20)
        diffs = h.compare(HANDLE_CTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return ['ctor: %s' % d for d in diffs]
        h.uc.mem_write(obj, b'\xEE' * 0x20)
        res = h.call(HANDLE_CTOR, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != obj:
            return ['returned %08X' % res['eax']]
        got = _fields(h, obj, 4)
        if got != (HANDLE_VTABLE, 0, 0, 0xEEEEEEEE):
            return ['fields (%08X, %08X, %08X, %08X), want (%08X, 0, 0, EEEEEEEE)'
                    % (got + (HANDLE_VTABLE,))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_handle_destructor(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x20, bytes(0x20))

        def write():
            h.uc.mem_write(obj, struct.pack('<4I', HANDLE_VTABLE, 0, 0x1234, 0x5678))

        write()
        diffs = h.compare(HANDLE_DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return ['dtor: %s' % d for d in diffs]
        write()
        res = h.call(HANDLE_DTOR, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        got = _fields(h, obj, 4)
        if got != (OBJECT_VTABLE, 0, 0x1234, 0x5678):
            return ['released as (%08X, %08X, %08X, %08X), want (%08X, 0, 1234, 5678)'
                    % (got + (OBJECT_VTABLE,))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0
