"""CGameObject::~CGameObject (0x00424C70): the vtable drops to CGameObject and an owner pointer would be an error
(only the clean path is exercised).  The vtable is 0x607D14."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

DTOR = 0x00424C70
VTABLE = 0x00607D14


def test_game_object_dtor(h):
    obj = h.alloc(8, struct.pack('<II', 0x11223344, 0))
    diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(DTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VTABLE:
        return ['the CGameObject vtable is not at +0']
    if struct.unpack('<I', h.uc.mem_read(obj + 4, 4))[0] != 0:
        return ['the destructor changed the owner pointer']
    return None
