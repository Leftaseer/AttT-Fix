"""nSpell::Slow::vf28 (0x00574830): stops the name effect on the target, registers the spell, sends the target's
position and height to the scripts as CurStandardInfo, looks Spell.Spell[name] up and calls its Begin, creates the
"PSMesh"/"PSDetMesh" particle meshes at 2*(+0xB4)+11 and links the two callback nodes.  The engine helpers are
replaced by small code stubs: the script lookups return fixed refcounted objects, the mesh constructor records its
arguments, and the module logger records the sprintf text."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

SLOW = 0x00574830
STOP = 0x0051E730
REGISTER = 0x0051EDD0
LOG_CODE = 0x005608D0
ANNOUNCE = 0x00562A50
ROOT = 0x005608F0
INDEX = 0x00561830
METHOD = 0x005626D0
CALL = 0x0055F400
INSTANCE = 0x0042F160
MESH_NAME = 0x00574610
MESH_CTOR = 0x00571AA0

GLOBAL_LIST = 0x006CA8E0
NODE_VTABLE = 0x0061D5A0
NODE_METHOD_GLOBAL = 0x005745F0
NODE_METHOD_TARGET = 0x005724E0
SCRATCH = 0x005E3F96
DESC = 0x11223344

LOG = 0
LOG_ED_THIS = 0x00
LOG_ED_ARG = 0x04
LOG_ANNOUNCE = 0x08
LOG_BEGIN = 0x0C
LOG_KIND1 = 0x10
LOG_KIND2 = 0x18
LOG_DESC = 0x20
LOG_UNIT = 0x24
LOG_POS = 0x28
LOG_SCENE = 0x34
LOG_MESH_COUNT = 0x38
LOG_LEN = 0x3C
LOG_BUF = 0x40
LOG_FLAG = 0x44


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def _string(h, addr):
    size, capacity = struct.unpack('<II', h.uc.mem_read(addr + 0x14, 8))
    pointer = addr + 4 if capacity < 16 else _u32(h, addr + 4)
    return bytes(h.uc.mem_read(pointer, size))


def _mov_eax(value):
    return b'\xB8' + struct.pack('<I', value)


def _mov_ecx_arg(index):
    return b'\x8B\x4C\x24' + bytes([4 * index])


def _mov_eax_arg(index):
    return b'\x8B\x44\x24' + bytes([4 * index])


def _store_eax(addr):
    return b'\xA3' + struct.pack('<I', addr)


def _store_ecx(addr):
    return b'\x89\x0D' + struct.pack('<I', addr)


def _store_edx(addr):
    return b'\x89\x15' + struct.pack('<I', addr)


def _load_eax(addr):
    return b'\xA1' + struct.pack('<I', addr)


def _inc(addr):
    return b'\xFF\x05' + struct.pack('<I', addr)


def _ret4():
    return b'\xC2\x04\x00'


def _ret16():
    return b'\xC2\x10\x00'


PATCHED = (STOP, REGISTER, LOG_CODE, ANNOUNCE, ROOT, INDEX, METHOD, CALL, INSTANCE, MESH_NAME, MESH_CTOR, SCRATCH)


def _patch(h, address, code, saved):
    if address not in saved:
        saved[address] = bytes(h.uc.mem_read(address, 32))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stubs(h, log, root, obj, fn, scene, box):
    _patch(h, STOP, b'\x33\xC0' + _ret4(), _stubs.saved)
    _patch(h, REGISTER, _store_ecx(log + LOG_ED_THIS) + _mov_eax_arg(1) + _store_eax(log + LOG_ED_ARG)
           + _ret4(), _stubs.saved)
    _patch(h, ANNOUNCE, _mov_eax_arg(1) + _store_eax(log + LOG_ANNOUNCE) + b'\xC3', _stubs.saved)
    _patch(h, ROOT, _mov_eax(root) + b'\xC3', _stubs.saved)
    _patch(h, INDEX, _mov_eax(obj) + _ret4(), _stubs.saved)
    _patch(h, METHOD, _mov_eax(fn) + _ret4(), _stubs.saved)
    _patch(h, CALL, _store_ecx(log + LOG_BEGIN) + b'\x33\xC0\xC3', _stubs.saved)
    _patch(h, INSTANCE, _mov_eax(scene) + b'\xC3', _stubs.saved)
    _record_buffer(h, log)
    _patch(h, MESH_NAME,
           _inc(log + LOG_MESH_COUNT)
           + _load_eax(log + LOG_MESH_COUNT)
           + _mov_ecx_arg(1)
           + b'\x83\xC1\x04' + b'\x8B\x11' + b'\x8B\x49\x04'          # the inline string's first 8 characters
           + b'\x83\xF8\x01'
           + b'\x75\x0E'
           + _store_edx(log + LOG_KIND1) + _store_ecx(log + LOG_KIND1 + 4)
           + b'\xEB\x0C'
           + _store_edx(log + LOG_KIND2) + _store_ecx(log + LOG_KIND2 + 4)
           + _mov_eax(DESC) + _ret4(), _stubs.saved)
    _patch(h, MESH_CTOR,
           _mov_eax_arg(1) + _store_eax(log + LOG_DESC)
           + _mov_eax_arg(2) + _store_eax(log + LOG_UNIT)
           + b'\x8B\x54\x24\x0C'                                    # the position
           + b'\x8B\x02' + _store_eax(log + LOG_POS)
           + b'\x8B\x42\x04' + _store_eax(log + LOG_POS + 4)
           + b'\x8B\x42\x08' + _store_eax(log + LOG_POS + 8)
           + _mov_eax_arg(4) + _store_eax(log + LOG_SCENE)
           + b'\xC7\x41\x04\x00\x00\x00\x00'                       # the base constructor zeroes the refcount
           + b'\x8B\xC1' + _ret16(), _stubs.saved)
    _patch(h, SCRATCH, _mov_eax(box) + b'\xC3', _stubs.saved)


_stubs.saved = {}


def _record_buffer(h, log):
    """a variant of the logger that also records the sprintf buffer pointer"""
    _patch(h, LOG_CODE,
           _mov_eax_arg(1) + _mov_ecx_arg(2)
           + b'\x89\x0D' + struct.pack('<I', log + LOG_LEN)
           + b'\x83\x3D' + struct.pack('<I', log + LOG_FLAG) + b'\x00'
           + b'\x74\x05'
           + _store_eax(log + LOG_BUF)
           + b'\xC3', _stubs.saved)


def _object(h, refs):
    o = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(o, struct.pack('<II', 0, refs))
    return o


def _case(h, count):
    log = h.alloc(0x48, bytes(0x48))
    root = h.alloc(0x10, bytes(0x10))
    a = _object(h, 1)
    fn = _object(h, 1)
    old_inst = _object(h, 2)
    old_mesh1 = _object(h, 2)
    old_mesh2 = _object(h, 2)
    scene = h.alloc(0x60, bytes(0x60))
    scene_obj = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(scene + 0x5c, struct.pack('<I', scene_obj))
    box = h.alloc(0x38, bytes(0x38))
    h.uc.mem_write(box + 4, struct.pack('<f', 1.5))
    h.uc.mem_write(box + 0x34, struct.pack('<f', 4.0))
    vtable = h.alloc(0xF0, bytes(0xF0))
    mesh = h.alloc(8, bytes(8))
    h.uc.mem_write(vtable + 0xEC, struct.pack('<I', SCRATCH))
    h.uc.mem_write(mesh, struct.pack('<I', vtable))
    unit = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(unit + 0x64, struct.pack('<f', 1.25))
    h.uc.mem_write(unit + 0x68, struct.pack('<f', 2.5))
    h.uc.mem_write(unit + 0x6C, struct.pack('<f', 3.75))
    h.uc.mem_write(unit + 0x1E8, struct.pack('<I', mesh))
    target = h.alloc(0xC0, bytes(0xC0))
    h.uc.mem_write(target + 0xA4, struct.pack('<I', unit))
    h.uc.mem_write(target + 0xB4, struct.pack('<I', count))
    spell = h.alloc(0x90, bytes(0x90))
    h.uc.mem_write(spell + 0x64, struct.pack('<I', target))
    h.uc.mem_write(spell + 0x74, struct.pack('<I', old_inst))
    h.uc.mem_write(spell + 0x78, struct.pack('<I', old_mesh1))
    h.uc.mem_write(spell + 0x7C, struct.pack('<I', old_mesh2))
    h.uc.mem_write(GLOBAL_LIST, bytes(4))
    _stubs(h, log, root, a, fn, scene, box)
    return {'log': log, 'root': root, 'a': a, 'fn': fn, 'old_inst': old_inst, 'old_mesh1': old_mesh1,
            'old_mesh2': old_mesh2, 'scene': scene, 'scene_obj': scene_obj, 'unit': unit, 'target': target,
            'spell': spell}


def test_slow_start(h):
    saved_global = bytes(h.uc.mem_read(GLOBAL_LIST, 4))
    _stubs.saved = {}
    heap0 = h.heap_ptr
    try:
        for count, want_y in ((4, 19.0), (0, 11.0), (0xFFFFFFFF, 8589934592.0)):
            s = _case(h, count)
            diffs = h.compare(SLOW, regs={UC_X86_REG_ECX: s['spell']}, ret=None)
            if diffs:
                return ['count %d: %s' % (count, d) for d in diffs]
            h.uc.mem_write(s['log'] + LOG_FLAG, struct.pack('<I', 1))
            res = h.call(SLOW, regs={UC_X86_REG_ECX: s['spell']})
            if res['fault']:
                return ['count %d: replacement faulted: %s' % (count, res['fault'])]
            spell = s['spell']
            if _u32(h, spell + 0x68) != 3:
                return ['count %d: +0x68 = %d' % (count, _u32(h, spell + 0x68))]
            if _u32(h, spell + 0x74) != s['a']:
                return ['count %d: +0x74 = %08X, want %08X' % (count, _u32(h, spell + 0x74), s['a'])]
            if _u32(h, s['a'] + 4) != 2:
                return ['count %d: the table refcount is %d' % (count, _u32(h, s['a'] + 4))]
            if _u32(h, s['fn'] + 4) != 1 or _u32(h, s['old_inst'] + 4) != 1:
                return ['count %d: refcounts fn %d old %d' % (count, _u32(h, s['fn'] + 4),
                                                             _u32(h, s['old_inst'] + 4))]
            if _u32(h, s['old_mesh1'] + 4) != 1 or _u32(h, s['old_mesh2'] + 4) != 1:
                return ['count %d: old mesh refcounts %d/%d' % (count, _u32(h, s['old_mesh1'] + 4),
                                                               _u32(h, s['old_mesh2'] + 4))]
            mesh1, mesh2 = _u32(h, spell + 0x78), _u32(h, spell + 0x7C)
            if not mesh1 or not mesh2 or mesh1 == s['old_mesh1'] or mesh2 == s['old_mesh2']:
                return ['count %d: meshes %08X/%08X' % (count, mesh1, mesh2)]
            if _u32(h, mesh1 + 4) != 1 or _u32(h, mesh2 + 4) != 1:
                return ['count %d: mesh refcounts %d/%d' % (count, _u32(h, mesh1 + 4), _u32(h, mesh2 + 4))]

            log = s['log']
            if _u32(h, log + LOG_ED_THIS) != s['target'] or _u32(h, log + LOG_ED_ARG) != spell:
                return ['count %d: register called with %08X/%08X' % (count, _u32(h, log + LOG_ED_THIS),
                                                                     _u32(h, log + LOG_ED_ARG))]
            if _u32(h, log + LOG_ANNOUNCE) != spell + 8:
                return ['count %d: announced %08X' % (count, _u32(h, log + LOG_ANNOUNCE))]
            if _u32(h, log + LOG_BEGIN) != s['fn']:
                return ['count %d: Begin called on %08X' % (count, _u32(h, log + LOG_BEGIN))]
            if _u32(h, log + LOG_MESH_COUNT) != 2:
                return ['count %d: mesh constructor called %d times' % (count, _u32(h, log + LOG_MESH_COUNT))]
            if _u32(h, log + LOG_DESC) != DESC or _u32(h, log + LOG_UNIT) != s['unit']:
                return ['count %d: mesh args %08X/%08X' % (count, _u32(h, log + LOG_DESC),
                                                           _u32(h, log + LOG_UNIT))]
            if _u32(h, log + LOG_SCENE) != s['scene_obj'] + 4:
                return ['count %d: mesh scene %08X' % (count, _u32(h, log + LOG_SCENE))]
            got_pos = struct.unpack('<3f', h.uc.mem_read(log + LOG_POS, 12))
            if got_pos != (0.0, want_y, 0.0):
                return ['count %d: position %r, want (0, %r, 0)' % (count, got_pos, want_y)]
            if bytes(h.uc.mem_read(log + LOG_KIND1, 8)) != b'PSMesh\0\0':
                return ['count %d: first kind %r' % (count, bytes(h.uc.mem_read(log + LOG_KIND1, 8)))]
            if bytes(h.uc.mem_read(log + LOG_KIND2, 8)) != b'PSDetMes':
                return ['count %d: second kind %r' % (count, bytes(h.uc.mem_read(log + LOG_KIND2, 8)))]

            node = _u32(h, GLOBAL_LIST)
            if (not node or _u32(h, node) != NODE_VTABLE or _u32(h, node + 4) != 0
                    or _u32(h, node + 8) != spell or _u32(h, node + 12) != NODE_METHOD_GLOBAL):
                return ['count %d: global node %r' % (count, [hex(_u32(h, node + i)) for i in (0, 4, 8, 12)] if node
                                                       else None)]
            node = _u32(h, s['target'] + 0x18)
            if (not node or _u32(h, node) != NODE_VTABLE or _u32(h, node + 4) != 0
                    or _u32(h, node + 8) != spell or _u32(h, node + 12) != NODE_METHOD_TARGET):
                return ['count %d: target node %r' % (count, [hex(_u32(h, node + i)) for i in (0, 4, 8, 12)] if node
                                                      else None)]

            buf, size = _u32(h, log + LOG_BUF), _u32(h, log + LOG_LEN)
            text = bytes(h.uc.mem_read(buf, size))
            want = b'CurStandardInfo = { x = 1.25, y = 2.50, z = 3.75, height = 2.50 };'
            if text != want:
                return ['count %d: logged %r, want %r' % (count, text, want)]
            if h._cstr(buf) != want:
                return ['count %d: the logged text is not terminated' % (count,)]
            h.heap_ptr = heap0
    finally:
        h.uc.mem_write(GLOBAL_LIST, saved_global)
        for address, code in _stubs.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + 32)
        _stubs.saved = {}
        h.heap_ptr = heap0
    return None
