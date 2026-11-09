"""The SkinMeshObject lifetime: the two constructors (0x4C0FE0 / 0x4C1100), the destructor (0x4C11D0) and the
deleting destructor (0x4C12B0).

The base constructor/destructor, the model load (0x4C0240), the effect attach (0x4AB810), the draw-table range
destroy (0x4BE1C0) and the manager's deleting destructor are replaced with recording stubs while the tests run;
the std::string operator= behind the name copy is the MSVCP80 import the harness emulates.  The animation reset
0x4C0BF0 is real (it only needs a clip group), so the tests preset one."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x004C0FE0
CTOR_FROM_EFFECT = 0x004C1100
DTOR = 0x004C11D0
DELETING_DTOR = 0x004C12B0

BASE_CTOR = 0x00430850
BASE_DTOR = 0x00430460
LOAD_MODEL = 0x004C0240
SET_EFFECT = 0x004AB810
RANGE_DESTROY = 0x004BE1C0
MANAGER_FACTORY = 0x004C0EE0

MANAGER = 0x006CA488      # the animation manager pointer
COUNT = 0x006CA48C        # how many skin mesh objects exist
OWNER = 0x006CA490        # the manager the first object created
VFTABLE = 0x006112C4


def _body(h, code):
    area = h.alloc(len(code) + 4, bytes(len(code) + 4))
    h.uc.mem_write(area, code)
    return area


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _redirect(h, entry, body):
    saved = bytes(h.uc.mem_read(entry, 6))
    h.uc.mem_write(entry, b'\xe9' + struct.pack('<i', body - (entry + 5)))
    h.uc.ctl_remove_cache(entry, entry + 8)
    return saved


def _restore_code(h, entry, saved):
    h.uc.mem_write(entry, saved)
    h.uc.ctl_remove_cache(entry, entry + 8)


def _string(h, text):
    """a MSVC 2005 std::string in memory (28 bytes): allocator, buffer or pointer, size, capacity"""
    data = text.encode()
    p = h.alloc(28, bytes(28))
    if len(data) < 16:
        h.uc.mem_write(p + 4, data + b'\0' * (16 - len(data)))
        capacity = 15
    else:
        q = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(p + 4, struct.pack('<I', q))
        capacity = len(data)
    h.uc.mem_write(p + 0x14, struct.pack('<II', len(data), capacity))
    return p


def _string_text(h, p):
    size, capacity = struct.unpack('<II', h.uc.mem_read(p + 0x14, 8))
    ptr = p + 4 if capacity < 16 else _u32(h, p + 4)
    return bytes(h.uc.mem_read(ptr, size)).decode()


def _base_ctor_stub(h):
    return _body(h, b'\xc3')


def _base_dtor_stub(h, log):
    """slot 0: record self and return"""
    return _body(h, b'\xb8' + struct.pack('<I', log) + b'\x89\x08' + b'\xc3')


def _load_model_stub(h, log):
    """0x4C0240 (ECX manager, name, meshes, animation, drawTable; ret 0x10): record all five"""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x89\x08'                                 # mov [eax], ecx
            + b'\x8b\x4c\x24\x04' + b'\x89\x48\x04'       # name
            + b'\x8b\x4c\x24\x08' + b'\x89\x48\x08'       # &meshes
            + b'\x8b\x4c\x24\x0c' + b'\x89\x48\x0c'       # &animation
            + b'\x8b\x4c\x24\x10' + b'\x89\x48\x10'       # &drawTable
            + b'\xc2\x10\x00')                            # ret 0x10
    return _body(h, code)


def _set_effect_stub(h, log):
    """0x4AB810 (ECX self, name, create; ret 8): record (self, name, create)"""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x89\x08'                                 # mov [eax], ecx
            + b'\x8b\x4c\x24\x04' + b'\x89\x48\x04'       # name
            + b'\x8b\x4c\x24\x08' + b'\x89\x48\x08'       # create
            + b'\xc2\x08\x00')                            # ret 8
    return _body(h, code)


def _range_destroy_stub(h, log):
    """0x4BE1C0 (cdecl: begin, end, table, self): record"""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x8b\x4c\x24\x04' + b'\x89\x08'           # begin
            + b'\x8b\x4c\x24\x08' + b'\x89\x48\x04'       # end
            + b'\x8b\x4c\x24\x0c' + b'\x89\x48\x08'       # table
            + b'\x8b\x4c\x24\x10' + b'\x89\x48\x0c'       # self
            + b'\xc3')
    return _body(h, code)


def _manager_stub(h, log):
    """the animation manager's deleting destructor (ECX manager, flag; ret 4)"""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x89\x08'                                 # mov [eax], ecx
            + b'\x8b\x4c\x24\x04' + b'\x89\x48\x04'       # flag
            + b'\xc2\x04\x00')                            # ret 4
    return _body(h, code)


def _manager(h, stub):
    """a fake animation manager: its first vtable slot is the deleting destructor"""
    vtable = h.alloc(4, struct.pack('<I', stub))
    return h.alloc(4, struct.pack('<I', vtable))


def _animation(h, frame_count=7):
    """a clip group with one clip whose frame count ResetAnimation (0x4C0BF0) reads"""
    clip = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(clip + 8, struct.pack('<i', frame_count))
    clip_buffer = h.alloc(4, struct.pack('<I', clip))
    return h.alloc(0x10, struct.pack('<IIII', 0, clip_buffer, clip_buffer + 4, clip_buffer + 4))


def _object(h, animation=0, draw_begin=0, draw_end=0, mesh_begin=0):
    obj = h.alloc(0x248, bytes(0x248))
    h.uc.mem_write(obj + 0x1EC, struct.pack('<I', animation))
    if draw_begin:
        h.uc.mem_write(obj + 0x238, struct.pack('<I', 0x5A))
        h.uc.mem_write(obj + 0x23C, struct.pack('<III', draw_begin, draw_end, draw_end))
    if mesh_begin:
        h.uc.mem_write(obj + 0x1DC, struct.pack('<I', 0x5A))
        h.uc.mem_write(obj + 0x1E0, struct.pack('<III', mesh_begin, mesh_begin + 4, mesh_begin + 4))
    return obj


def _options(h):
    """the globals of the manager list"""
    h.uc.mem_write(COUNT, struct.pack('<i', 1))
    h.uc.mem_write(MANAGER, struct.pack('<I', 0x5EED0000))
    h.uc.mem_write(OWNER, bytes(4))


def _stub_common(h):
    log = {}
    log['base'] = h.alloc(4, bytes(4))
    log['base_ctor'] = _base_ctor_stub(h)
    log['base_dtor'] = _base_dtor_stub(h, log['base'])
    log['load'] = h.alloc(20, bytes(20))
    log['load_stub'] = _load_model_stub(h, log['load'])
    log['effect'] = h.alloc(12, bytes(12))
    log['effect_stub'] = _set_effect_stub(h, log['effect'])
    saved = {BASE_CTOR: _redirect(h, BASE_CTOR, log['base_ctor']),
             BASE_DTOR: _redirect(h, BASE_DTOR, log['base_dtor']),
             LOAD_MODEL: _redirect(h, LOAD_MODEL, log['load_stub']),
             SET_EFFECT: _redirect(h, SET_EFFECT, log['effect_stub'])}
    return log, saved


def _unstub(h, saved):
    for entry, code in saved.items():
        _restore_code(h, entry, code)


def test_init_skin_mesh_object(h):
    """0x4C0FE0 copies the name, joins the manager's list, loads the model and attaches the named effect."""
    log, saved = _stub_common(h)
    try:
        _options(h)
        name = _string(h, 'skmodel')
        effect = _string(h, 'fx')
        obj = _object(h, animation=_animation(h))
        diffs = h.compare(CTOR, args=[name, effect], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        res = h.call(CTOR, args=[name, effect], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != obj:
            return ['the constructor returned %#x, not %#x' % (res['eax'], obj)]
        if _u32(h, obj) != VFTABLE:
            return ['the vtable is %#x' % _u32(h, obj)]
        if _string_text(h, obj + 8) != 'skmodel':
            return ['the name is %r' % _string_text(h, obj + 8)]
        for off, what in ((0x1E0, 'mesh begin'), (0x1E4, 'mesh end'), (0x1E8, 'mesh limit'),
                          (0x23C, 'draw begin'), (0x240, 'draw end'), (0x244, 'draw limit')):
            if _u32(h, obj + off) != 0:
                return ['%s is %#x' % (what, _u32(h, obj + off))]
        if struct.unpack('<i', h.uc.mem_read(COUNT, 4))[0] != 2:
            return ['the object count is %d' % struct.unpack('<i', h.uc.mem_read(COUNT, 4))[0]]
        load = struct.unpack('<5I', h.uc.mem_read(log['load'], 20))
        if load != (0x5EED0000, name, obj + 0x1DC, obj + 0x1EC, obj + 0x238):
            return ['the model load got %r' % (load,)]
        got = struct.unpack('<3I', h.uc.mem_read(log['effect'], 12))
        if got != (obj, effect, 0):
            return ['the effect attach got %r' % (got,)]
        if _u32(h, obj + 0x1C8) != 7 or h.uc.mem_read(obj + 0x1D4, 1)[0] != 1:
            return ['the animation was not reset (frame count %d, animated %d)'
                    % (_u32(h, obj + 0x1C8), h.uc.mem_read(obj + 0x1D4, 1)[0])]
        return []
    finally:
        _unstub(h, saved)


def test_init_first_skin_mesh_object(h):
    """0x4C0FE0 creates the animation manager when this is the first object."""
    log = {}
    log['base_ctor'] = _base_ctor_stub(h)
    log['load'] = h.alloc(20, bytes(20))
    log['load_stub'] = _load_model_stub(h, log['load'])
    log['effect'] = h.alloc(12, bytes(12))
    log['effect_stub'] = _set_effect_stub(h, log['effect'])
    fresh = 0x7A7A0000
    factory = _body(h, b'\xb8' + struct.pack('<I', fresh) + b'\xc3')
    saved = {BASE_CTOR: _redirect(h, BASE_CTOR, log['base_ctor']),
             LOAD_MODEL: _redirect(h, LOAD_MODEL, log['load_stub']),
             SET_EFFECT: _redirect(h, SET_EFFECT, log['effect_stub']),
             MANAGER_FACTORY: _redirect(h, MANAGER_FACTORY, factory)}
    try:
        _options(h)
        h.uc.mem_write(COUNT, bytes(4))
        name = _string(h, 'skmodel')
        effect = _string(h, 'fx')
        obj = _object(h, animation=_animation(h))
        diffs = h.compare(CTOR, args=[name, effect], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        res = h.call(CTOR, args=[name, effect], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, MANAGER) != fresh:
            return ['the manager is %#x, not the created %#x' % (_u32(h, MANAGER), fresh)]
        if struct.unpack('<i', h.uc.mem_read(COUNT, 4))[0] != 1:
            return ['the object count is %d' % struct.unpack('<i', h.uc.mem_read(COUNT, 4))[0]]
        if struct.unpack('<5I', h.uc.mem_read(log['load'], 20))[0] != fresh:
            return ['the model load got manager %#x' % struct.unpack('<5I', h.uc.mem_read(log['load'], 20))[0]]
        return []
    finally:
        _unstub(h, saved)


def test_init_skin_mesh_object_from_effect(h):
    """0x4C1100 takes the effect name from the file name at +4 of the effect it is given."""
    log, saved = _stub_common(h)
    try:
        _options(h)
        name = _string(h, 'skmodel')
        source = h.alloc(32, bytes(32))
        file_name = _string(h, 'fx2')
        h.uc.mem_write(source + 4, bytes(h.uc.mem_read(file_name, 28)))
        obj = _object(h, animation=_animation(h))
        diffs = h.compare(CTOR_FROM_EFFECT, args=[name, source], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        res = h.call(CTOR_FROM_EFFECT, args=[name, source], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != obj:
            return ['the constructor returned %#x, not %#x' % (res['eax'], obj)]
        if _string_text(h, obj + 8) != 'skmodel':
            return ['the name is %r' % _string_text(h, obj + 8)]
        got = struct.unpack('<3I', h.uc.mem_read(log['effect'], 12))
        if got != (obj, source + 4, 0):
            return ['the effect attach got %r, not (%#x, %#x, 0)' % (got, obj, source + 4)]
        return []
    finally:
        _unstub(h, saved)


def test_destroy_skin_mesh_object(h):
    """0x4C11D0 clears the draw table through its range destroyer, frees both vectors and leaves the manager."""
    log = {}
    log['base'] = h.alloc(4, bytes(4))
    log['base_dtor'] = _base_dtor_stub(h, log['base'])
    log['range'] = h.alloc(16, bytes(16))
    log['range_stub'] = _range_destroy_stub(h, log['range'])
    saved = {BASE_DTOR: _redirect(h, BASE_DTOR, log['base_dtor']),
             RANGE_DESTROY: _redirect(h, RANGE_DESTROY, log['range_stub'])}
    try:
        _options(h)
        h.uc.mem_write(COUNT, struct.pack('<i', 2))
        draw = h.alloc(8, bytes(8))
        meshes = h.alloc(4, bytes(4))
        obj = _object(h, draw_begin=draw, draw_end=draw + 8, mesh_begin=meshes)
        diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        res = h.call(DTOR, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if struct.unpack('<i', h.uc.mem_read(COUNT, 4))[0] != 1:
            return ['the object count is %d' % struct.unpack('<i', h.uc.mem_read(COUNT, 4))[0]]
        if _u32(h, OWNER) != 0:
            return ['the manager was deleted before the last object']
        for off, what in ((0x1E0, 'mesh begin'), (0x1E4, 'mesh end'), (0x1E8, 'mesh limit'),
                          (0x23C, 'draw begin'), (0x240, 'draw end'), (0x244, 'draw limit')):
            if _u32(h, obj + off) != 0:
                return ['%s is %#x' % (what, _u32(h, obj + off))]
        got = struct.unpack('<4I', h.uc.mem_read(log['range'], 16))
        if got != (draw, draw + 8, obj + 0x238, obj):
            return ['the range destroyer got %r' % (got,)]
        if _u32(h, log['base']) != obj:
            return ['the base destructor got %#x, not %#x' % (_u32(h, log['base']), obj)]
        return []
    finally:
        _unstub(h, saved)


def test_destroy_last_skin_mesh_object(h):
    """0x4C11D0 deletes the animation manager with the last object."""
    log = {}
    log['base'] = h.alloc(4, bytes(4))
    log['base_dtor'] = _base_dtor_stub(h, log['base'])
    log['range'] = h.alloc(16, bytes(16))
    log['range_stub'] = _range_destroy_stub(h, log['range'])
    log['manager'] = h.alloc(8, bytes(8))
    log['manager_stub'] = _manager_stub(h, log['manager'])
    manager = _manager(h, log['manager_stub'])
    saved = {BASE_DTOR: _redirect(h, BASE_DTOR, log['base_dtor']),
             RANGE_DESTROY: _redirect(h, RANGE_DESTROY, log['range_stub'])}
    try:
        _options(h)
        h.uc.mem_write(COUNT, struct.pack('<i', 1))
        h.uc.mem_write(OWNER, struct.pack('<I', manager))
        obj = _object(h)
        diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        res = h.call(DTOR, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if struct.unpack('<i', h.uc.mem_read(COUNT, 4))[0] != 0:
            return ['the object count is %d' % struct.unpack('<i', h.uc.mem_read(COUNT, 4))[0]]
        if _u32(h, OWNER) != 0:
            return ['the manager pointer is %#x' % _u32(h, OWNER)]
        got = struct.unpack('<2I', h.uc.mem_read(log['manager'], 8))
        if got != (manager, 1):
            return ['the manager destructor got %r' % (got,)]
        return []
    finally:
        _unstub(h, saved)


def test_delete_skin_mesh_object(h):
    """0x4C12B0 runs the destructor and frees the object when the low flag bit is set."""
    log = {}
    log['base'] = h.alloc(4, bytes(4))
    log['base_dtor'] = _base_dtor_stub(h, log['base'])
    log['range'] = h.alloc(16, bytes(16))
    log['range_stub'] = _range_destroy_stub(h, log['range'])
    saved = {BASE_DTOR: _redirect(h, BASE_DTOR, log['base_dtor']),
             RANGE_DESTROY: _redirect(h, RANGE_DESTROY, log['range_stub'])}
    try:
        _options(h)
        h.uc.mem_write(COUNT, struct.pack('<i', 2))
        draw = h.alloc(8, bytes(8))
        obj = _object(h, draw_begin=draw, draw_end=draw + 8)
        for flags in (1, 0):
            diffs = h.compare(DELETING_DTOR, args=[flags], regs={UC_X86_REG_ECX: obj})
            if diffs:
                return diffs
            res = h.call(DELETING_DTOR, args=[flags], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['replacement faulted for flags %d: %s' % (flags, res['fault'])]
            if res['eax'] != obj:
                return ['the deleting destructor returned %#x, not %#x' % (res['eax'], obj)]
            if _u32(h, obj + 0x23C) != 0 or _u32(h, obj + 0x1E0) != 0:
                return ['the object was not cleared for flags %d' % flags]
        return []
    finally:
        _unstub(h, saved)
