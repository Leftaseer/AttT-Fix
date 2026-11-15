"""0x42DA70 (keyframe matrix picked from the mesh object's key lists) and 0x42DB40 (projectile per-frame update);
the D3DX calls and the other helpers are stubbed so the tests observe what the functions pass them."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

KEYFRAME = 0x0042DA70
UPDATE = 0x0042DB40

ROTATION = 0x005B802C                       # D3DXMatrixRotationYawPitchRoll thunk
MULTIPLY = 0x005B8020                       # D3DXMatrixMultiply thunk
CONSTANT = 0x006C1190                       # the matrix the keyframe result is multiplied by
UPDATE_TRANSFORM = 0x004AC890
DRAW = 0x00474BC0

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, stub):
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    h.uc.ctl_remove_cache(target, target + 5)


def _log_eax(offset):
    return b'\xA3' + _dword(offset)


def _log_ecx(offset):
    return b'\x89\x0D' + _dword(offset)


def _rotation_stub(h, log):
    """logs yaw, pitch, roll from the stack; marks the matrix rows 0..2 and the (unused) cell 15"""
    code = b'\x8B\x54\x24\x04'                                # mov edx, [esp+4]  (the matrix)
    for i, off in enumerate((8, 12, 16)):
        code += b'\x8B\x44\x24' + bytes([off]) + _log_eax(log + 4 * i)
    code += b'\xC7\x02' + _dword(0x11111111)
    code += b'\xC7\x42\x04' + _dword(0x22222222)
    code += b'\xC7\x42\x08' + _dword(0x33333333)
    code += b'\xC7\x42\x3C' + _dword(0xCAFEBABE)
    code += b'\x33\xC0'                                       # xor eax, eax
    code += b'\xC2\x10\x00'                                   # ret 16
    return _stub(h, code)


def _multiply_stub(h, log):
    """logs (out, b) and the matrix cells 0, 1, 2, 12..14, 15; writes 0xDEADBEEF into out"""
    code = b'\x8B\x54\x24\x04' + b'\x89\x15' + _dword(log + 0x10)   # mov edx, [esp+4]; mov [log+10], edx
    code += b'\x8B\x4C\x24\x08'                               # mov ecx, [esp+8]  (a)
    code += b'\x8B\x44\x24\x0C' + _log_eax(log + 0x14)        # mov eax, [esp+0xc]; log b
    for i, off in enumerate((0, 4, 8, 0x30, 0x34, 0x38, 0x3C)):
        code += b'\x8B\x41' + bytes([off]) + _log_eax(log + 0x18 + 4 * i)
    code += b'\xC7\x02' + _dword(0xDEADBEEF)                  # mov dword [edx], 0xDEADBEEF
    code += b'\x8B\xC2'                                       # mov eax, edx
    code += b'\xC2\x0C\x00'                                   # ret 12
    return _stub(h, code)


def _keyframe_setup(h, list_index, stride, count):
    s = h.alloc(0x200, bytes(0x200))
    pose = h.alloc(0x40, bytes(0x40))
    lists = h.alloc(0x30, bytes(0x30))
    recs = [h.alloc(0x100, bytes(0x100)) for _ in range(3)]
    for j in range(3):
        h.uc.mem_write(recs[j], b''.join(_dword(_bits(float(100 * j + 6 * i + k)))
                                         for i in range(4) for k in range(6)))
        entry = h.alloc(0x20, bytes(0x20))
        h.uc.mem_write(entry, _dword(recs[j]))
        h.uc.mem_write(entry + 8, _dword(count))
        h.uc.mem_write(entry + 0xc, _dword(stride))
        h.uc.mem_write(lists + 4 * j, _dword(entry))
    h.uc.mem_write(pose + 4, _dword(lists))
    h.uc.mem_write(pose + 8, _dword(lists + 12))
    h.uc.mem_write(s + 0x78, _dword(list_index))
    out = h.alloc(0x40, b'\xCC' * 0x40)
    return s, pose, out, recs


def test_keyframe_matrix(h):
    """+0x78 picks the list, the frame the record (stride*0x18; out of range reads record 0), the record's first
    vec3 is fed to D3DXMatrixRotationYawPitchRoll as yaw/pitch/roll and its second one becomes matrix row 3; the
    result is D3DXMatrixMultiply(out, matrix, 0x006C1190) and out is returned"""
    heap0 = h.heap_ptr
    log = h.alloc(0x40, bytes(0x40))
    _hook(h, ROTATION, _rotation_stub(h, log))
    _hook(h, MULTIPLY, _multiply_stub(h, log))
    try:
        problems = []
        for list_index, frame, stride, count in ((0, 1, 2, 3), (2, 0, 1, 3), (1, 7, 1, 2), (0, 0xffffffff, 2, 3)):
            s, pose, out, recs = _keyframe_setup(h, list_index, stride, count)
            index = frame if frame < count else 0
            rec = recs[list_index] + stride * index * 0x18
            want = [_u32(h, rec + 4 * i) for i in range(6)]
            h.uc.mem_write(log, bytes(0x40))
            diffs = h.compare(KEYFRAME, args=[out, pose, frame], regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                return ['list %d frame %#x: %s' % (list_index, frame, d) for d in diffs]
            res = h.call(KEYFRAME, args=[out, pose, frame], regs={UC_X86_REG_ECX: s})
            if res['eax'] != out:
                problems.append('list %d frame %#x: result %#x' % (list_index, frame, res['eax']))
            if [_u32(h, log + 4 * i) for i in (1, 0, 2)] != want[0:3]:
                problems.append('list %d frame %#x: yaw/pitch/roll %r, want %r'
                                % (list_index, frame, [_u32(h, log + 4 * i) for i in (1, 0, 2)], want[0:3]))
            if [_u32(h, log + 0x18 + 4 * i) for i in (3, 4, 5)] != want[3:6]:
                problems.append('list %d frame %#x: translation %r, want %r'
                                % (list_index, frame, [_u32(h, log + 0x18 + 4 * i) for i in (3, 4, 5)], want[3:6]))
            if [_u32(h, log + 0x18 + 4 * i) for i in (0, 1, 2)] != [0x11111111, 0x22222222, 0x33333333]:
                problems.append('list %d frame %#x: another rotation matrix is multiplied' % (list_index, frame))
            if _u32(h, log + 0x30) != 0xCAFEBABE:
                problems.append('list %d frame %#x: the multiply got another matrix' % (list_index, frame))
            if _u32(h, log + 0x10) != out or _u32(h, log + 0x14) != h.to_rebuilt(CONSTANT):
                problems.append('list %d frame %#x: multiply got %#x, %#x'
                                % (list_index, frame, _u32(h, log + 0x10), _u32(h, log + 0x14)))
            if _u32(h, out) != 0xDEADBEEF:
                problems.append('list %d frame %#x: out is untouched' % (list_index, frame))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _update_stubs(h, log):
    transform = _stub(h, _log_ecx(log) + b'\xC3')
    code = _log_ecx(log + 4)
    for i in range(4):
        code += b'\x8B\x44\x24' + bytes([4 + 4 * i]) + _log_eax(log + 8 + 4 * i)
    code += b'\xB8' + _dword(0x77) + b'\xC2\x10\x00'
    draw = _stub(h, code)
    trail = _stub(h, _log_ecx(log + 0x20) + b'\xB8' + _dword(0xAB) + b'\xC3')
    return transform, draw, trail


def _update_setup(h, index, flying, trail_stub):
    s = h.alloc(0x300, bytes(0x300))
    owner = h.alloc(0x300, bytes(0x300))
    holder = h.alloc(0x200, bytes(0x200))
    info = h.alloc(0x200, bytes(0x200))
    mesh_list = h.alloc(0x20, bytes(0x20))
    meshes = [h.alloc(0x10, bytes(0x10)) for _ in range(3)]
    trail = h.alloc(0x40, bytes(0x40))
    vt = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(mesh_list, b''.join(_dword(m) for m in meshes))
    h.uc.mem_write(s + 0x1c8, _dword(mesh_list))
    h.uc.mem_write(s + 0x1cc, _dword(mesh_list + 12))
    h.uc.mem_write(s + 0x2bc, _dword(owner))
    h.uc.mem_write(owner + 0x2d0, _dword(index))
    h.uc.mem_write(owner + 0x168, b''.join(_dword(0x1000 + i) for i in range(16)))
    h.uc.mem_write(owner + 0x220, _dword(holder))
    h.uc.mem_write(holder + 0x1c4, _dword(info))
    h.uc.mem_write(info + 0x1d8, _dword(0x11D8))
    h.uc.mem_write(info + 0x1ec, _dword(0x11EC))
    h.uc.mem_write(vt + 8, _dword(trail_stub))
    h.uc.mem_write(trail, _dword(vt))
    h.uc.mem_write(s + 0x2c8, _dword(trail))
    h.uc.mem_write(s + 0x2c0, bytes([1 if flying else 0]))
    h.uc.mem_write(s + 0x214, b'\xCC' * 0x40)
    return s, owner, meshes, trail


def test_projectile_update(h):
    """glide: the pose mesh of the owner's (+0x2BC) index (+0x2D0, clamped to the mesh vector at +0x1C8) is drawn
    over the owner's transform (+0x168 copied to +0x214) with the info ids; flying: +0x214 is drawn bare with zero
    flags and stays untouched; the trail's (+0x2C8) vtable entry 2 result is returned"""
    heap0 = h.heap_ptr
    log = h.alloc(0x40, bytes(0x40))
    transform, draw, trail = _update_stubs(h, log)
    _hook(h, UPDATE_TRANSFORM, transform)
    _hook(h, DRAW, draw)
    try:
        problems = []
        for index, flying, want_index in ((1, False, 1), (0, False, 0), (2, False, 2),
                                          (3, True, 2), (0x99, True, 2)):
            s, owner, meshes, trail_obj = _update_setup(h, index, flying, trail)
            h.uc.mem_write(log, bytes(0x40))
            diffs = h.compare(UPDATE, regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                return ['index %#x flying %r: %s' % (index, flying, d) for d in diffs]
            res = h.call(UPDATE, regs={UC_X86_REG_ECX: s})
            if res['eax'] != 0xAB:
                problems.append('index %#x: result %#x' % (index, res['eax']))
            if _u32(h, log) != s:
                problems.append('index %#x: 0x004AC890 got %#x' % (index, _u32(h, log)))
            if _u32(h, log + 0x20) != trail_obj:
                problems.append('index %#x: the trail entry 2 got %#x' % (index, _u32(h, log + 0x20)))
            got = [_u32(h, log + 8 + 4 * i) for i in range(4)]
            if _u32(h, log + 4) != meshes[want_index] or got[0] != s + 0x214:
                problems.append('index %#x: draw got this %#x, matrix %#x'
                                % (index, _u32(h, log + 4), got[0]))
            if flying:
                if any(got[1:]) or bytes(h.uc.mem_read(s + 0x214, 0x40)) != b'\xCC' * 0x40:
                    problems.append('index %#x: the flying flags %r change the kept transform' % (index, got[1:]))
            else:
                if got[1] != 1 or got[2] != 0x11D8 or got[3] != 0x11EC:
                    problems.append('index %#x: draw got %r' % (index, got[1:]))
                if bytes(h.uc.mem_read(s + 0x214, 0x40)) != bytes(h.uc.mem_read(owner + 0x168, 0x40)):
                    problems.append('index %#x: the transform was not copied' % index)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
