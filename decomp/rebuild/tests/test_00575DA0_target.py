"""nSpell::Target::vf28 (0x00575DA0): stops the name effect on the target, adds 100 to its +0xA8, registers and
announces the spell, looks Spell.Spell[name] up (its instance goes to +0x70) and calls its Begin, creates the
"PSMesh"/"PSDetMesh" particle meshes at 2*(+0xB4)+11 above the target's unit and stores them in +0x74/+0x78, then links
two callback nodes.  The engine helpers are replaced by small code stubs that record their arguments."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

TARGET = 0x00575DA0
STOP = 0x0051E730
REGISTER = 0x0051EDD0
ANNOUNCE = 0x00562A50
ROOT = 0x005608F0
INDEX = 0x00561830
METHOD = 0x005626D0
CALL = 0x0055F400
INSTANCE = 0x0042F160
MESH_NAME = 0x00575B80
MESH_CTOR = 0x00571AA0

GLOBAL_LIST = 0x006CA8E0
NODE_VTABLE = 0x0061D734
NODE_METHOD_GLOBAL = 0x00575AD0
NODE_METHOD_TARGET = 0x005724E0
DESC = 0x11223344

LOG_ED_THIS = 0x00
LOG_ED_ARG = 0x04
LOG_ANNOUNCE = 0x08
LOG_CALL_FN = 0x0C
LOG_METHOD_THIS = 0x10
LOG_MESH_COUNT = 0x14
LOG_NAME_COUNT = 0x18
LOG_NAMES = 0x20          # 2 * (this, first 8 characters of the name)
LOG_MESH = 0x38           # 2 * (desc, unit, x, y, z, scene, mem)
LOG_SIZE = 0x80


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


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


def _ret16():
    return b'\xC2\x10\x00'


def _patch(h, address, code, saved):
    if address not in saved:
        saved[address] = bytes(h.uc.mem_read(address, 32))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stubs(h, log, root, obj, fn, scene):
    _patch(h, STOP, b'\x33\xC0' + _ret4(), _stubs.saved)
    _patch(h, REGISTER, _store_ecx(log + LOG_ED_THIS) + _mov_eax_arg(1) + _store_eax(log + LOG_ED_ARG)
           + _ret4(), _stubs.saved)
    _patch(h, ANNOUNCE, _mov_eax_arg(1) + _store_eax(log + LOG_ANNOUNCE) + b'\xC3', _stubs.saved)
    _patch(h, ROOT, _mov_eax(root) + b'\xC3', _stubs.saved)
    _patch(h, INDEX, _mov_eax(obj) + _ret4(), _stubs.saved)
    _patch(h, METHOD, _store_ecx(log + LOG_METHOD_THIS) + _mov_eax(fn) + _ret4(), _stubs.saved)
    _patch(h, CALL, _store_ecx(log + LOG_CALL_FN) + b'\x33\xC0\xC3', _stubs.saved)
    _patch(h, INSTANCE, _mov_eax(scene) + b'\xC3', _stubs.saved)
    _patch(h, MESH_NAME,
           _load_eax(log + LOG_NAME_COUNT)
           + b'\x6B\xD0\x0C'                           # imul edx,eax,12
           + b'\x81\xC2' + struct.pack('<I', log + LOG_NAMES)
           + b'\x89\x0A'                               # this
           + _mov_eax_arg(1)
           + b'\x8B\x48\x04' + b'\x89\x4A\x04'         # the inline string's first 8 characters
           + b'\x8B\x48\x08' + b'\x89\x4A\x08'
           + _inc(log + LOG_NAME_COUNT)
           + _mov_eax(DESC) + _ret4(), _stubs.saved)
    _patch(h, MESH_CTOR,
           b'\x53'                                     # push ebx
           + _load_eax(log + LOG_MESH_COUNT)
           + b'\x8B\xD8'                               # mov ebx,eax
           + b'\xC1\xE3\x05'                           # shl ebx,5
           + b'\x81\xC3' + struct.pack('<I', log + LOG_MESH)
           + _mov_eax_arg(2) + b'\x89\x03'             # desc
           + _mov_eax_arg(3) + b'\x89\x43\x04'         # unit
           + b'\x8B\x54\x24\x10'                       # pos
           + b'\x8B\x02' + b'\x89\x43\x08'
           + b'\x8B\x42\x04' + b'\x89\x43\x0C'
           + b'\x8B\x42\x08' + b'\x89\x43\x10'
           + _mov_eax_arg(5) + b'\x89\x43\x14'         # scene
           + b'\x89\x4B\x18'                           # the new object
           + b'\xC7\x41\x04\x00\x00\x00\x00'           # the base constructor zeroes the refcount
           + b'\x8B\xC1'                               # return it
           + _inc(log + LOG_MESH_COUNT)
           + b'\x5B' + _ret16(), _stubs.saved)


_stubs.saved = {}


def _object(h, refs):
    o = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(o, struct.pack('<II', 0, refs))
    return o


def _case(h, count, start_a8):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    root = h.alloc(0x10, bytes(0x10))
    a = _object(h, 1)
    fn = _object(h, 1)
    old_inst = _object(h, 2)
    old_mesh1 = _object(h, 2)
    old_mesh2 = _object(h, 2)
    scene = h.alloc(0x60, bytes(0x60))
    scene_obj = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(scene + 0x5c, struct.pack('<I', scene_obj))
    unit = h.alloc(0x100, bytes(0x100))
    target = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(target + 0xa4, struct.pack('<I', unit))
    h.uc.mem_write(target + 0xa8, struct.pack('<f', start_a8))
    h.uc.mem_write(target + 0xb4, struct.pack('<I', count))
    spell = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(spell + 0x64, struct.pack('<I', target))
    h.uc.mem_write(spell + 0x70, struct.pack('<I', old_inst))
    h.uc.mem_write(spell + 0x74, struct.pack('<I', old_mesh1))
    h.uc.mem_write(spell + 0x78, struct.pack('<I', old_mesh2))
    h.uc.mem_write(GLOBAL_LIST, bytes(4))
    _stubs(h, log, root, a, fn, scene)
    return {'log': log, 'a': a, 'fn': fn, 'old_inst': old_inst, 'old_mesh1': old_mesh1,
            'old_mesh2': old_mesh2, 'scene_obj': scene_obj, 'unit': unit, 'target': target, 'spell': spell}


def test_target_start(h):
    saved_global = bytes(h.uc.mem_read(GLOBAL_LIST, 4))
    _stubs.saved = {}
    heap0 = h.heap_ptr
    try:
        for count, start_a8, want_y in ((4, 500.0, 19.0), (0, -250.0, 11.0),
                                        (0xFFFFFFFF, 0.0, 8589934592.0)):
            s = _case(h, count, start_a8)
            diffs = h.compare(TARGET, regs={UC_X86_REG_ECX: s['spell']}, ret=None)
            if diffs:
                return ['count %d: %s' % (count, d) for d in diffs]
            res = h.call(TARGET, regs={UC_X86_REG_ECX: s['spell']})
            if res['fault']:
                return ['count %d: replacement faulted: %s' % (count, res['fault'])]
            log, spell = s['log'], s['spell']
            if _u32(h, spell + 0x6c) != 3:
                return ['count %d: +0x6C = %d' % (count, _u32(h, spell + 0x6c))]
            if _f32(h, s['target'] + 0xa8) != start_a8 + 100.0:
                return ['count %d: +0xA8 = %r' % (count, _f32(h, s['target'] + 0xa8))]
            if _u32(h, log + LOG_ED_THIS) != s['target'] or _u32(h, log + LOG_ED_ARG) != spell:
                return ['count %d: register called with %08X/%08X' % (count, _u32(h, log + LOG_ED_THIS),
                                                                     _u32(h, log + LOG_ED_ARG))]
            if _u32(h, log + LOG_ANNOUNCE) != spell + 8:
                return ['count %d: announced %08X' % (count, _u32(h, log + LOG_ANNOUNCE))]
            if _u32(h, spell + 0x70) != s['a'] or _u32(h, s['a'] + 4) != 2:
                return ['count %d: +0x70 = %08X (refs %d)' % (count, _u32(h, spell + 0x70), _u32(h, s['a'] + 4))]
            if _u32(h, log + LOG_METHOD_THIS) != s['a'] or _u32(h, log + LOG_CALL_FN) != s['fn']:
                return ['count %d: lookups/begin %08X/%08X' % (count, _u32(h, log + LOG_METHOD_THIS),
                                                              _u32(h, log + LOG_CALL_FN))]
            if _u32(h, s['fn'] + 4) != 1 or _u32(h, s['old_inst'] + 4) != 1:
                return ['count %d: refcounts fn %d old %d' % (count, _u32(h, s['fn'] + 4),
                                                             _u32(h, s['old_inst'] + 4))]
            if _u32(h, s['old_mesh1'] + 4) != 1 or _u32(h, s['old_mesh2'] + 4) != 1:
                return ['count %d: old mesh refcounts %d/%d' % (count, _u32(h, s['old_mesh1'] + 4),
                                                               _u32(h, s['old_mesh2'] + 4))]
            mesh1, mesh2 = _u32(h, spell + 0x74), _u32(h, spell + 0x78)
            if not mesh1 or not mesh2 or mesh1 == s['old_mesh1'] or mesh2 == s['old_mesh2']:
                return ['count %d: meshes %08X/%08X' % (count, mesh1, mesh2)]
            if _u32(h, mesh1 + 4) != 1 or _u32(h, mesh2 + 4) != 1:
                return ['count %d: mesh refcounts %d/%d' % (count, _u32(h, mesh1 + 4), _u32(h, mesh2 + 4))]
            if _u32(h, log + LOG_NAME_COUNT) != 2 or _u32(h, log + LOG_MESH_COUNT) != 2:
                return ['count %d: %d names, %d meshes' % (count, _u32(h, log + LOG_NAME_COUNT),
                                                          _u32(h, log + LOG_MESH_COUNT))]
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
            node = _u32(h, GLOBAL_LIST)
            if (not node or _u32(h, node) != NODE_VTABLE or _u32(h, node + 4) != 0
                    or _u32(h, node + 8) != spell or _u32(h, node + 12) != NODE_METHOD_GLOBAL):
                return ['count %d: global node %r' % (count, [hex(_u32(h, node + i)) for i in (0, 4, 8, 12)]
                                                      if node else None)]
            node = _u32(h, s['target'] + 0x18)
            if (not node or _u32(h, node) != NODE_VTABLE or _u32(h, node + 4) != 0
                    or _u32(h, node + 8) != spell or _u32(h, node + 12) != NODE_METHOD_TARGET):
                return ['count %d: target node %r' % (count, [hex(_u32(h, node + i)) for i in (0, 4, 8, 12)]
                                                      if node else None)]
            h.heap_ptr = heap0
    finally:
        h.uc.mem_write(GLOBAL_LIST, saved_global)
        for address, code in _stubs.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + 32)
        _stubs.saved = {}
        h.heap_ptr = heap0
    return None
