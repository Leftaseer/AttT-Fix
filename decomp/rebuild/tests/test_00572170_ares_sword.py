"""nSpell::AresSword::vf28 (0x00572170): stops the name effect on the target, registers the spell (its turn count +0x6C
becomes 2), announces it, assigns SpellAct[name] to +0x74 and calls its Begin without results, creates the
"PSMesh"/"PSDetMesh" particle meshes at 2*(+0xB4)+11 above the target's unit into +0x80/+0x84, pushes three callback
nodes (target's +8, global list, target's +0x18) and destroys the script tables.  All script table helpers are replaced
by recording stubs; the mesh constructor is stubbed to record its arguments."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

ARES = 0x00572170
STOP = 0x0051E730
REGISTER = 0x0051EDD0
ANNOUNCE = 0x00562A50
TABLE_CTOR = 0x004323E0
LOOKUP = 0x00437870
ASSIGN = 0x0057A860
BEGIN_LOOKUP = 0x0057B770
BEGIN_CALL = 0x0057A180
DTOR_TABLE = 0x004220A0
DTOR_RESULT = 0x00427820
DTOR_METHOD = 0x004378D0
INSTANCE = 0x0042F160
MESH_NAME = 0x005720D0
MESH_CTOR = 0x00571AA0

GLOBAL_LIST = 0x006CA8E0
NODE_VTABLE = 0x0061D014
NODE_METHOD_TARGET8 = 0x00571DA0
NODE_METHOD_GLOBAL = 0x00575AD0
NODE_METHOD_TARGET18 = 0x005724E0
SPELLACT = 0x00613988
BEGIN = 0x006121B8
DESC = 0x11223344

LOG_ED_THIS = 0x00
LOG_ED_ARG = 0x04
LOG_ANNOUNCE = 0x08
LOG_TABLE_ARG = 0x0C
LOG_TABLE_ACT = 0x10
LOG_LOOKUP_NAME = 0x14
LOG_ASSIGN_SELF = 0x18
LOG_ASSIGN_SRC = 0x1C
LOG_BEGLOOK_SELF = 0x20
LOG_BEGLOOK_KEY = 0x24
LOG_BEGIN_SELF = 0x28
LOG_BEGIN_NRES = 0x2C
LOG_DTOR_A = 0x30        # first 0x004220A0 (the lookup result)
LOG_DTOR_D = 0x34        # second 0x004220A0 (the SpellAct table)
LOG_DTOR_B = 0x38        # 0x00427820 (the Begin result)
LOG_DTOR_C = 0x3C        # 0x004378D0 (the Begin method)
LOG_DTOR_COUNT = 0x40
LOG_NAME_COUNT = 0x44
LOG_NAMES = 0x48         # 2 * (this, first 8 characters of the name)
LOG_MESH_COUNT = 0x60
LOG_MESH = 0x64          # 2 * (desc, unit, x, y, z, scene, mem)
LOG_FLAG = 0xBC          # only record the stack addresses outside the comparison runs
LOG_SIZE = 0xC0


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _mov_eax(value):
    return b'\xB8' + struct.pack('<I', value)


def _mov_eax_arg(index):
    return b'\x8B\x44\x24' + bytes([4 * index])


def _store_eax(addr):
    return b'\xA3' + struct.pack('<I', addr)


def _store_ecx(addr):
    return b'\x89\x0D' + struct.pack('<I', addr)


def _load_eax(addr):
    return b'\xA1' + struct.pack('<I', addr)


def _inc(addr):
    return b'\xFF\x05' + struct.pack('<I', addr)


def _ret4():
    return b'\xC2\x04\x00'


def _ret8():
    return b'\xC2\x08\x00'


def _ret16():
    return b'\xC2\x10\x00'


def _patch(h, address, code, saved):
    if address not in saved:
        saved[address] = bytes(h.uc.mem_read(address, 32))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _gated(log, body):
    """run body only when the recording flag is set"""
    return (b'\x83\x3D' + struct.pack('<I', log + LOG_FLAG) + b'\x00'
            + b'\x74' + bytes([len(body)]) + body)


def _deref_ecx_into(log, slot):
    """store ECX into the next entry of a 4-byte array and count up"""
    return _gated(log, _load_eax(log + LOG_DTOR_COUNT)
                  + b'\x8B\xD0'                            # mov edx,eax
                  + b'\xC1\xE2\x02'                        # shl edx,2
                  + b'\x81\xC2' + struct.pack('<I', slot)
                  + b'\x89\x0A'                            # mov [edx],ecx
                  + _inc(log + LOG_DTOR_COUNT))


def _stubs(h, log, spell, scene):
    _stubs.log = log
    _patch(h, STOP, b'\x33\xC0' + _ret4(), _stubs.saved)
    _patch(h, REGISTER, _store_ecx(log + LOG_ED_THIS) + _mov_eax_arg(1) + _store_eax(log + LOG_ED_ARG)
           + _ret4(), _stubs.saved)
    _patch(h, ANNOUNCE, _mov_eax_arg(1) + _store_eax(log + LOG_ANNOUNCE) + b'\xC3', _stubs.saved)
    _patch(h, TABLE_CTOR, _gated(log, _store_ecx(log + LOG_TABLE_ACT) + _mov_eax_arg(1)
                                 + _store_eax(log + LOG_TABLE_ARG)) + _ret4(), _stubs.saved)
    _patch(h, LOOKUP, _mov_eax_arg(2) + _store_eax(log + LOG_LOOKUP_NAME) + b'\x33\xC0' + _ret8(), _stubs.saved)
    _patch(h, ASSIGN, _store_ecx(log + LOG_ASSIGN_SELF) + _mov_eax_arg(1) + _store_eax(log + LOG_ASSIGN_SRC)
           + _ret4(), _stubs.saved)
    _patch(h, BEGIN_LOOKUP, _store_ecx(log + LOG_BEGLOOK_SELF) + _mov_eax_arg(2) + _store_eax(log + LOG_BEGLOOK_KEY)
           + b'\x33\xC0' + _ret8(), _stubs.saved)
    _patch(h, BEGIN_CALL, _gated(log, _store_ecx(log + LOG_BEGIN_SELF) + _mov_eax_arg(2)
                                 + _store_eax(log + LOG_BEGIN_NRES)) + b'\x33\xC0' + _ret8(), _stubs.saved)
    _patch(h, DTOR_TABLE, _deref_ecx_into(log, log + LOG_DTOR_A) + b'\xC3', _stubs.saved)
    _patch(h, DTOR_RESULT, _gated(log, _store_ecx(log + LOG_DTOR_B)) + b'\xC3', _stubs.saved)
    _patch(h, DTOR_METHOD, _gated(log, _store_ecx(log + LOG_DTOR_C)) + b'\xC3', _stubs.saved)
    _patch(h, INSTANCE, _mov_eax(scene) + b'\xC3', _stubs.saved)
    _patch(h, MESH_NAME,
           _load_eax(log + LOG_NAME_COUNT)
           + b'\x6B\xD0\x0C'                            # imul edx,eax,12
           + b'\x81\xC2' + struct.pack('<I', log + LOG_NAMES)
           + b'\x89\x0A'                                # this
           + _mov_eax_arg(1)
           + b'\x8B\x48\x04' + b'\x89\x4A\x04'          # the inline string's first 8 characters
           + b'\x8B\x48\x08' + b'\x89\x4A\x08'
           + _inc(log + LOG_NAME_COUNT)
           + _mov_eax(DESC) + _ret4(), _stubs.saved)
    _patch(h, MESH_CTOR,
           b'\x53'                                      # push ebx
           + _load_eax(log + LOG_MESH_COUNT)
           + b'\x8B\xD8'                                # mov ebx,eax
           + b'\xC1\xE3\x05'                            # shl ebx,5
           + b'\x81\xC3' + struct.pack('<I', log + LOG_MESH)
           + _mov_eax_arg(2) + b'\x89\x03'              # desc
           + _mov_eax_arg(3) + b'\x89\x43\x04'          # unit
           + b'\x8B\x54\x24\x10'                        # pos
           + b'\x8B\x02' + b'\x89\x43\x08'
           + b'\x8B\x42\x04' + b'\x89\x43\x0C'
           + b'\x8B\x42\x08' + b'\x89\x43\x10'
           + _mov_eax_arg(5) + b'\x89\x43\x14'          # scene
           + b'\x89\x4B\x18'                            # the new object
           + b'\xC7\x41\x04\x00\x00\x00\x00'            # the base constructor zeroes the refcount
           + b'\x8B\xC1'                                # return it
           + _inc(log + LOG_MESH_COUNT)
           + b'\x5B' + _ret16(), _stubs.saved)


_stubs.saved = {}
_stubs.log = 0


def _object(h, refs):
    o = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(o, struct.pack('<II', 0, refs))
    return o


def _case(h, count):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    old_mesh1 = _object(h, 2)
    old_mesh2 = _object(h, 2)
    scene = h.alloc(0x60, bytes(0x60))
    scene_obj = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(scene + 0x5c, struct.pack('<I', scene_obj))
    unit = h.alloc(0x100, bytes(0x100))
    target = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(target + 0xa4, struct.pack('<I', unit))
    h.uc.mem_write(target + 0xb4, struct.pack('<I', count))
    spell = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(spell + 0x64, struct.pack('<I', target))
    h.uc.mem_write(spell + 0x74, bytes(4))
    h.uc.mem_write(spell + 0x80, struct.pack('<I', old_mesh1))
    h.uc.mem_write(spell + 0x84, struct.pack('<I', old_mesh2))
    h.uc.mem_write(GLOBAL_LIST, bytes(4))
    _stubs(h, log, spell, scene)
    return {'log': log, 'old_mesh1': old_mesh1, 'old_mesh2': old_mesh2, 'scene_obj': scene_obj,
            'unit': unit, 'target': target, 'spell': spell}


def test_ares_sword_start(h):
    saved_global = bytes(h.uc.mem_read(GLOBAL_LIST, 4))
    _stubs.saved = {}
    heap0 = h.heap_ptr
    try:
        for count, want_y in ((4, 19.0), (0, 11.0), (0xFFFFFFFF, 8589934592.0)):
            s = _case(h, count)
            diffs = h.compare(ARES, regs={UC_X86_REG_ECX: s['spell']}, ret=None)
            if diffs:
                return ['count %d: %s' % (count, d) for d in diffs]
            h.uc.mem_write(s['log'] + LOG_FLAG, struct.pack('<I', 1))
            res = h.call(ARES, regs={UC_X86_REG_ECX: s['spell']})
            if res['fault']:
                return ['count %d: replacement faulted: %s' % (count, res['fault'])]
            log, spell = s['log'], s['spell']
            if _u32(h, spell + 0x6c) != 2:
                return ['count %d: +0x6C = %d' % (count, _u32(h, spell + 0x6c))]
            if _u32(h, log + LOG_ED_THIS) != s['target'] or _u32(h, log + LOG_ED_ARG) != spell:
                return ['count %d: register called with %08X/%08X' % (count, _u32(h, log + LOG_ED_THIS),
                                                                     _u32(h, log + LOG_ED_ARG))]
            if _u32(h, log + LOG_ANNOUNCE) != spell + 8:
                return ['count %d: announced %08X' % (count, _u32(h, log + LOG_ANNOUNCE))]
            if _u32(h, log + LOG_TABLE_ARG) != SPELLACT or not _u32(h, log + LOG_TABLE_ACT):
                return ['count %d: SpellAct table %08X/%08X' % (count, _u32(h, log + LOG_TABLE_ACT),
                                                                _u32(h, log + LOG_TABLE_ARG))]
            if _u32(h, log + LOG_LOOKUP_NAME) != spell + 8:
                return ['count %d: lookup for %08X' % (count, _u32(h, log + LOG_LOOKUP_NAME))]
            if _u32(h, log + LOG_ASSIGN_SELF) != spell + 0x74:
                return ['count %d: assigned to %08X' % (count, _u32(h, log + LOG_ASSIGN_SELF))]
            if (_u32(h, log + LOG_BEGLOOK_SELF) != spell + 0x74 or _u32(h, log + LOG_BEGLOOK_KEY) != BEGIN
                    or _u32(h, log + LOG_BEGIN_NRES) != 0):
                return ['count %d: Begin lookup/call %08X/%08X/%d'
                        % (count, _u32(h, log + LOG_BEGLOOK_SELF), _u32(h, log + LOG_BEGLOOK_KEY),
                           _u32(h, log + LOG_BEGIN_NRES))]
            tmp1, tmp2, meth, act = (_u32(h, log + o) for o in (LOG_DTOR_A, LOG_DTOR_B, LOG_DTOR_C, LOG_DTOR_D))
            # both script results share the same temporary, destroyed by the two 0x004220A0 calls
            if _u32(h, log + LOG_DTOR_COUNT) != 2 or tmp1 != tmp2 or not tmp1 or not meth or not act:
                return ['count %d: the tables destroyed %08X/%08X/%08X/%08X (count %d)'
                        % (count, tmp1, tmp2, meth, act, _u32(h, log + LOG_DTOR_COUNT))]
            if tmp1 in (meth, act) or meth == act:
                return ['count %d: the table addresses repeat %08X/%08X/%08X/%08X' % (count, tmp1, tmp2, meth, act)]
            if _u32(h, log + LOG_NAME_COUNT) != 2 or _u32(h, log + LOG_MESH_COUNT) != 2:
                return ['count %d: %d names, %d meshes' % (count, _u32(h, log + LOG_NAME_COUNT),
                                                          _u32(h, log + LOG_MESH_COUNT))]
            mesh1, mesh2 = _u32(h, spell + 0x80), _u32(h, spell + 0x84)
            if not mesh1 or not mesh2 or mesh1 == s['old_mesh1'] or mesh2 == s['old_mesh2']:
                return ['count %d: meshes %08X/%08X' % (count, mesh1, mesh2)]
            if _u32(h, mesh1 + 4) != 1 or _u32(h, mesh2 + 4) != 1:
                return ['count %d: mesh refcounts %d/%d' % (count, _u32(h, mesh1 + 4), _u32(h, mesh2 + 4))]
            if _u32(h, s['old_mesh1'] + 4) != 1 or _u32(h, s['old_mesh2'] + 4) != 1:
                return ['count %d: old mesh refcounts %d/%d' % (count, _u32(h, s['old_mesh1'] + 4),
                                                               _u32(h, s['old_mesh2'] + 4))]
            for i, kind in enumerate((b'PSMesh\0\0', b'PSDetMes')):
                at = log + LOG_NAMES + 12 * i
                if _u32(h, at) != spell:
                    return ['count %d: name %d called on %08X' % (count, i, _u32(h, at))]
                if bytes(h.uc.mem_read(at + 4, 8)) != kind:
                    return ['count %d: name %d is %r' % (count, i, bytes(h.uc.mem_read(at + 4, 8)))]
                rec = log + LOG_MESH + 0x20 * i
                desc, unit, px, py, pz, scene, mem = struct.unpack('<II3fII', h.uc.mem_read(rec, 0x1C))
                if desc != DESC or unit != s['unit'] or scene != s['scene_obj'] + 4:
                    return ['count %d: mesh %d args %08X/%08X/%08X' % (count, i, desc, unit, scene)]
                if (px, py, pz) != (0.0, want_y, 0.0):
                    return ['count %d: mesh %d position %r' % (count, i, (px, py, pz))]
                if (mesh1, mesh2)[i] != mem:
                    return ['count %d: mesh %d is %08X, constructed %08X' % (count, i, (mesh1, mesh2)[i], mem)]
            for head, want, fn in ((s['target'] + 8, 0, NODE_METHOD_TARGET8),
                                   (GLOBAL_LIST, 0, NODE_METHOD_GLOBAL),
                                   (s['target'] + 0x18, 0, NODE_METHOD_TARGET18)):
                node = _u32(h, head)
                if (not node or _u32(h, node) != NODE_VTABLE or _u32(h, node + 4) != want
                        or _u32(h, node + 8) != spell or _u32(h, node + 12) != fn):
                    return ['count %d: node at %08X is %r' % (count, head, [hex(_u32(h, node + i))
                                                                           for i in (0, 4, 8, 12)] if node else None)]
            h.heap_ptr = heap0
    finally:
        h.uc.mem_write(GLOBAL_LIST, saved_global)
        for address, code in _stubs.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + 32)
        _stubs.saved = {}
        h.heap_ptr = heap0
    return None
