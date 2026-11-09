"""CConsole::~CConsole (0x004427E0): the game folder, the 200 lines, the string at +0x3C and the updater go, and
the vtable ends on CSingleton's (0x60A2B8); the updater's own destructor leaves 0x607D14 in its slot."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

DTOR = 0x004427E0
SIZE = 0x1658
SINGLETON_VTABLE = 0x0060A2B8
UPDATE_VTABLE = 0x00607D5C
GAME_VTABLE = 0x00607D14


def _sso(h, addr, text):
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + bytes(16 - len(text)))
    h.uc.mem_write(addr + 0x14, struct.pack('<II', len(text), 15))


def _setup(h, obj):
    h.uc.mem_write(obj, bytes(SIZE))
    h.uc.mem_write(obj, struct.pack('<II', 0x11223344, 0x55667788))   # vtable sentinel, updater vtable sentinel
    _sso(h, obj + 0x0C, b'console')                                   # the updater's name
    _sso(h, obj + 0x3C, b'pending')                                   # the string at +0x3C
    _sso(h, obj + 0x58, b'first line')                                # lines[0]
    _sso(h, obj + 0x161C, b'last line')                               # lines[199]
    _sso(h, obj + 0x1638, b'D:\\Game\\')                              # the game folder


def _check(h, obj):
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != SINGLETON_VTABLE:
        return ['the CSingleton vtable is not at +0 after the destructor']
    if struct.unpack('<I', h.uc.mem_read(obj + 4, 4))[0] != GAME_VTABLE:
        return ['the updater was not destroyed (its vtable is %08X)'
                % struct.unpack('<I', h.uc.mem_read(obj + 4, 4))[0]]
    if struct.unpack('<I', h.uc.mem_read(obj + 8, 4))[0] != 0:
        return ['the updater owner is not null after the destructor']
    if h.uc.mem_read(obj + 0x163C, 8) != b'D:\\Game\\':
        return ['the game folder buffer was changed']
    if struct.unpack('<II', h.uc.mem_read(obj + 0x164C, 8)) != (8, 15):
        return ['the game folder size or capacity was changed']
    return None


def test_console_dtor(h):
    obj = h.alloc(SIZE, bytes(SIZE))
    _setup(h, obj)
    diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    _setup(h, obj)
    res = h.call(DTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    return _check(h, obj)
