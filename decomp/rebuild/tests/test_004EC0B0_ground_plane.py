"""0x004EC0B0 (ground plane build): the fields are reset, slot 0x28 of the plane's own vtable runs with the first
int, the old vertex array is deleted and rows*columns 12-byte vertices are allocated; the grid is rows*rows points
with sx = 1/(columns-1) and sz = 1/(rows-1), a 20-byte vertex buffer gets u = x + 0.5 and v = 1 - (z + 0.5) at
+0x0C/+0x10 of every entry, and a 16-bit index buffer gets six indices per quad.  The device, its creations, the
buffers and the three helpers are stubs that log their arguments; the vertices, the UVs, the indices and the field
updates are checked against a Python model."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_FPCW

FN = 0x004EC0B0
DEV_GLOBAL = 0x006C8C10
FVF_GLOBAL = 0x006C09F8
CHECK = 0x00458940
NEW = 0x005E3B10
DELETE = 0x005E3EBA
GROUND_H = 0x00612BC8          # "e:\prog\att1\GroundPlane.h"
FVF = 0x01C4
FILE_NAME = b'e:\\prog\\att1\\GroundPlane.h'
ARG_INIT = 0x1234
HR_VB = 0x11112222
HR_IB = 0x33334444

L_COUNT = 0x00
L_EVENTS = 0x08
LOG_SIZE = 0x400

E_INIT_SELF = 0x01
E_INIT_ARG = 0x02
E_DELETE = 0x03
E_NEW = 0x04
E_CV_LEN = 0x10
E_CV_USAGE = 0x11
E_CV_FMT = 0x12
E_CV_POOL = 0x13
E_CV_OUT = 0x14
E_CHK_HR = 0x20
E_CHK_FILE = 0x21
E_CHK_LINE = 0x22
E_LOCK_SELF = 0x30
E_LOCK_OFF = 0x31
E_LOCK_LEN = 0x32
E_LOCK_FLAGS = 0x33
E_UNLOCK_SELF = 0x40
E_CI_LEN = 0x50
E_CI_USAGE = 0x51
E_CI_FMT = 0x52
E_CI_POOL = 0x53
E_CI_OUT = 0x54

saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _thunk_to(h, address, stub):
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _patch_callee(h, address, stub):
    """the original body calls the entry; the rebuilt code may call the glue implementation directly"""
    _thunk_to(h, address, stub)
    target = h.symbols.get('_sub_%08X' % address)
    if target is not None and target != address:
        _thunk_to(h, target, stub)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _ev(log, code, load):
    """appends (code, value) to the event list; load leaves the value in eax"""
    return (b'\xFF\x05' + _dword(log + L_COUNT) +
            b'\xA1' + _dword(log + L_COUNT) +
            b'\x48' +
            b'\x8D\x14\xC5' + _dword(log + L_EVENTS) +
            b'\xC7\x02' + _dword(code) +
            load +
            b'\x89\x42\x04')


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def _arg(n):
    return b'\x8B\x44\x24' + bytes([4 + 4 * n])                    # mov eax,[esp+4+4n]


def _init_stub(log):
    return _ev(log, E_INIT_SELF, b'\x8B\xC1') + _ev(log, E_INIT_ARG, _arg(0)) + b'\xC2\x04\x00'


def _create_stub(log, tags, obj, hr):
    code = _ev(log, tags[0], _arg(1))                             # length
    code += _ev(log, tags[1], _arg(2))                            # usage
    code += _ev(log, tags[2], _arg(3))                            # FVF / format
    code += _ev(log, tags[3], _arg(4))                            # pool
    code += _ev(log, tags[4], _arg(5))                            # out pointer
    code += _arg(5) + b'\xC7\x00' + _dword(obj)                   # *out = obj
    code += b'\xB8' + _dword(hr) + b'\xC2\x1C\x00'                # return hr
    return code


def _check_stub(log):
    return (_ev(log, E_CHK_HR, _arg(0)) + _ev(log, E_CHK_FILE, _arg(1)) + _ev(log, E_CHK_LINE, _arg(2)) +
            b'\xC3')


def _lock_stub(log, data):
    code = _ev(log, E_LOCK_SELF, _arg(0))
    code += _ev(log, E_LOCK_OFF, _arg(1))
    code += _ev(log, E_LOCK_LEN, _arg(2))
    code += _ev(log, E_LOCK_FLAGS, _arg(4))
    code += _arg(3) + b'\xC7\x00' + _dword(data)                  # *data = buffer
    code += b'\x33\xC0\xC2\x14\x00'
    return code


def _unlock_stub(log):
    return _ev(log, E_UNLOCK_SELF, _arg(0)) + b'\x33\xC0\xC2\x04\x00'


def _new_stub(log, buffer):
    return _ev(log, E_NEW, _arg(0)) + b'\xB8' + _dword(buffer) + b'\xC3'


def _delete_stub(log):
    return _ev(log, E_DELETE, _arg(0)) + b'\xC3'


def _f32bits(d):
    if d != d:                                                    # the x87/SSE invalid result
        return 0xFFC00000
    return struct.unpack('<I', struct.pack('<f', d))[0]


def _bits_f(bits):
    return struct.unpack('<f', struct.pack('<I', bits))[0]


def _recip(n):
    """1.0/(double)(unsigned)n, rounded to float (0 gives +inf)"""
    if n == 0:
        return float('inf')
    return _bits_f(_f32bits(1.0 / float(n)))


def _grid(width, height):
    """(x bits, z bits) of every point, in write order"""
    sx = _recip((width - 1) & 0xFFFFFFFF)
    sz = _recip((height - 1) & 0xFFFFFFFF)
    out = []
    for i in range(height):
        for j in range(height):
            out.append((_f32bits(float(j) * float(sx) - 0.5), _f32bits(float(i) * float(sz) - 0.5)))
    return out


def _uv(point):
    """(u bits, v bits) the vertex buffer gets for a grid point"""
    return (_f32bits(_bits_f(point[0]) + 0.5), _f32bits(1.0 - (_bits_f(point[1]) + 0.5)))


def _indices(width, height):
    w16 = width & 0xFFFF
    out = []
    for i in range((height - 1) & 0xFFFFFFFF):
        for j in range((width - 1) & 0xFFFFFFFF):
            a = (w16 * i + j) & 0xFFFF
            b = (w16 * ((i + 1) & 0xFFFF) + j) & 0xFFFF
            out += [a, b, (a + 1) & 0xFFFF, b, (b + 1) & 0xFFFF, (a + 1) & 0xFFFF]
    return out


def _case(h, width, height, flag, old, label=''):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    this = h.alloc(0x200, bytes(0x200))
    this_vt = h.alloc(0x40, bytes(0x40))
    device = h.alloc(0x10, bytes(0x10))
    dev_vt = h.alloc(0x80, bytes(0x80))
    vb_obj = h.alloc(0x10, bytes(0x10))
    ib_obj = h.alloc(0x10, bytes(0x10))
    vb_vt = h.alloc(0x40, bytes(0x40))
    ib_vt = h.alloc(0x40, bytes(0x40))
    count = height * height
    quads = ((height - 1) & 0xFFFFFFFF) * ((width - 1) & 0xFFFFFFFF)
    verts_size = 12 * max(width * height, count) + 16
    uv_size = 20 * count + 16
    idx_size = 12 * quads + 16
    verts = h.alloc(verts_size, b'\xCC' * verts_size)
    uvs = h.alloc(uv_size, b'\xCC' * uv_size)
    indices = h.alloc(idx_size, b'\xCC' * idx_size)
    h.uc.mem_write(vb_obj, _dword(vb_vt))
    h.uc.mem_write(ib_obj, _dword(ib_vt))
    h.uc.mem_write(vb_vt + 0x2C, _dword(_stub(h, _lock_stub(log, uvs))))
    h.uc.mem_write(vb_vt + 0x30, _dword(_stub(h, _unlock_stub(log))))
    h.uc.mem_write(ib_vt + 0x2C, _dword(_stub(h, _lock_stub(log, indices))))
    h.uc.mem_write(ib_vt + 0x30, _dword(_stub(h, _unlock_stub(log))))
    h.uc.mem_write(device, _dword(dev_vt))
    h.uc.mem_write(dev_vt + 0x68, _dword(_stub(h, _create_stub(
        log, (E_CV_LEN, E_CV_USAGE, E_CV_FMT, E_CV_POOL, E_CV_OUT), vb_obj, HR_VB))))
    h.uc.mem_write(dev_vt + 0x6C, _dword(_stub(h, _create_stub(
        log, (E_CI_LEN, E_CI_USAGE, E_CI_FMT, E_CI_POOL, E_CI_OUT), ib_obj, HR_IB))))
    h.uc.mem_write(this_vt + 0x28, _dword(_stub(h, _init_stub(log))))

    _patch(h, DEV_GLOBAL, _dword(device))
    _patch(h, FVF_GLOBAL, _dword(FVF))
    _patch_callee(h, CHECK, _stub(h, _check_stub(log)))
    _patch_callee(h, NEW, _stub(h, _new_stub(log, verts)))
    _patch_callee(h, DELETE, _stub(h, _delete_stub(log)))

    def setup():
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(this, b'\xCC' * 0x200)
        h.uc.mem_write(this, _dword(this_vt))
        h.uc.mem_write(this + 0x19C, _dword(old))
        h.uc.mem_write(verts, b'\xCC' * verts_size)
        h.uc.mem_write(uvs, b'\xCC' * uv_size)
        h.uc.mem_write(indices, b'\xCC' * idx_size)

    setup()
    diffs = h.compare(FN, args=(ARG_INIT, width, height, flag), regs={UC_X86_REG_ECX: this}, ret=None)
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]

    setup()
    res = h.call(FN, args=(ARG_INIT, width, height, flag), regs={UC_X86_REG_ECX: this})
    if res['fault']:
        return ['%s: replacement faulted: %s' % (label, res['fault'])]

    events = [(E_INIT_SELF, this), (E_INIT_ARG, ARG_INIT)]
    if old:
        events.append((E_DELETE, old))
    if width * height:
        events.append((E_NEW, (width * height * 12) & 0xFFFFFFFF))
    events += [(E_CV_LEN, (count * 20) & 0xFFFFFFFF), (E_CV_USAGE, 8), (E_CV_FMT, FVF), (E_CV_POOL, 1),
               (E_CV_OUT, this + 0x18C)]
    events += [(E_CHK_HR, HR_VB), (E_CHK_LINE, 0xD4)]
    events += [(E_LOCK_SELF, vb_obj), (E_LOCK_OFF, 0), (E_LOCK_LEN, 0), (E_LOCK_FLAGS, 0),
               (E_UNLOCK_SELF, vb_obj)]
    events += [(E_CI_LEN, (quads * 12) & 0xFFFFFFFF), (E_CI_USAGE, 8), (E_CI_FMT, 0x65), (E_CI_POOL, 1),
               (E_CI_OUT, this + 0x190)]
    events += [(E_CHK_HR, HR_IB), (E_CHK_LINE, 0xE6)]
    events += [(E_LOCK_SELF, ib_obj), (E_LOCK_OFF, 0), (E_LOCK_LEN, 0), (E_LOCK_FLAGS, 0),
               (E_UNLOCK_SELF, ib_obj)]
    got = _events(h, log)
    files = [value for code, value in got if code == E_CHK_FILE]
    if len(files) != 2 or any(bytes(h.uc.mem_read(p, len(FILE_NAME) + 1)) != FILE_NAME + b'\x00'
                              for p in files):
        return ['%s: the file argument is %r' % (label, files)]
    got = [(code, value) for code, value in got if code != E_CHK_FILE]
    if got != events:
        return ['%s: events %r, expected %r' % (label, got, events)]

    want = {'+0x184': width, '+0x188': height, '+0x194': (quads * 2) & 0xFFFFFFFF, '+0x1a0': count,
            '+0x19c': verts, '+0x18c': vb_obj, '+0x190': ib_obj}
    for name, value in want.items():
        if _u32(h, this + int(name, 16)) != value & 0xFFFFFFFF:
            return ['%s: %s is %#x, expected %#x' % (label, name, _u32(h, this + int(name, 16)), value)]
    if bytes(h.uc.mem_read(this + 0x1A4, 3)) != bytes((1, 1, flag & 0xFF)):
        return ['%s: the tail bytes are %r' % (label, bytes(h.uc.mem_read(this + 0x1A4, 3)))]

    grid = _grid(width, height)
    area = bytes(h.uc.mem_read(verts, verts_size))
    for k, (bx, bz) in enumerate(grid):
        entry = struct.unpack('<3I', area[k * 12:k * 12 + 12])
        if entry != (bx, 0, bz):
            return ['%s: vertex %d is %r, expected (%08X, 0, %08X)' % (label, k, entry, bx, bz)]
    if area[len(grid) * 12:] != b'\xCC' * (verts_size - len(grid) * 12):
        return ['%s: the vertex array has bytes past the last point' % label]

    area = bytes(h.uc.mem_read(uvs, uv_size))
    for k, point in enumerate(grid):
        u, v = _uv(point)
        if struct.unpack('<2I', area[k * 20 + 0xC:k * 20 + 0x14]) != (u, v):
            return ['%s: UV %d is %s, expected (%08X, %08X)' % (label, k, area[k * 20 + 0xC:k * 20 + 0x14].hex(), u, v)]
        if area[k * 20:k * 20 + 0xC] != b'\xCC' * 12:
            return ['%s: UV %d has other bytes written' % (label, k)]
    if area[count * 20:] != b'\xCC' * (uv_size - count * 20):
        return ['%s: the vertex buffer has bytes past the last UV' % label]

    area = bytes(h.uc.mem_read(indices, idx_size))
    want_idx = _indices(width, height)
    got_idx = list(struct.unpack('<%dH' % (len(want_idx) or 1), area[:2 * len(want_idx) or 2]))
    if got_idx[:len(want_idx)] != want_idx:
        return ['%s: indices %r, expected %r' % (label, got_idx[:len(want_idx)], want_idx)]
    if area[2 * len(want_idx):] != b'\xCC' * (idx_size - 2 * len(want_idx)):
        return ['%s: the index buffer has bytes past the last index' % label]
    return None


def test_004EC0B0(h):
    heap0 = h.heap_ptr
    control = h.uc.reg_read(UC_X86_REG_FPCW)
    try:
        h.uc.reg_write(UC_X86_REG_FPCW, 0x027F)
        old = h.alloc(0x20, b'\xEE' * 0x20)
        for case in (dict(width=5, height=3, flag=0x5A, old=old, label='5x3 with an old array'),
                     dict(width=3, height=5, flag=0, old=0, label='3x5, no old array'),
                     dict(width=2, height=4, flag=7, old=0, label='2x4'),
                     dict(width=1, height=1, flag=1, old=old, label='1x1')):
            result = _case(h, **case)
            if result:
                return result
    finally:
        _restore(h)
        h.uc.reg_write(UC_X86_REG_FPCW, control)
        h.heap_ptr = heap0
    return None
