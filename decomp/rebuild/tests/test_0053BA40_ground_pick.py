"""Ground pick at 0x0053BA40: the viewport extent getters, D3DXMatrixInverse and the screen size are stubs, and a
prepared camera/mesh makes the view ray hit the nearest of several triangles."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x0053BA40
INVERSE = 0x005B801A
ONE = 0x0068AE00
HEIGHT = 0x006C8958
WIDTH = 0x006C895C

# inverse view: identity axes, the eye in the translation row (dir = row2 + fx*row0 + fy*row1)
MATRIX = (1.0, 0.0, 0.0, 0.0,
          0.0, 1.0, 0.0, 0.0,
          0.0, 0.0, 1.0, 0.0,
          10.0, 20.0, 30.0, 1.0)
CAM = (10.0, 20.0, 30.0)
W = 500.0                       # 2*W/800 - 1 = 0.25 -> fx
H = 150.0                       # 2*H/600 - 1 = 0.5  -> fy
VERTICES = [(0.0, 0.0, 0.0), (0.0, 8.0, 0.0), (8.0, 0.0, 0.0),
            (0.0, 0.0, -10.0), (0.0, 8.0, -10.0), (8.0, 0.0, -10.0),
            (100.0, 100.0, 0.0), (100.0, 108.0, 0.0), (108.0, 100.0, 0.0)]
# back-facing (den < 0), off to the side, far (hit at (0,0,-10)), near (hit at (2.5,5,0))
TRIS = [(0, 2, 1), (6, 7, 8), (3, 4, 5), (0, 1, 2)]
NEAREST = (2.5, 5.0, 0.0)

saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


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


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _coord_stub(log, offset, value):
    """logs this and the call count, returns the float at value"""
    return (b'\x89\x0D' + _dword(log + offset) + b'\xFF\x05' + _dword(log + offset + 4) +
            b'\xD9\x05' + _dword(value) + b'\xC3')


def _inverse_stub(log, matrix):
    """logs det/matrix and the call count, copies the prepared matrix to out (its address is a frame local, so it
    is not logged; the two halves would differ)"""
    code = (b'\x8B\x44\x24\x04' +
            b'\x8B\x4C\x24\x08' + b'\x89\x0D' + _dword(log + 0x20) +
            b'\x8B\x54\x24\x0C' + b'\x89\x15' + _dword(log + 0x24) +
            b'\xFF\x05' + _dword(log + 0x28))
    for i in range(16):
        code += b'\x8B\x0D' + _dword(matrix + 4 * i) + b'\x89\x88' + _dword(4 * i)
    return code + b'\xC2\x0C\x00'


def _case(h, vertices, tris, indexed, want, label):
    log = h.alloc(0x40, bytes(0x40))
    obj = h.alloc(0x300, bytes(0x300))
    view = h.alloc(4, bytes(4))
    vtable = h.alloc(0xa0, bytes(0xa0))
    camera = h.alloc(0x100, bytes(0x100))
    mesh = h.alloc(0x210, bytes(0x210))
    coords = h.alloc(8, struct.pack('<ff', W, H))
    matrix = h.alloc(64, struct.pack('<16f', *MATRIX))
    verts = h.alloc(len(vertices) * 32, bytes(len(vertices) * 32))
    for i, (x, y, z) in enumerate(vertices):
        h.uc.mem_write(verts + i * 32, struct.pack('<3f', x, y, z))
    idx = h.alloc(max(6, 6 * len(tris)), b''.join(struct.pack('<3H', *t) for t in tris) + bytes(6))
    out = h.alloc(0x0c, b'\xCC' * 0x0c)
    h.uc.mem_write(vtable + 0x8c, _dword(_stub(h, _coord_stub(log, 0x00, coords))))
    h.uc.mem_write(vtable + 0x90, _dword(_stub(h, _coord_stub(log, 0x08, coords + 4))))
    h.uc.mem_write(view, _dword(vtable))
    h.uc.mem_write(camera + 0x88, struct.pack('<16f', *MATRIX))
    h.uc.mem_write(camera + 0xc8, _dword(_bits(1.0)))
    h.uc.mem_write(camera + 0xdc, _dword(_bits(1.0)))
    h.uc.mem_write(camera + 0x44, struct.pack('<3f', *CAM))
    h.uc.mem_write(obj + 0x144, _dword(view))
    h.uc.mem_write(obj + 0x160, _dword(camera))
    h.uc.mem_write(obj + 0x98, _dword(mesh))
    h.uc.mem_write(mesh + 0x1ec, _dword(verts))
    h.uc.mem_write(mesh + 0x1fc, _dword(idx if indexed else 0))
    h.uc.mem_write(mesh + 0x200, _dword(idx + 6 * len(tris) if indexed else 0))
    _hook(h, INVERSE, _inverse_stub(log, matrix))

    diffs = h.compare(FN, args=(out,), regs={UC_X86_REG_ECX: obj}, ret='al')
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]

    h.uc.mem_write(log, bytes(0x40))
    h.uc.mem_write(out, b'\xCC' * 0x0c)
    result = h.call(FN, args=(out,), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['%s: %s' % (label, result['fault'])]

    problems = []
    if (result['eax'] & 0xFF) != (1 if want else 0):
        return ['%s: the result is %#x' % (label, result['eax'] & 0xFF)]
    if want:
        got = struct.unpack('<3f', h.uc.mem_read(out, 0x0c))
        if got != want:
            problems.append('%s: the hit point is %s, want %s' % (label, got, want))
    elif h.uc.mem_read(out, 0x0c) != b'\xCC' * 0x0c:
        problems.append('%s: the hit point was written without a hit' % label)
    if _u32(h, log + 0x00) != view or _u32(h, log + 0x08) != view:
        problems.append('%s: the extent getters got %08X / %08X' % (label, _u32(h, log), _u32(h, log + 8)))
    if _u32(h, log + 0x04) != 1 or _u32(h, log + 0x0c) != 1:
        problems.append('%s: the extent getter counts are %d / %d' % (label, _u32(h, log + 4), _u32(h, log + 0xc)))
    if _u32(h, log + 0x20) != 0 or _u32(h, log + 0x24) != camera + 0x88:
        problems.append('%s: the inverse arguments are %08X %08X' %
                        (label, _u32(h, log + 0x20), _u32(h, log + 0x24)))
    if _u32(h, log + 0x28) != 1:
        problems.append('%s: the inverse was called %d times' % (label, _u32(h, log + 0x28)))
    return problems


def test_0053BA40(h):
    heap0 = h.heap_ptr
    try:
        _patch(h, WIDTH, _dword(_bits(800.0)))
        _patch(h, HEIGHT, _dword(_bits(600.0)))
        _patch(h, ONE, struct.pack('<d', 1.0))
        problems = []
        problems += _case(h, VERTICES, TRIS, True, NEAREST, 'nearest of four triangles')
        problems += _case(h, [VERTICES[6], VERTICES[7], VERTICES[8]], [(0, 1, 2)], True, None,
                          'every triangle misses')
        problems += _case(h, VERTICES, TRIS, False, None, 'no index list')
        problems += _case(h, VERTICES, [], True, None, 'empty index list')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
