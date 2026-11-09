"""CUpdateObject::~CUpdateObject (0x00424E00): the vtable drops to the updater's, a parent is told through its
fifth slot, then the name and the CGameObject base go.  The CGameObject base sets 0x607D14 last."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

DTOR = 0x00424E00
UPDATE_VTABLE = 0x00607D5C
GAME_VTABLE = 0x00607D14
NAME = b'console'


def _setup(h, obj, parent=0):
    h.uc.mem_write(obj, bytes(0x38))
    h.uc.mem_write(obj, struct.pack('<II', 0x11223344, 0))      # vtable sentinel, a null owner
    h.uc.mem_write(obj + 0x0C, NAME + bytes(16 - len(NAME)))     # the name, small-string optimised
    h.uc.mem_write(obj + 0x1C, struct.pack('<II', len(NAME), 15))
    h.uc.mem_write(obj + 0x2C, struct.pack('<I', parent))


def _check(h, obj, parent):
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != GAME_VTABLE:
        return ['the CGameObject vtable is not at +0 after the destructor']
    if h.uc.mem_read(obj + 0x0C, len(NAME)) != NAME:
        return ['the name buffer was changed']
    if struct.unpack('<II', h.uc.mem_read(obj + 0x1C, 8)) != (len(NAME), 15):
        return ['the name size or capacity was changed']
    if struct.unpack('<I', h.uc.mem_read(obj + 0x2C, 4))[0] != parent:
        return ['the parent pointer was changed']
    return None


def test_update_object_dtor(h):
    obj = h.alloc(0x38, bytes(0x38))
    _setup(h, obj)
    diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return ['no parent: %s' % d for d in diffs]
    _setup(h, obj)
    res = h.call(DTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['no parent: replacement faulted: %s' % res['fault']]
    bad = _check(h, obj, 0)
    if bad:
        return ['no parent: %s' % d for d in bad]

    scratch = h.alloc(8, bytes(8))
    code = (b'\x8B\x44\x24\x04'                        # mov eax, [esp+4]  (the child)
            b'\xA3' + struct.pack('<I', scratch) +     # mov [scratch], eax
            b'\x89\x0D' + struct.pack('<I', scratch + 4) +   # mov [scratch+4], ecx  (the parent)
            b'\xC2\x04\x00')                           # ret 4
    stub = h.alloc(len(code), code)
    table = h.alloc(24, bytes(24))
    h.uc.mem_write(table + 20, struct.pack('<I', stub))
    parent = h.alloc(0x38, bytes(0x38))
    h.uc.mem_write(parent, struct.pack('<I', table))

    _setup(h, obj, parent)
    diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return ['parent: %s' % d for d in diffs]
    _setup(h, obj, parent)
    h.uc.mem_write(scratch, bytes(8))
    res = h.call(DTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['parent: replacement faulted: %s' % res['fault']]
    bad = _check(h, obj, parent)
    if bad:
        return ['parent: %s' % d for d in bad]
    if struct.unpack('<II', h.uc.mem_read(scratch, 8)) != (obj, parent):
        return ['parent: slot 5 got %r, want (child %08X, parent %08X)'
                % (struct.unpack('<II', h.uc.mem_read(scratch, 8)), obj, parent)]
    return None
