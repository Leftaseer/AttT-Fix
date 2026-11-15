"""The master module registration (luaclass.cpp): 0x56FE20 runs once per LuaModuleInit object (its +8 flag),
puts the four bindings the scripts use (String, LuaWrapper, CWorldHero, CBorder) into _G with their collector,
registers every class module by name and runs MainInit through 0x562A50.  The test stubs CLuaWrapper::DoFile
(0x432620) so the last step does not read the game's files, then checks the bindings and a class module."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C
NEWSTATE = 0x00402870
SETTOP = 0x00402A70
TYPE = 0x00402C20
GETFIELD = 0x00403300

DOFILE = 0x00432620
REGISTER = 0x0056FE20

LUA_GLOBALS = -10002
LUA_TTABLE = 5
LUA_TFUNCTION = 6

CLASS_FLAG = 0x006CA98C


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _call(h, entry, args=(), regs=None):
    res = h.call(entry, args=args, regs=regs)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _state(h):
    state = _call(h, NEWSTATE)['eax']
    h.uc.mem_write(LUA_STATE_SLOT, struct.pack('<I', state))
    return state


def _top(h, state):
    return _call(h, 0x00402A60, (state,))['eax']


def _stack_type(h, state, index):
    return _call(h, TYPE, (state, index))['eax']


def _getfield(h, state, index, name):
    _call(h, GETFIELD, (state, index, name))
    return _stack_type(h, state, -1)


def test_register_modules(h):
    state = _state(h)
    init = h.alloc(0x40, bytes(0x40))
    h.uc.mem_write(init, struct.pack('<III', 0x0061C5A4, 0, 1))

    # CLuaWrapper::DoFile reads the archive; a bare return (popping its thiscall argument) stands in for it
    stub = b'\xc2\x04\x00'
    entry = h.to_rebuilt(DOFILE)
    saved_orig = bytes(h.uc.mem_read(DOFILE, 3))
    saved_new = bytes(h.uc.mem_read(entry, 3))
    h.uc.mem_write(DOFILE, stub)
    h.uc.mem_write(entry, stub)
    try:
        diffs = h.compare(REGISTER, regs={UC_X86_REG_ECX: init}, ret=None)
        if diffs:
            return diffs

        _call(h, REGISTER, regs={UC_X86_REG_ECX: init})
    finally:
        h.uc.mem_write(DOFILE, saved_orig)
        h.uc.mem_write(entry, saved_new)

    if h.uc.mem_read(init + 8, 1) != b'\0':
        return ['the one-shot flag is still set']
    if _top(h, state) != 0:
        return ['top %d after the registration, want 0' % _top(h, state)]
    for name, addr in ((b'String\0', 0x00610484), (b'LuaWrapper\0', 0x0061CEF0),
                       (b'CWorldHero\0', 0x0060BF28), (b'CBorder\0', 0x00614A84)):
        key = h.alloc(len(name), name)
        if _getfield(h, state, LUA_GLOBALS, key) != LUA_TFUNCTION:
            return ['_G[%s] is not a function' % name.split(b'\0')[0].decode()]
        _call(h, SETTOP, (state, 0))
    for addr in (CLASS_FLAG, 0x008D0FC4, 0x006CAAC8, 0x008D0FC8):
        if _u32(h, addr) == 0:
            return ['the collector at %08X was not made' % addr]

    module = h.alloc(16, b'ParticleSystem\0')
    new_key = h.alloc(4, b'new\0')
    if _getfield(h, state, LUA_GLOBALS, module) != LUA_TTABLE:
        return ['_G[ParticleSystem] is not a table']
    if _getfield(h, state, -1, new_key) != LUA_TFUNCTION:
        return ['ParticleSystem has no "new"']
    _call(h, SETTOP, (state, 0))

    # the flag consumed: a second call registers nothing more
    _call(h, REGISTER, regs={UC_X86_REG_ECX: init})
    if _top(h, state) != 0:
        return ['top %d after the second call, want 0' % _top(h, state)]
    return None
