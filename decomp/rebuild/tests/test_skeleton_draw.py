"""CSkeletonMeshSubObject::Draw (0x4BA850): poses the skeleton from the animation set at the requested frame, skins
the vertices, binds the index and vertex buffers, sets the texture and draws every subset through the device.

The device singleton at 0x6C8C10 points at a fake device whose vtable slots log their arguments; the pose/skin
helpers and the vertex-buffer wrapper helpers are replaced with stubs too.  Every log record is eight dwords
(slot, then arguments).  The fake sub object carries one vector of 0x6C-byte subsets at +08, the track index at
+0xD4, the skin target at +0xD8, the vertex vector at +0xDC/+0xE0, the vertex buffer wrapper at +0xEC and the
index buffer at +0xFC."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

DRAW = 0x004BA850
POSE = 0x004B9110
SKIN = 0x004BA7F0
GET_VERTEX_BUFFER = 0x004BA550
END_VERTEX_BUFFER = 0x004BA4D0
DEVICE = 0x006C8C10

VB_HANDLE = 0xB000B000
END_RESULT = 0x1234

RECORD = 32


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


def _log_head(log):
    return (b'\xb8' + struct.pack('<I', log)                  # mov eax, log
            + b'\x8b\x10'                                     # mov edx, [eax]
            + b'\xc1\xe2\x05'                                 # shl edx, 5
            + b'\x8d\x54\x10\x04')                            # lea edx, [eax+edx+4]


def _std_stub(h, log, slot, nargs):
    """stdcall device method: records (slot, [dev], args...) and pops nargs arguments"""
    code = _log_head(log) + b'\xc7\x02' + struct.pack('<I', slot)
    for i in range(nargs):
        code += b'\x8b\x4c\x24' + bytes((4 + 4 * i,)) + b'\x89\x4a' + bytes((4 + 4 * i,))
    code += b'\xff\x00' + b'\xc2' + struct.pack('<H', nargs * 4)
    return _body(h, code)


def _this_stub(h, log, slot, nargs):
    """thiscall helper: records (slot, self, args...) and pops nargs arguments"""
    code = _log_head(log) + b'\xc7\x02' + struct.pack('<I', slot) + b'\x89\x4a\x04'
    for i in range(nargs):
        code += b'\x8b\x4c\x24' + bytes((4 + 4 * i,)) + b'\x89\x4a' + bytes((8 + 4 * i,))
    code += b'\xff\x00' + b'\xc2' + struct.pack('<H', nargs * 4)
    return _body(h, code)


def _records(h, log):
    count = _u32(h, log)
    return [struct.unpack('<8I', h.uc.mem_read(log + 4 + i * RECORD, RECORD)) for i in range(count)]


def _clear_log(h, log, size):
    h.uc.mem_write(log, bytes(size))


def _device(h, log):
    idle = _body(h, b'\xc3')
    vtable = h.alloc(0x1A4, struct.pack('<I', idle) * (0x1A4 // 4))
    for offset, nargs in ((0xC4, 2), (0x104, 3), (0x148, 7), (0x190, 5), (0x1A0, 2)):
        h.uc.mem_write(vtable + offset, struct.pack('<I', _std_stub(h, log, offset, nargs)))
    return h.alloc(4, struct.pack('<I', vtable))


def _texture(h, handle):
    idle = _body(h, b'\xc3')
    vtable = h.alloc(0x2C, struct.pack('<I', idle) * (0x2C // 4))
    h.uc.mem_write(vtable + 0x28, struct.pack('<I', _body(h, b'\xb8' + struct.pack('<I', handle) + b'\xc3')))
    return h.alloc(4, struct.pack('<I', vtable))


def _track(h, data, frame_count, stride):
    track = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(track, struct.pack('<IIII', data, 0, frame_count, stride))
    return track


def _animation_set(h, tracks):
    buf = h.alloc(4 * len(tracks), b''.join(struct.pack('<I', t) for t in tracks))
    return h.alloc(0xC, struct.pack('<III', 0x5A, buf, buf + 4 * len(tracks)))


def _skeleton(h, subsets, index=0, vertices=0, vertex_wrapper=0xD8D8D8D8, vertex_buffer=0xECECECEC,
              index_buffer=0xFCFCFCFC):
    """subsets: (texture, first index, triangle count); returns the object and the contiguous subset addresses"""
    obj = h.alloc(0x100, b'\x5A' * 0x100)
    buf = h.alloc(0x6C * len(subsets), bytes(0x6C * len(subsets)))
    subs = []
    for i, (tex, first, count) in enumerate(subsets):
        sub = buf + 0x6C * i
        h.uc.mem_write(sub, b'\x5A' * 0x6C)
        h.uc.mem_write(sub + 0x60, struct.pack('<I', tex))
        h.uc.mem_write(sub + 0x64, struct.pack('<H', first))
        h.uc.mem_write(sub + 0x68, struct.pack('<I', count))
        subs.append(sub)
    end = buf + 0x6C * len(subsets)
    h.uc.mem_write(obj + 8, struct.pack('<III', buf, end, end))
    h.uc.mem_write(obj + 0xD4, struct.pack('<I', index))
    h.uc.mem_write(obj + 0xD8, struct.pack('<I', vertex_wrapper))
    if vertices:
        h.uc.mem_write(obj + 0xDC, struct.pack('<II', 0x1000, 0x1000 + 32 * vertices))
    h.uc.mem_write(obj + 0xEC, struct.pack('<I', vertex_buffer))
    h.uc.mem_write(obj + 0xFC, struct.pack('<I', index_buffer))
    return obj, subs


def _setup(h):
    log = h.alloc(RECORD * 64, bytes(RECORD * 64))
    dev = _device(h, log)
    vb_cell = h.alloc(4, struct.pack('<I', VB_HANDLE))
    redirected = [(POSE, _this_stub(h, log, POSE, 1)),
                  (SKIN, _this_stub(h, log, SKIN, 1)),
                  (GET_VERTEX_BUFFER, _body(h, b'\xb8' + struct.pack('<I', vb_cell) + b'\xc3')),
                  (END_VERTEX_BUFFER, _body(h, b'\xb8' + struct.pack('<I', END_RESULT) + b'\xc3'))]
    saved = [(entry, _redirect(h, entry, body)) for entry, body in redirected]
    singleton = bytes(h.uc.mem_read(DEVICE, 4))
    h.uc.mem_write(DEVICE, struct.pack('<I', dev))

    def done():
        for entry, old in saved:
            _restore_code(h, entry, old)
        h.uc.mem_write(DEVICE, singleton)

    return log, dev, done


def _draw(h, obj, set_, frame, tex):
    return h.compare(DRAW, args=[set_, frame, tex], regs={UC_X86_REG_ECX: obj}, ret='eax')


def test_skeleton_draw_frame_and_buffers(h):
    """The pose reads the tile at the frame, the stream source uses the vertex buffer at 32 bytes a vertex, and the
    draw calls carry the vertex count from +0xDC..+0xE0 and each subset's own first index and triangle count."""
    log, dev, done = _setup(h)
    try:
        track = _track(h, 0xA000, 5, 3)
        set_ = _animation_set(h, [track])
        obj, (sub_a, sub_b) = _skeleton(h, [(0, 0, 3), (0, 6, 12)], vertices=7, index_buffer=0x11112222)
        diffs = _draw(h, obj, set_, 2, 0)
        if diffs:
            return diffs
        _clear_log(h, log, RECORD * 64)
        res = h.call(DRAW, args=[set_, 2, 0], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != END_RESULT:
            return ['the draw returned %#x' % res['eax']]
        expected = [
            (POSE, obj, 0xA000 + 3 * 2 * 0x18, 0, 0, 0, 0, 0),
            (SKIN, obj, obj + 0xD8, 0, 0, 0, 0, 0),
            (0x1A0, dev, 0x11112222, 0, 0, 0, 0, 0),
            (0x190, dev, 0, VB_HANDLE, 0, 0x20, 0, 0),
            (0xC4, dev, sub_a, 0, 0, 0, 0, 0),
            (0x148, dev, 4, 0, 0, 7, 0, 3),
            (0xC4, dev, sub_b, 0, 0, 0, 0, 0),
            (0x148, dev, 4, 0, 0, 7, 6, 12),
        ]
        got = _records(h, log)
        if got != expected:
            return ['the calls were %r' % (got,)]
        return []
    finally:
        done()


def test_skeleton_draw_frame_wraps(h):
    """A frame past the track's count poses the first frame."""
    log, dev, done = _setup(h)
    try:
        track = _track(h, 0xB000, 3, 2)
        set_ = _animation_set(h, [track])
        obj, _ = _skeleton(h, [(0, 0, 0)], vertices=1)
        diffs = _draw(h, obj, set_, 9, 0)
        if diffs:
            return diffs
        _clear_log(h, log, RECORD * 64)
        res = h.call(DRAW, args=[set_, 9, 0], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        got = _records(h, log)
        if not got or got[0] != (POSE, obj, 0xB000, 0, 0, 0, 0, 0):
            return ['the pose call was %r' % (got[:1],)]
        return []
    finally:
        done()


def test_skeleton_draw_uses_argument_texture(h):
    """With a texture argument the subsets' own textures are ignored and it is set once, before the materials."""
    log, dev, done = _setup(h)
    try:
        track = _track(h, 0xC000, 2, 1)
        set_ = _animation_set(h, [track])
        tex = _texture(h, 0x7777)
        obj, (sub_a, sub_b) = _skeleton(h, [(_texture(h, 0x5555), 0, 0),
                                            (_texture(h, 0x6666), 0, 0)], vertices=2)
        diffs = _draw(h, obj, set_, 1, tex)
        if diffs:
            return diffs
        _clear_log(h, log, RECORD * 64)
        res = h.call(DRAW, args=[set_, 1, tex], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        got = _records(h, log)
        expected = [
            (POSE, obj, 0xC000 + 1 * 0x18, 0, 0, 0, 0, 0),
            (SKIN, obj, obj + 0xD8, 0, 0, 0, 0, 0),
            (0x1A0, dev, 0xFCFCFCFC, 0, 0, 0, 0, 0),
            (0x190, dev, 0, VB_HANDLE, 0, 0x20, 0, 0),
            (0x104, dev, 0, 0x7777, 0, 0, 0, 0),
            (0xC4, dev, sub_a, 0, 0, 0, 0, 0),
            (0x148, dev, 4, 0, 0, 2, 0, 0),
            (0xC4, dev, sub_b, 0, 0, 0, 0, 0),
            (0x148, dev, 4, 0, 0, 2, 0, 0),
        ]
        if got != expected:
            return ['the calls were %r' % (got,)]
        return []
    finally:
        done()


def test_skeleton_draw_subset_textures(h):
    """Without a texture argument each subset sets its own texture before its material."""
    log, dev, done = _setup(h)
    try:
        track = _track(h, 0xD000, 4, 1)
        set_ = _animation_set(h, [track])
        obj, (sub_a, sub_b) = _skeleton(h, [(_texture(h, 0x5555), 0, 0),
                                            (_texture(h, 0x6666), 0, 0)], vertices=3)
        diffs = _draw(h, obj, set_, 0, 0)
        if diffs:
            return diffs
        _clear_log(h, log, RECORD * 64)
        res = h.call(DRAW, args=[set_, 0, 0], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        got = _records(h, log)
        tail = [r for r in got if r[0] in (0x104, 0xC4, 0x148)]
        expected = [
            (0x104, dev, 0, 0x5555, 0, 0, 0, 0),
            (0xC4, dev, sub_a, 0, 0, 0, 0, 0),
            (0x148, dev, 4, 0, 0, 3, 0, 0),
            (0x104, dev, 0, 0x6666, 0, 0, 0, 0),
            (0xC4, dev, sub_b, 0, 0, 0, 0, 0),
            (0x148, dev, 4, 0, 0, 3, 0, 0),
        ]
        if tail != expected:
            return ['the calls were %r' % (tail,)]
        return []
    finally:
        done()


def test_skeleton_draw_without_vertices(h):
    """An empty vertex vector draws with a vertex count of zero."""
    log, dev, done = _setup(h)
    try:
        track = _track(h, 0xE000, 2, 1)
        set_ = _animation_set(h, [track])
        obj, _ = _skeleton(h, [(0, 2, 5)], vertices=0)
        diffs = _draw(h, obj, set_, 0, 0)
        if diffs:
            return diffs
        _clear_log(h, log, RECORD * 64)
        res = h.call(DRAW, args=[set_, 0, 0], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        got = _records(h, log)
        draw = [r for r in got if r[0] == 0x148]
        if draw != [(0x148, dev, 4, 0, 0, 0, 2, 5)]:
            return ['the draw was %r' % (draw,)]
        return []
    finally:
        done()
