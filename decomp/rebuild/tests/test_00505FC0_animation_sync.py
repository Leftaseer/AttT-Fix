"""0x505FC0 (the battle standard's animation sync): the position from the standard's own vtable (+0x68, +0x64)
becomes the animation's previous (+0x58) and current (+0x64) position, the +0x74 vector and the +0x98 vector
doubled go to the animation, the animation's +0x168 matrix is the device's world transform (also kept at
0x6CA0A4) and its 8 box corners are transformed and tested against the camera's planes; only a visible box
draws.  Every virtual call is a stub; the standard, animation, device and camera objects are ours.  The
comparison leaves memory out because 0x6CA0A4 holds a pointer to the caller's frame."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

SETUP = 0x00505FC0
DEV_GLOBAL = 0x006C8C10
MATRIX_GLOBAL = 0x006CA0A4
CAMERA_GLOBAL = 0x006CA2C8

saved = {}

IDENT = (1.0, 0.0, 0.0, 0.0,  0.0, 1.0, 0.0, 0.0,  0.0, 0.0, 1.0, 0.0,  0.0, 0.0, 0.0, 1.0)
TRANS10 = (1.0, 0.0, 0.0, 0.0,  0.0, 1.0, 0.0, 0.0,  0.0, 0.0, 1.0, 0.0,  10.0, 0.0, 0.0, 1.0)

POS = (11.5, -2.25, 3.75)              # the standard's +0x64, returned by its vtable +0x68
VEC74 = (1.0, 1.5, 2.0)                # copied unscaled
VEC98 = (1.25, -3.5, 0.1)              # doubled into the animation
OLDPOS = (-1.0, -2.0, -3.0)            # the animation's position before the update
OLDPREV = (9.0, 9.5, 9.25)             # its previous position before the update

CORNERS = (0.0, 0.0, 0.0,   0.5, 1.0, 0.0,   1.0, 0.0, 1.0,   1.5, 1.0, 1.0,
           2.0, 0.5, 0.5,   0.25, 0.0, -1.0,  0.75, 1.0, -1.0,  1.25, 0.5, 2.0)


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _tag(seq, tag):
    """appends tag to the sequence at seq (count at +0, entries from +4)"""
    return (b'\xA1' + _dword(seq) +                                   # mov eax,[seq]
            b'\xFF\x05' + _dword(seq) +                               # inc dword [seq]
            b'\xC7\x04\x85' + _dword(seq + 4) + _dword(tag))          # mov dword [seq+4+eax*4],tag


def _getpos_stub(h, seq, log):
    """vtable +0x68(self): logs self, returns self + 0x64"""
    code = _tag(seq, 1) + b'\x89\x0D' + _dword(log) + b'\x8D\x41\x64\xC3'
    return _stub(h, code)


def _update_stub(h, seq, log):
    """vtable +0x18(self): logs self"""
    code = _tag(seq, 2) + b'\x89\x0D' + _dword(log) + b'\x33\xC0\xC3'
    return _stub(h, code)


def _swap_update_stub(h, seq, log, this_cell, anim2):
    """vtable +0x18(self): logs self and repoints the standard's +0x1E8 at anim2"""
    code = _tag(seq, 2) + b'\x89\x0D' + _dword(log)
    code += b'\x8B\x15' + _dword(this_cell)                           # mov edx,[this_cell]
    code += b'\xC7\x82\xE8\x01\x00\x00' + _dword(anim2)               # mov dword [edx+0x1E8],anim2
    code += b'\x33\xC0\xC3'
    return _stub(h, code)


def _box_stub(h, seq, log, corners):
    """vtable +0xEC(self): logs self, returns the 0x60-byte corner array"""
    code = _tag(seq, 4) + b'\x89\x0D' + _dword(log) + b'\xB8' + _dword(corners) + b'\xC3'
    return _stub(h, code)


def _draw_stub(h, seq, log):
    """vtable +0x08(self): logs self"""
    code = _tag(seq, 5) + b'\x89\x0D' + _dword(log) + b'\x33\xC0\xC3'
    return _stub(h, code)


def _set_transform_stub(h, seq, log, copy):
    """device vtable +0xB0(dev, state, matrix): logs the arguments and copies the matrix"""
    code = _tag(seq, 3)
    code += b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)               # dev
    code += b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4)           # state
    code += b'\x8B\x4C\x24\x0C' + b'\x89\x0D' + _dword(log + 8)       # matrix pointer
    code += b'\x56\x57'                                               # push esi; push edi
    code += b'\x8B\xF1' + b'\xBF' + _dword(copy)                      # mov esi,ecx; mov edi,copy
    code += b'\xB9\x40\x00\x00\x00' + b'\xF3\xA4'                     # mov ecx,0x40; rep movsb
    code += b'\x5F\x5E' + b'\x33\xC0' + b'\xC2\x0C\x00'               # pop edi; pop esi; xor eax,eax; ret 0xC
    return _stub(h, code)


def _scaled(raw):
    return struct.pack('<f', struct.unpack('<f', raw)[0] * 2.0)


def _check(h, visible_camera, translate, swap):
    heap0 = h.heap_ptr
    seq = h.alloc(0x40, bytes(0x40))
    log_pos = h.alloc(0x10, bytes(0x10))
    log_upd = h.alloc(0x10, bytes(0x10))
    log_draw = h.alloc(0x10, bytes(0x10))
    log_box = h.alloc(0x10, bytes(0x10))
    log_st = h.alloc(0x20, bytes(0x20))
    matcopy = h.alloc(0x40, b'\xCC' * 0x40)
    try:
        # camera: 6 planes at +4; the (1,0,0,-5) plane has every corner behind until they are moved +10 in x
        camera = h.alloc(0x80, bytes(0x80))
        planes = [(0.0, 0.0, 0.0, 100.0)] * 6 if visible_camera else \
                 [(1.0, 0.0, 0.0, -5.0)] + [(0.0, 0.0, 0.0, 100.0)] * 5
        for i, plane in enumerate(planes):
            h.uc.mem_write(camera + 4 + i * 16, struct.pack('<4f', *plane))

        corners = h.alloc(0x60, struct.pack('<24f', *CORNERS))

        anim = h.alloc(0x200, b'\xCC' * 0x200)
        anim2 = h.alloc(0x200, b'\xCC' * 0x200)
        for a, matrix in ((anim, TRANS10 if translate else IDENT), (anim2, IDENT)):
            h.uc.mem_write(a + 0x58, struct.pack('<3f', *OLDPREV))
            h.uc.mem_write(a + 0x64, struct.pack('<3f', *OLDPOS))
            h.uc.mem_write(a + 0x74, struct.pack('<3f', 7.0, 8.0, 9.0))
            h.uc.mem_write(a + 0x98, struct.pack('<3f', 4.0, 5.0, 6.0))
            h.uc.mem_write(a + 0x168, struct.pack('<16f', *matrix))

        this = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(this + 0x64, struct.pack('<3f', *POS))
        h.uc.mem_write(this + 0x74, struct.pack('<3f', *VEC74))
        h.uc.mem_write(this + 0x98, struct.pack('<3f', *VEC98))
        h.uc.mem_write(this + 0x1e8, _dword(anim))

        vt_this = h.alloc(0x80, bytes(0x80))
        vt_anim = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(this, _dword(vt_this))
        h.uc.mem_write(anim, _dword(vt_anim))
        h.uc.mem_write(anim2, _dword(vt_anim))
        h.uc.mem_write(vt_this + 0x68, _dword(_getpos_stub(h, seq, log_pos)))
        if swap:
            this_cell = h.alloc(4, _dword(this))
            h.uc.mem_write(vt_anim + 0x18, _dword(_swap_update_stub(h, seq, log_upd, this_cell, anim2)))
        else:
            h.uc.mem_write(vt_anim + 0x18, _dword(_update_stub(h, seq, log_upd)))
        h.uc.mem_write(vt_anim + 0xec, _dword(_box_stub(h, seq, log_box, corners)))
        h.uc.mem_write(vt_anim + 0x08, _dword(_draw_stub(h, seq, log_draw)))

        device = h.alloc(0x10, bytes(0x10))
        devvt = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(device, _dword(devvt))
        h.uc.mem_write(devvt + 0xb0, _dword(_set_transform_stub(h, seq, log_st, matcopy)))
        _patch(h, DEV_GLOBAL, _dword(device))
        _patch(h, MATRIX_GLOBAL, _dword(0))
        _patch(h, CAMERA_GLOBAL, _dword(camera))

        diffs = h.compare(SETUP, regs={UC_X86_REG_ECX: this}, ret=None, mem=False)
        if diffs:
            return ['visible %d translate %d swap %d: %s' % (visible_camera, translate, swap, d) for d in diffs]

        result = h.call(SETUP, regs={UC_X86_REG_ECX: this})
        if result['fault']:
            return ['visible %d translate %d swap %d: %s' % (visible_camera, translate, swap, result['fault'])]

        used = anim2 if swap else anim
        visible = visible_camera or (translate and not swap)
        problems = []
        tags = [_u32(h, seq + 4 + i * 4) for i in range(_u32(h, seq))]
        want = [1, 2, 3, 4] + ([5] if visible else [])
        if tags != want:
            problems.append('calls %r, want %r' % (tags, want))
        if _u32(h, log_pos) != this:
            problems.append('the position was asked of %#x, not %#x' % (_u32(h, log_pos), this))
        if _u32(h, log_upd) != anim:
            problems.append('the update ran on %#x, not %#x' % (_u32(h, log_upd), anim))
        if _u32(h, log_box) != used:
            problems.append('the box was asked of %#x, not %#x' % (_u32(h, log_box), used))
        if visible and _u32(h, log_draw) != used:
            problems.append('the draw ran on %#x, not %#x' % (_u32(h, log_draw), used))
        if (_u32(h, log_st), _u32(h, log_st + 4)) != (device, 0x100):
            problems.append('set transform on %#x, %#x' % (_u32(h, log_st), _u32(h, log_st + 4)))
        if _u32(h, log_st + 8) != _u32(h, MATRIX_GLOBAL):
            problems.append('the current matrix %#x is not the one set (%#x)'
                            % (_u32(h, MATRIX_GLOBAL), _u32(h, log_st + 8)))
        if bytes(h.uc.mem_read(matcopy, 0x40)) != bytes(h.uc.mem_read(used + 0x168, 0x40)):
            problems.append('the set matrix is not %#x + 0x168' % used)
        if bytes(h.uc.mem_read(anim + 0x58, 0xc)) != struct.pack('<3f', *OLDPOS):
            problems.append('the previous position is not the old position')
        if bytes(h.uc.mem_read(anim + 0x64, 0xc)) != struct.pack('<3f', *POS):
            problems.append('the position was not copied')
        if bytes(h.uc.mem_read(anim + 0x70, 1)) != b'\x01':
            problems.append('+0x70 was not set')
        if bytes(h.uc.mem_read(anim + 0x74, 0xc)) != struct.pack('<3f', *VEC74):
            problems.append('the +0x74 vector was not copied')
        if bytes(h.uc.mem_read(anim + 0x80, 1)) != b'\x01':
            problems.append('+0x80 was not set')
        want98 = b''.join(_scaled(struct.pack('<f', v)) for v in VEC98)
        if bytes(h.uc.mem_read(anim + 0x98, 0xc)) != want98:
            problems.append('the scale is %r, want %r' % (bytes(h.uc.mem_read(anim + 0x98, 0xc)), want98))
        if bytes(h.uc.mem_read(anim + 0xa4, 1)) != b'\x01':
            problems.append('+0xA4 was not set')
        if swap and bytes(h.uc.mem_read(anim2 + 0x64, 0xc)) != struct.pack('<3f', *OLDPOS):
            problems.append('the repointed animation got the position')
        return ['visible %d translate %d swap %d: %s' % (visible_camera, translate, swap, p) for p in problems] or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_visible_animation_updates_and_draws(h):
    return _check(h, True, False, False)


def test_hidden_animation_skips_draw(h):
    return _check(h, False, False, False)


def test_world_matrix_moves_corners_into_view(h):
    return _check(h, False, True, False)


def test_update_repoints_the_animation(h):
    """the animation is read again after the update and after the transform: the repointed one is used"""
    return _check(h, False, True, True)
