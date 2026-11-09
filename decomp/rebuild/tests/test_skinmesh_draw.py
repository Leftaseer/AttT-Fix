"""The skin mesh draw path: the two sub-object walkers (0x4C0620 / 0x4C0680), the four SkinMeshObject entry
points (0x4C0DE0 / 0x4C0E30 / 0x4C0E60 / 0x4C0EA0), the frame tick (0x4C0B20) and the animation reset (0x4C0BF0).

The sub objects are fake vtable entries whose stubs record the call: the first slot stores (self, clips, frame,
second, first) and the third (self, clips, frame, first).  The draw table is the vector at +0x238: an 8-byte
entry per mesh plus a leading one, so sub object i uses entry i+1.  SetWorldTransform (0x4AC890) and
CRenderObject3D::Tick (0x4AC690) are replaced with recording stubs while the tests run (both are original code
shared by the two runs)."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

DRAW4 = 0x004C0620
DRAW3 = 0x004C0680
TICK = 0x004C0B20
RESET = 0x004C0BF0
DRAW = 0x004C0DE0
DRAW_CURRENT = 0x004C0E30
DRAW3_WRAPPER = 0x004C0E60
DRAW_NOWORLD = 0x004C0EA0

SET_WORLD = 0x004AC890
BASE_TICK = 0x004AC690

PALETTE = [0, 2, 1, 1, 2, 3, 0, 4, 6, 0, 6, 2,
           0, 5, 4, 0, 1, 5, 7, 5, 1, 3, 7, 1,
           2, 6, 3, 3, 6, 7, 4, 5, 7, 4, 7, 6]


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


def _draw4_stub(h, log):
    """slot 1 (ret 0x10): (self, clips, frame, second, first) into 20-byte records after the count"""
    code = (b'\xb8' + struct.pack('<I', log)                  # mov eax, log
            + b'\x8b\x10'                                     # mov edx, [eax]
            + b'\x6b\xd2\x14'                                 # imul edx, edx, 20
            + b'\x8d\x54\x10\x04'                             # lea edx, [eax+edx+4]
            + b'\x89\x0a'                                     # mov [edx], ecx        self
            + b'\x8b\x4c\x24\x04' + b'\x89\x4a\x04'           # clips
            + b'\x8b\x4c\x24\x08' + b'\x89\x4a\x08'           # frame
            + b'\x8b\x4c\x24\x0c' + b'\x89\x4a\x0c'           # second
            + b'\x8b\x4c\x24\x10' + b'\x89\x4a\x10'           # first
            + b'\xff\x00'                                     # inc dword [eax]
            + b'\xc2\x10\x00')                                # ret 0x10
    return _body(h, code)


def _draw3_stub(h, log):
    """slot 3 (ret 0xC): (self, clips, frame, first) into 16-byte records"""
    code = (b'\xb8' + struct.pack('<I', log)                  # mov eax, log
            + b'\x8b\x10'                                     # mov edx, [eax]
            + b'\xc1\xe2\x04'                                 # shl edx, 4
            + b'\x8d\x54\x10\x04'                             # lea edx, [eax+edx+4]
            + b'\x89\x0a'                                     # mov [edx], ecx        self
            + b'\x8b\x4c\x24\x04' + b'\x89\x4a\x04'           # clips
            + b'\x8b\x4c\x24\x08' + b'\x89\x4a\x08'           # frame
            + b'\x8b\x4c\x24\x0c' + b'\x89\x4a\x0c'           # first
            + b'\xff\x00'                                     # inc dword [eax]
            + b'\xc2\x0c\x00')                                # ret 0xC
    return _body(h, code)


def _logs(h):
    log4 = h.alloc(4 + 8 * 20, bytes(4 + 8 * 20))
    log3 = h.alloc(4 + 8 * 16, bytes(4 + 8 * 16))
    return log4, log3


def _entries(h, log, stride):
    count = _u32(h, log)
    out = []
    for i in range(count):
        out.append(struct.unpack_from('<%dI' % (stride // 4), h.uc.mem_read(log + 4 + i * stride, stride)))
    return out


def _clear_log(h, log, size):
    h.uc.mem_write(log, bytes(size))


def _sub_object(h, stub4, stub3):
    idle = _body(h, b'\xc3')
    vtable = h.alloc(16, struct.pack('<IIII', idle, stub4, idle, stub3))
    return h.alloc(4, struct.pack('<I', vtable))


def _mesh(h, objects):
    mesh = h.alloc(0x74, bytes(0x74))
    buf = h.alloc(4 * len(objects), b''.join(struct.pack('<I', o) for o in objects))
    h.uc.mem_write(mesh + 4, struct.pack('<I', 0x5A))
    h.uc.mem_write(mesh + 8, struct.pack('<III', buf, buf + 4 * len(objects), buf + 4 * len(objects)))
    return mesh


def _table(h, entries):
    """entries: (first, second); the callers pass the table itself (allocator + begin/end/limit)"""
    buf = h.alloc(8 * len(entries), b''.join(struct.pack('<II', a, b) for a, b in entries))
    return h.alloc(0x10, struct.pack('<IIII', 0x5A, buf, buf + 8 * len(entries), buf + 8 * len(entries)))


def _object(h, meshes, table, clips=0xC0DE, frame=5, fallback=0xBEEF, count=None, current=1,
            frame_count=3, animated=1):
    obj = h.alloc(0x248, bytes(0x248))
    n = len(meshes) if count is None else count
    buf = h.alloc(4 * len(meshes), b''.join(struct.pack('<I', m) for m in meshes))
    h.uc.mem_write(obj + 0x3C, struct.pack('<I', fallback))
    h.uc.mem_write(obj + 0x1C8, struct.pack('<i', frame_count))
    h.uc.mem_write(obj + 0x1CC, struct.pack('<I', n))
    h.uc.mem_write(obj + 0x1D0, struct.pack('<I', current))
    h.uc.mem_write(obj + 0x1D4, bytes((animated,)))
    h.uc.mem_write(obj + 0x1D8, struct.pack('<I', frame))
    h.uc.mem_write(obj + 0x1DC, struct.pack('<I', 0x5A) + struct.pack('<III', buf, buf + 4 * len(meshes),
                                                                     buf + 4 * len(meshes)))
    h.uc.mem_write(obj + 0x1EC, struct.pack('<I', clips))
    h.uc.mem_write(obj + 0x238, struct.pack('<I', 0x5A) + struct.pack('<III', table[0], table[1], table[2]))
    return obj


def _draw_table_parts(h, entries):
    buf = h.alloc(8 * len(entries), b''.join(struct.pack('<II', a, b) for a, b in entries))
    return buf, buf + 8 * len(entries), buf + 8 * len(entries)


def _scene(h):
    """two sub objects and one mesh around them, a three-entry draw table (a header and one entry per mesh)"""
    log4, log3 = _logs(h)
    stub4 = _draw4_stub(h, log4)
    stub3 = _draw3_stub(h, log3)
    obj_a = _sub_object(h, stub4, stub3)
    obj_b = _sub_object(h, stub4, stub3)
    mesh = _mesh(h, [obj_a, obj_b])
    parts = _draw_table_parts(h, [(0xAAAA, 0xBBBB), (0x1111, 0x2222), (0x3333, 0)])
    return log4, log3, obj_a, obj_b, mesh, parts


def test_draw_sub_objects_ex(h):
    """0x4C0620 walks the sub objects with the entry after their own; a zero second value becomes the fallback."""
    log4, log3, obj_a, obj_b, mesh, parts = _scene(h)
    table = h.alloc(0x10, struct.pack('<I', 0x5A) + struct.pack('<III', *parts))
    diffs = h.compare(DRAW4, args=[0xC0DE, 7, table, 0xBEEF], regs={UC_X86_REG_ECX: mesh}, ret=None)
    if diffs:
        return diffs
    res = h.call(DRAW4, args=[0xC0DE, 7, table, 0xBEEF], regs={UC_X86_REG_ECX: mesh})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    entries = _entries(h, log4, 20)
    if entries != [(obj_a, 0xC0DE, 7, 0x2222, 0x1111), (obj_b, 0xC0DE, 7, 0xBEEF, 0x3333)]:
        return ['the draws were %r' % (entries,)]
    return []


def test_draw_sub_objects(h):
    """0x4C0680 calls the third slot with the first value of the entry after the sub object's own."""
    log4, log3, obj_a, obj_b, mesh, parts = _scene(h)
    table = h.alloc(0x10, struct.pack('<I', 0x5A) + struct.pack('<III', *parts))
    diffs = h.compare(DRAW3, args=[0xC0DE, 7, table], regs={UC_X86_REG_ECX: mesh}, ret=None)
    if diffs:
        return diffs
    res = h.call(DRAW3, args=[0xC0DE, 7, table], regs={UC_X86_REG_ECX: mesh})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    entries = _entries(h, log3, 16)
    if entries != [(obj_a, 0xC0DE, 7, 0x1111), (obj_b, 0xC0DE, 7, 0x3333)]:
        return ['the draws were %r' % (entries,)]
    return []


def test_skin_mesh_object_draw3(h):
    """0x4C0E60 clamps the index to the last mesh and draws it through the three-argument helper."""
    log4, log3, obj_a, obj_b, mesh, parts = _scene(h)
    mesh_b = _mesh(h, [obj_b])
    table = _draw_table_parts(h, [(0, 0), (0, 0), (0, 0)])
    obj = _object(h, [mesh, mesh_b], table)
    diffs = h.compare(DRAW3_WRAPPER, args=[9], regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(DRAW3_WRAPPER, args=[9], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    entries = _entries(h, log3, 16)
    if entries != [(obj_b, 0xC0DE, 5, 0)]:
        return ['the draws were %r' % (entries,)]
    return []


def test_skin_mesh_object_draw_current(h):
    """0x4C0E30 draws the current mesh (no clamping)."""
    log4, log3, obj_a, obj_b, mesh, parts = _scene(h)
    mesh_b = _mesh(h, [obj_b])
    table = _draw_table_parts(h, [(0, 0), (0x1111, 0), (0x3333, 0)])
    obj = _object(h, [mesh, mesh_b], table, current=1)
    diffs = h.compare(DRAW_CURRENT, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(DRAW_CURRENT, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    entries = _entries(h, log3, 16)
    if entries != [(obj_b, 0xC0DE, 5, 0x1111)]:
        return ['the draws were %r' % (entries,)]
    return []


def test_skin_mesh_object_draw_no_world(h):
    """0x4C0EA0 runs the four-argument helper without touching the world transform."""
    log4, log3, obj_a, obj_b, mesh, parts = _scene(h)
    mesh_b = _mesh(h, [obj_b])
    table = _draw_table_parts(h, [(0, 0), (0x1111, 0x2222), (0x3333, 0)])
    obj = _object(h, [mesh, mesh_b], table, fallback=0xBEEF)
    marker = h.alloc(4, bytes(4))
    stub = _body(h, b'\xc7\x05' + struct.pack('<I', marker) + b'\x01\x00\x00\x00' + b'\xc3')
    saved = _redirect(h, SET_WORLD, stub)
    try:
        diffs = h.compare(DRAW_NOWORLD, args=[0], regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        res = h.call(DRAW_NOWORLD, args=[0], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, marker) != 0:
            return ['the world transform was set']
        entries = _entries(h, log4, 20)
        if entries != [(obj_a, 0xC0DE, 5, 0x2222, 0x1111), (obj_b, 0xC0DE, 5, 0xBEEF, 0x3333)]:
            return ['the draws were %r' % (entries,)]
        return []
    finally:
        _restore_code(h, SET_WORLD, saved)


def test_skin_mesh_object_draw(h):
    """0x4C0DE0 clamps the index, sets the world transform and runs the four-argument helper."""
    log4, log3, obj_a, obj_b, mesh, parts = _scene(h)
    mesh_b = _mesh(h, [obj_b])
    table = _draw_table_parts(h, [(0, 0), (0x1111, 0x2222), (0x3333, 0)])
    obj = _object(h, [mesh, mesh_b], table, fallback=0xBEEF)
    marker = h.alloc(4, bytes(4))
    stub = _body(h, b'\xc7\x05' + struct.pack('<I', marker) + b'\x01\x00\x00\x00' + b'\xc3')
    saved = _redirect(h, SET_WORLD, stub)
    try:
        diffs = h.compare(DRAW, args=[9], regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        res = h.call(DRAW, args=[9], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, marker) != 1:
            return ['the world transform was not set']
        entries = _entries(h, log4, 20)
        if entries != [(obj_b, 0xC0DE, 5, 0x2222, 0x1111)]:
            return ['the draws were %r' % (entries,)]
        return []
    finally:
        _restore_code(h, SET_WORLD, saved)


def test_tick_skin_mesh_object(h):
    """0x4C0B20 advances the frame (wrapping exactly at the clip's count) when animated and passes EAX on."""
    log_eax = h.alloc(4, bytes(4))
    log_ecx = h.alloc(4, bytes(4))
    stub = _body(h, b'\xa3' + struct.pack('<I', log_eax)            # mov [log_eax], eax
                 + b'\x89\x0d' + struct.pack('<I', log_ecx)         # mov [log_ecx], ecx
                 + b'\xc3')
    saved = _redirect(h, BASE_TICK, stub)
    try:
        diffs = []
        cases = [((2, 3, 1), 0), ((3, 3, 1), 4), ((0xFFFFFFFF, -1, 1), 0), ((2, 3, 0), 2)]
        for (frame, count, animated), expected in cases:
            obj = h.alloc(0x1DC, bytes(0x1DC))
            h.uc.mem_write(obj + 0x1C8, struct.pack('<i', count))
            h.uc.mem_write(obj + 0x1D4, bytes((animated,)))
            h.uc.mem_write(obj + 0x1D8, struct.pack('<I', frame))
            diffs += h.compare(TICK, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x12345678}, ret=None)
            if diffs:
                return diffs
            res = h.call(TICK, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x12345678})
            if res['fault']:
                return ['replacement faulted for frame %#x/%d: %s' % (frame, count, res['fault'])]
            if _u32(h, obj + 0x1D8) != expected:
                diffs.append('frame %#x of %d became %#x, not %#x' % (frame, count, _u32(h, obj + 0x1D8), expected))
            if _u32(h, log_eax) != 0x12345678:
                diffs.append('the base tick got EAX %#x' % _u32(h, log_eax))
            if _u32(h, log_ecx) != obj:
                diffs.append('the base tick got ECX %#x, not %#x' % (_u32(h, log_ecx), obj))
            if diffs:
                return diffs
        return []
    finally:
        _restore_code(h, BASE_TICK, saved)


def test_reset_animation(h):
    """0x4C0BF0 takes the frame count from the first clip, counts the meshes, writes the bone table and restarts."""
    clip = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(clip + 8, struct.pack('<i', 7))
    clip_buf = h.alloc(4, struct.pack('<I', clip))
    group = h.alloc(0x10, struct.pack('<IIII', 0x5A, clip_buf, clip_buf + 4, clip_buf + 4))
    mesh_buf = h.alloc(8, struct.pack('<II', 0x11111111, 0x22222222))
    obj = h.alloc(0x248, b'\x5A' * 0x248)
    h.uc.mem_write(obj + 0x1C8, struct.pack('<i', -1))
    h.uc.mem_write(obj + 0x1CC, struct.pack('<I', 0xDEAD))
    h.uc.mem_write(obj + 0x1D0, struct.pack('<I', 9))
    h.uc.mem_write(obj + 0x1D4, b'\x00')
    h.uc.mem_write(obj + 0x1D8, struct.pack('<I', 9))
    h.uc.mem_write(obj + 0x1DC, struct.pack('<I', 0x5A) + struct.pack('<III', mesh_buf, mesh_buf + 8, mesh_buf + 8))
    h.uc.mem_write(obj + 0x1EC, struct.pack('<I', group))

    diffs = h.compare(RESET, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(RESET, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<i', h.uc.mem_read(obj + 0x1C8, 4))[0] != 7:
        return ['the frame count is %d' % struct.unpack('<i', h.uc.mem_read(obj + 0x1C8, 4))[0]]
    if _u32(h, obj + 0x1CC) != 2:
        return ['the mesh count is %d' % _u32(h, obj + 0x1CC)]
    if _u32(h, obj + 0x1D0) != 0:
        return ['the current mesh is %d' % _u32(h, obj + 0x1D0)]
    if _u32(h, obj + 0x1D8) != 0:
        return ['the frame is %d' % _u32(h, obj + 0x1D8)]
    if h.uc.mem_read(obj + 0x1D4, 1)[0] != 1:
        return ['the object is not animated']
    got = struct.unpack('<36H', h.uc.mem_read(obj + 0x1F0, 72))
    if list(got) != PALETTE:
        return ['the palette is %r' % (list(got),)]
    return []
