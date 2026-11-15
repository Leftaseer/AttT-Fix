"""The four method dispatchers (0x563900 String, 0x563950 LuaWrapper, 0x5639A0 CWorldHero, 0x5639F0 CBorder)
are the closures the wrapper tables fill: the method's number is the closure's upvalue(1), the call's single
argument (stack index 1) is the wrapper table and its [0] the light userdata passed as the method's this.
CWorldHero's table entries also carry an offset into the object.  The test builds the Lua call frame by hand
(a fake CClosure for upvalue(1), the wrapper table on the stack) and puts returning stubs into each method
table, then compares both halves of every dispatcher."""
import struct

NEWSTATE = 0x00402870
CREATETABLE = 0x004033D0
PUSHLIGHTUSERDATA = 0x004032A0
RAWSETI = 0x00403610
PUSHNIL = 0x00403080

# dispatch, its method function table, the entry stride, where in an entry the object offset lives (0 = none)
CASES = (
    (0x00563900, 0x00610490, 8, 0),
    (0x00563950, 0x0061CF04, 8, 0),
    (0x005639A0, 0x006C0AD0, 16, 4),
    (0x005639F0, 0x006C3964, 8, 0),
)

CONSTANT_STUB = b'\xb8\x11\x11\x11\x11\xc2\x04\x00'  # mov eax, 0x11111111; ret 4
THIS_STUB = b'\x8b\xc1\xc2\x04\x00'                  # mov eax, ecx; ret 4


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _call(h, entry, args=()):
    res = h.call(entry, args=args)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _state(h):
    state = _call(h, NEWSTATE)['eax']
    _call(h, CREATETABLE, (state, 0, 0))  # the wrapper table, at stack index 1
    return state


def _bind(h, state, object):
    _call(h, PUSHLIGHTUSERDATA, (state, object))
    _call(h, RAWSETI, (state, 1, 0))


def _fake_closure(h, state, method):
    """make the running call frame a C closure whose upvalue(1) is the number of the method"""
    closure = h.alloc(0x20, bytes(0x20))
    h.uc.mem_write(closure + 7, b'\1')                                # nupvalues
    h.uc.mem_write(closure + 0x14, struct.pack('<f', float(method)))  # upvalue[0]
    h.uc.mem_write(closure + 0x18, struct.pack('<I', 3))              # LUA_TNUMBER
    function = h.alloc(8, struct.pack('<II', closure, 6))             # LUA_TFUNCTION
    frame = _u32(h, state + 0x14)                                     # lua_State.ci
    h.uc.mem_write(frame + 4, struct.pack('<I', function))            # CallInfo.func


def test_method_dispatch(h):
    state = _state(h)
    object = h.alloc(0x40, bytes(0x40))
    _bind(h, state, object)
    constant = h.alloc(len(CONSTANT_STUB), CONSTANT_STUB)
    this_stub = h.alloc(len(THIS_STUB), THIS_STUB)

    for dispatch, base, stride, offset_slot in CASES:
        for method, stub in ((0, constant), (1, this_stub)):
            h.uc.mem_write(base + method * stride, struct.pack('<I', stub))
            if offset_slot:
                h.uc.mem_write(base + method * stride + offset_slot, struct.pack('<I', method * 0x20))
        for method in (0, 1):
            _fake_closure(h, state, method)
            diffs = h.compare(dispatch, args=(state,))
            if diffs:
                return ['%08X method %d: %s' % (dispatch, method, diff) for diff in diffs]
            want = 0x11111111 if method == 0 else object + (method * 0x20 if offset_slot else 0)
            eax = _call(h, h.to_rebuilt(dispatch), args=(state,))['eax']
            if eax != want:
                return ['%08X method %d returned %08X, want %08X' % (dispatch, method, eax, want)]

    # an empty [0] reaches the method as a null this
    _fake_closure(h, state, 1)
    _call(h, PUSHNIL, (state,))
    _call(h, RAWSETI, (state, 1, 0))
    diffs = h.compare(0x005639F0, args=(state,))
    if diffs:
        return ['CBorder with no wrapper object: %s' % diff for diff in diffs]
    if _call(h, h.to_rebuilt(0x005639F0), args=(state,))['eax'] != 0:
        return ['CBorder with no wrapper object passed a non-null this']
    return None
