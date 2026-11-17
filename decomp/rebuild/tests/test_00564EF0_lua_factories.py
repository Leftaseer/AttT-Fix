"""Ten Lua object factories at 0x564EF0 through 0x5690C0; allocation, construction and Lua API calls
are recording stubs.  The owned TableGet is destroyed before the object is returned as userdata."""
import struct

LUA_STATE_SLOT = 0x008D122C
NEW = 0x005E3EAE
GETTOP = 0x00402A60
TABLEGET_CTOR = 0x004277B0
TABLEGET_DTOR = 0x00427820
NEWUSERDATA = 0x00403BF0
RAWGETI = 0x00403390
SETMETATABLE = 0x004036B0

SPECS = (
    (0x00564EF0, 0x41c, 0x008CF3E8, 0x00514AD0, 0x006C3410),
    (0x00565160, 0x110, 0x006CA838, 0x004F57A0, 0x006C2A2C),
    (0x00565720, 0x290, 0x008CF700, 0x005824A0, 0x006BF9A8),
    (0x00566AA0, 0x194, 0x008CFF40, 0x00583350, 0x006C68B4),
    (0x00567460, 0x2a8, 0x008D0360, 0x0050AF10, 0x006C32C8),
    (0x005676D0, 0x230, 0x008D0468, 0x0051B940, 0x006C3504),
    (0x00567940, 0x374, 0x008D0570, 0x00532120, 0x006C1EA8),
    (0x00567BB0, 0x3ec, 0x008D0678, 0x005430C0, 0x006C4FD8),
    (0x00567E20, 0x198, 0x008D0780, 0x00472CB0, 0x006C1008),
    (0x005690C0, 0x0c4, 0x006CA210, 0x0047EE10, 0x006C146C),
)
saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _inc(log):
    return b'\xFF\x05' + _dword(log)


def _fixture(h, allocation_succeeds):
    log = h.alloc(0x50, bytes(0x50))
    state = h.alloc(0x20, bytes(0x20))
    allocated = h.alloc(0x20, bytes(0x20))
    constructed = h.alloc(0x20, bytes(0x20))
    userdata = h.alloc(4, bytes(4))
    _patch(h, LUA_STATE_SLOT, _dword(state))
    h.uc.mem_write(log + 0x44, _dword(4))
    for i, spec in enumerate(SPECS):
        _patch(h, spec[2], _dword(0x700000 + i * 0x10))
        _patch(h, spec[4], _dword(0x5000 + i))

    _hook(h, NEW, _arg(4, log) + _inc(log + 4) +
          b'\xB8' + _dword(allocated if allocation_succeeds else 0) + b'\xC3')
    _hook(h, GETTOP, _inc(log + 8) + b'\xA1' + _dword(log + 0x44) + b'\xC3')
    _hook(h, TABLEGET_CTOR, _arg(4, log + 0x0c) + _arg(8, log + 0x10) +
          _arg(12, log + 0x14) + _inc(log + 0x18) + b'\x8B\xC1\xC2\x0C\x00')
    ctor = b'\x89\x0D' + _dword(log + 0x1c) + _inc(log + 0x20)
    ctor += b'\xB8' + _dword(constructed) + b'\xC2\x04\x00'
    for spec in SPECS:
        _hook(h, spec[3], ctor)
    _hook(h, TABLEGET_DTOR, _inc(log + 0x24) + b'\xC3')
    _hook(h, NEWUSERDATA, _arg(8, log + 0x28) + _inc(log + 0x2c) +
          b'\xB8' + _dword(userdata) + b'\xC3')
    _hook(h, RAWGETI, _arg(8, log + 0x30) + _arg(12, log + 0x34) + _inc(log + 0x38) + b'\xC3')
    _hook(h, SETMETATABLE, _arg(8, log + 0x3c) + _inc(log + 0x40) + b'\x33\xC0\xC3')
    return log, allocated, constructed, userdata


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _check(h, spec, index, fixture, allocation_succeeds):
    fn, size, _, _, _ = spec
    log, allocated, constructed, userdata = fixture
    h.uc.mem_write(log, bytes(0x44))
    h.uc.mem_write(userdata, _dword(0xA5A5A5A5))
    result = h.call(fn)
    if result['fault']:
        return ['%08X: %s' % (fn, result['fault'])]
    expected_object = constructed if allocation_succeeds else 0
    expected = (
        (0, size, 'allocation size'),
        (4, 1, 'allocation calls'),
        (8, int(allocation_succeeds), 'gettop calls'),
        (0x0c, 0x700000 + index * 0x10 if allocation_succeeds else 0, 'table handle'),
        (0x10, 3 if allocation_succeeds else 0, 'TableGet count'),
        (0x14, 1 if allocation_succeeds else 0, 'TableGet ownership'),
        (0x18, int(allocation_succeeds), 'TableGet constructor calls'),
        (0x1c, allocated if allocation_succeeds else 0, 'object constructor object'),
        (0x20, int(allocation_succeeds), 'object constructor calls'),
        (0x24, int(allocation_succeeds), 'TableGet destructor calls'),
        (0x28, 4, 'userdata size'),
        (0x2c, 1, 'userdata calls'),
        (0x30, -10000, 'registry index'),
        (0x34, 0x5000 + index, 'metatable reference'),
        (0x38, 1, 'rawgeti calls'),
        (0x3c, -2, 'setmetatable index'),
        (0x40, 1, 'setmetatable calls'),
    )
    problems = []
    for offset, want, label in expected:
        got = _u32(h, log + offset)
        if got != want & 0xFFFFFFFF:
            problems.append('%08X: %s is %#x, want %#x' % (fn, label, got, want & 0xFFFFFFFF))
    if result['eax'] != 1:
        problems.append('%08X: returned %d, want 1' % (fn, result['eax']))
    if _u32(h, userdata) != expected_object:
        problems.append('%08X: userdata is %#x, want %#x' % (fn, _u32(h, userdata), expected_object))
    return problems


def _exercise(h, allocation_succeeds):
    heap0 = h.heap_ptr
    try:
        fixture = _fixture(h, allocation_succeeds)
        problems = []
        for i, spec in enumerate(SPECS):
            diffs = h.compare(spec[0], mem=False)
            if diffs:
                problems += ['%08X: %s' % (spec[0], d) for d in diffs]
                continue
            problems += _check(h, spec, i, fixture, allocation_succeeds)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_lua_object_factories(h):
    return _exercise(h, True)


def test_lua_object_factories_allocation_failure(h):
    return _exercise(h, False)
