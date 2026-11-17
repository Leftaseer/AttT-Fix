"""The 35 Lua callback registrars share one template: resolve the class entry and globals,
call the registered callback through nScript::TableGet, then discard positive callback arguments."""
import struct

LUA_STATE_SLOT = 0x008D122C
GETITEM = 0x00402FD0
GETTOP = 0x00402A60
SETTOP = 0x00402AC0
TABLEGET_CTOR = 0x004277B0
TABLEGET_DTOR = 0x00427820
CALLBACK_RESULT = 0x89ABCDEF

FUNCTIONS = (
    0x00427A70, 0x00469CD0, 0x0047D1C0, 0x004B48D0, 0x004D1180, 0x004ED7D0,
    0x00564AF0, 0x00564D60, 0x00564FD0, 0x00565320, 0x00565590, 0x00565800,
    0x00565A70, 0x00565CE0, 0x00565F50, 0x005661C0, 0x00566430, 0x005666A0,
    0x00566910, 0x00566B80, 0x00566DF0, 0x00567060, 0x005672D0, 0x00567540,
    0x005677B0, 0x00567A20, 0x00567C90, 0x00567F00, 0x00568170, 0x00568650,
    0x005688C0, 0x00568B30, 0x00568DA0, 0x00569280, 0x005AD530,
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


def _fixture(h, top):
    log = h.alloc(0x60, bytes(0x60))
    state = h.alloc(0x20, bytes(0x20))
    entry = h.alloc(4, _dword(0x40))
    callback = _stub(h, b'\x89\x0D' + _dword(log + 0x20) + _inc(log + 0x24) +
                     b'\xB8' + _dword(CALLBACK_RESULT) + b'\xC2\x04\x00')
    globals_entry = h.alloc(16, struct.pack('<4I', 0x12345678, 0, callback, 0x20))
    h.uc.mem_write(LUA_STATE_SLOT, _dword(state))
    h.uc.mem_write(log + 0x28, _dword(top))

    getitem = (_arg(8, log + 4) + b'\x83\xF8\x01\x75\x0B' +
               b'\xA3' + _dword(log) + b'\xB8' + _dword(entry) + b'\xC3' +
               b'\xB8' + _dword(globals_entry) + b'\xC3')
    _hook(h, GETITEM, getitem)
    _hook(h, GETTOP, b'\xA1' + _dword(log + 0x28) + b'\xC3')
    _hook(h, TABLEGET_CTOR, _arg(4, log + 8) + _arg(8, log + 0x0c) +
          _arg(12, log + 0x10) + _inc(log + 0x14) + b'\x8B\xC1\xC2\x0C\x00')
    _hook(h, TABLEGET_DTOR, _inc(log + 0x2c) + b'\xC3')
    _hook(h, SETTOP, _arg(8, log + 0x30) + _inc(log + 0x34) + b'\xC3')
    return log


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _check(h, fn, log, top):
    h.uc.mem_write(log + 0x2c, bytes(0x0c))
    h.uc.mem_write(log, bytes(0x28))
    result = h.call(fn)
    if result['fault']:
        return ['%08X: %s' % (fn, result['fault'])]
    expected_count = top - 1
    expected = (
        (0, 1, 'first stack index'),
        (4, -10003, 'globals stack index'),
        (8, 0x12345678, 'table handle'),
        (0x0c, expected_count, 'TableGet count'),
        (0x10, 0, 'TableGet ownership'),
        (0x14, 1, 'TableGet constructor calls'),
        (0x20, 0x60, 'callback object'),
        (0x24, 1, 'callback calls'),
        (0x2c, 1, 'TableGet destructor calls'),
        (0x30, 2 if expected_count > 0 else 0, 'cleanup stack index'),
        (0x34, max(expected_count, 0), 'cleanup calls'),
    )
    problems = []
    for offset, want, label in expected:
        got = _u32(h, log + offset)
        if got != want & 0xFFFFFFFF:
            problems.append('%08X: %s is %#x, want %#x' % (fn, label, got, want & 0xFFFFFFFF))
    if result['eax'] != CALLBACK_RESULT:
        problems.append('%08X: returned %#x, want %#x' % (fn, result['eax'], CALLBACK_RESULT))
    return problems


def _exercise(h, tops):
    heap0 = h.heap_ptr
    old_state = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    try:
        problems = []
        for top in tops:
            log = _fixture(h, top)
            for fn in FUNCTIONS:
                diffs = h.compare(fn, mem=False)
                if diffs:
                    problems += ['%08X top %d: %s' % (fn, top, d) for d in diffs]
                    continue
                problems += _check(h, fn, log, top)
        return problems or None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old_state)
        _restore(h)
        h.heap_ptr = heap0


def test_lua_callback_registrars(h):
    return _exercise(h, (4,))


def test_lua_callback_registrars_nonpositive_count(h):
    return _exercise(h, (1, 0))
