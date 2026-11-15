"""nSpell::Invisible::vf28 (0x00572F70): stops the name effect on the target, subtracts 1000 from the target's +0xA8,
registers the spell, announces it, looks Spell.Spell[name] up and calls its Begin, then gives every unit of the target's
list a "PSMesh" particle mesh (named per unit by 0x00572D40) half its height above it and stores it in the matching
entry of the spell's +0x7C array, before linking a callback node on the global list.  The engine helpers are replaced by
small code stubs that record their arguments; the height helper keeps its real arithmetic on the unit fields."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

INVISIBLE = 0x00572F70
STOP = 0x0051E730
REGISTER = 0x0051EDD0
ANNOUNCE = 0x00562A50
ROOT = 0x005608F0
INDEX = 0x00561830
METHOD = 0x005626D0
CALL = 0x0055F400
INSTANCE = 0x0042F160
HEIGHT = 0x00511CD0
MESH_NAME = 0x00572D40
MESH_CTOR = 0x00571AA0

GLOBAL_LIST = 0x006CA8E0
NODE_VTABLE = 0x0061D2B4
NODE_METHOD_GLOBAL = 0x005745F0
DESC = 0x11223344

LOG_ED_THIS = 0x00
LOG_ED_ARG = 0x04
LOG_ANNOUNCE = 0x08
LOG_CALL_FN = 0x0C
LOG_MESH_COUNT = 0x10
LOG_NAME_COUNT = 0x14
LOG_NAMES = 0x18          # 4 * (this, index)
LOG_MESH = 0x38           # 4 * (desc, unit, x, y, z, scene, mem)
LOG_METHOD_THIS = 0xE0
LOG_SIZE = 0x100


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
    _patch(h, HEIGHT,
           b'\xD9\x81' + struct.pack('<I', 0x368)      # fld dword [ecx+0x368]
           + b'\xD8\xA1' + struct.pack('<I', 0x338)    # fsub dword [ecx+0x338]
           + b'\xC3', _stubs.saved)
    _patch(h, MESH_NAME,
           _load_eax(log + LOG_NAME_COUNT)
           + b'\x8B\xD0'                               # mov edx,eax
           + b'\xC1\xE2\x03'                           # shl edx,3
           + b'\x81\xC2' + struct.pack('<I', log + LOG_NAMES)
           + b'\x89\x0A'                               # this
           + _mov_eax_arg(1) + b'\x89\x42\x04'         # index
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


def _case(h, heights, start_a8):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    root = h.alloc(0x10, bytes(0x10))
    a = _object(h, 1)
    fn = _object(h, 1)
    old_inst = _object(h, 2)
    units = h.alloc(0x10, bytes(0x10))
    tables, old_meshes = [], []
    for i, (top, bottom) in enumerate(heights):
        u = h.alloc(0x400, bytes(0x400))
        h.uc.mem_write(u + 0x368, struct.pack('<f', top))
        h.uc.mem_write(u + 0x338, struct.pack('<f', bottom))
        h.uc.mem_write(units + 4 * i, struct.pack('<I', u))
        tables.append(u)
    target = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(target + 0x58, struct.pack('<I', units))
    h.uc.mem_write(target + 0x5c, struct.pack('<I', len(heights)))
    h.uc.mem_write(target + 0xa8, struct.pack('<f', start_a8))
    slots = h.alloc(0x10, bytes(0x10))
    for i in range(len(heights)):
        m = _object(h, 2)
        h.uc.mem_write(slots + 4 * i, struct.pack('<I', m))
        old_meshes.append(m)
    scene = h.alloc(0x60, bytes(0x60))
    scene_obj = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(scene + 0x5c, struct.pack('<I', scene_obj))
    spell = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(spell + 0x64, struct.pack('<I', target))
    h.uc.mem_write(spell + 0x74, struct.pack('<I', old_inst))
    h.uc.mem_write(spell + 0x7c, struct.pack('<I', slots))
    h.uc.mem_write(GLOBAL_LIST, bytes(4))
    _stubs(h, log, root, a, fn, scene)
    return {'log': log, 'a': a, 'fn': fn, 'old_inst': old_inst, 'units': tables, 'target': target,
            'slots': slots, 'old_meshes': old_meshes, 'scene_obj': scene_obj, 'spell': spell}


def test_invisible_start(h):
    saved_global = bytes(h.uc.mem_read(GLOBAL_LIST, 4))
    _stubs.saved = {}
    heap0 = h.heap_ptr
    try:
        cases = ((3, [(5.0, 1.0), (8.0, 2.0), (1.5, 0.5)], 500.0, -500.0),
                 (0, [], 250.0, -750.0),
                 (1, [(3.0, 3.0)], -250.0, -1250.0))
        for n, heights, start_a8, want_a8 in cases:
            s = _case(h, heights, start_a8)
            diffs = h.compare(INVISIBLE, regs={UC_X86_REG_ECX: s['spell']}, ret=None)
            if diffs:
                return ['units %d: %s' % (n, d) for d in diffs]
            res = h.call(INVISIBLE, regs={UC_X86_REG_ECX: s['spell']})
            if res['fault']:
                return ['units %d: replacement faulted: %s' % (n, res['fault'])]
            log, spell = s['log'], s['spell']
            if _u32(h, spell + 0x68) != 3:
                return ['units %d: +0x68 = %d' % (n, _u32(h, spell + 0x68))]
            if _f32(h, s['target'] + 0xa8) != want_a8:
                return ['units %d: +0xA8 = %r, want %r' % (n, _f32(h, s['target'] + 0xa8), want_a8)]
            if _u32(h, log + LOG_ED_THIS) != s['target'] or _u32(h, log + LOG_ED_ARG) != spell:
                return ['units %d: register called with %08X/%08X' % (n, _u32(h, log + LOG_ED_THIS),
                                                                     _u32(h, log + LOG_ED_ARG))]
            if _u32(h, log + LOG_ANNOUNCE) != spell + 8:
                return ['units %d: announced %08X' % (n, _u32(h, log + LOG_ANNOUNCE))]
            if _u32(h, log + LOG_METHOD_THIS) != s['a'] or _u32(h, log + LOG_CALL_FN) != s['fn']:
                return ['units %d: lookups/begin %08X/%08X' % (n, _u32(h, log + LOG_METHOD_THIS),
                                                              _u32(h, log + LOG_CALL_FN))]
            if _u32(h, spell + 0x74) != s['a'] or _u32(h, s['a'] + 4) != 2:
                return ['units %d: +0x74 = %08X (refs %d)' % (n, _u32(h, spell + 0x74), _u32(h, s['a'] + 4))]
            if _u32(h, s['fn'] + 4) != 1 or _u32(h, s['old_inst'] + 4) != 1:
                return ['units %d: refcounts fn %d old %d' % (n, _u32(h, s['fn'] + 4),
                                                             _u32(h, s['old_inst'] + 4))]
            if _u32(h, log + LOG_NAME_COUNT) != n or _u32(h, log + LOG_MESH_COUNT) != n:
                return ['units %d: %d names, %d meshes' % (n, _u32(h, log + LOG_NAME_COUNT),
                                                          _u32(h, log + LOG_MESH_COUNT))]
            for i in range(n):
                at = log + LOG_NAMES + 8 * i
                if _u32(h, at) != spell or _u32(h, at + 4) != i + 1:
                    return ['units %d: name %d called with %08X/%d' % (n, i, _u32(h, at), _u32(h, at + 4))]
                rec = log + LOG_MESH + 0x20 * i
                desc, unit, px, py, pz, scene, mem = struct.unpack('<II3fII', h.uc.mem_read(rec, 0x1C))
                want_y = 0.5 * (heights[i][0] - heights[i][1])
                if desc != DESC or unit != s['units'][i] or scene != s['scene_obj'] + 4:
                    return ['units %d: mesh %d args %08X/%08X/%08X' % (n, i, desc, unit, scene)]
                if (px, py, pz) != (0.0, want_y, 0.0):
                    return ['units %d: mesh %d position %r' % (n, i, (px, py, pz))]
                if _u32(h, s['slots'] + 4 * i) != mem or _u32(h, mem + 4) != 1:
                    return ['units %d: mesh %d not stored (slot %08X, mem %08X, refs %d)'
                            % (n, i, _u32(h, s['slots'] + 4 * i), mem, _u32(h, mem + 4))]
                if _u32(h, s['old_meshes'][i] + 4) != 1:
                    return ['units %d: old mesh %d refcount %d' % (n, i, _u32(h, s['old_meshes'][i] + 4))]
            node = _u32(h, GLOBAL_LIST)
            if (not node or _u32(h, node) != NODE_VTABLE or _u32(h, node + 4) != 0
                    or _u32(h, node + 8) != spell or _u32(h, node + 12) != NODE_METHOD_GLOBAL):
                return ['units %d: global node %r' % (n, [hex(_u32(h, node + i)) for i in (0, 4, 8, 12)] if node
                                                      else None)]
            if _u32(h, spell + 0x7c) != s['slots']:
                return ['units %d: the mesh array changed' % (n,)]
            h.heap_ptr = heap0
    finally:
        h.uc.mem_write(GLOBAL_LIST, saved_global)
        for address, code in _stubs.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + 32)
        _stubs.saved = {}
        h.heap_ptr = heap0
    return None
