"""Mouse-ray unprojection at 0x424A90 and 0x507670; virtual coordinates and D3DXMatrixInverse are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

INVERSE = 0x005B801A
ONE = 0x0068AE00
HEIGHT = 0x006C8958
WIDTH = 0x006C895C
MATRIX = (0.5, -1.0, 2.0, 0.0,
          0.25, 0.75, -0.5, 0.0,
          1.5, 2.5, -3.0, 0.0,
          10.0, 20.0, 30.0, 1.0)
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
    return (b'\x89\x0D' + _dword(log + offset) +
            b'\xFF\x05' + _dword(log + offset + 4) +
            b'\xD9\x05' + _dword(value) + b'\xC3')


def _inverse_stub(log, matrix):
    code = (b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 0x20) +
            b'\x8B\x4C\x24\x08' + b'\x89\x0D' + _dword(log + 0x24) +
            b'\x8B\x54\x24\x0C' + b'\x89\x15' + _dword(log + 0x28) +
            b'\xFF\x05' + _dword(log + 0x2c))
    for i in range(16):
        code += b'\x8B\x0D' + _dword(matrix + 4 * i)
        code += b'\x89\x88' + _dword(4 * i)
    return code + b'\xC2\x0C\x00'


def _case(h, fn, mouse_off, camera_off, coord_x, coord_y, want_dir, label):
    log = h.alloc(0x40, bytes(0x40))
    obj = h.alloc(0x80, bytes(0x80))
    mouse = h.alloc(4, bytes(4))
    camera = h.alloc(0x100, bytes(0x100))
    coords = h.alloc(8, struct.pack('<ff', coord_x, coord_y))
    matrix = h.alloc(64, struct.pack('<16f', *MATRIX))
    origin = h.alloc(0x0c, b'\xCC' * 0x0c)
    direction = h.alloc(0x0c, b'\xCC' * 0x0c)
    vtable = h.alloc(0x94, bytes(0x94))
    h.uc.mem_write(vtable + 0x8c, _dword(_stub(h, _coord_stub(log, 0x00, coords))))
    h.uc.mem_write(vtable + 0x90, _dword(_stub(h, _coord_stub(log, 0x08, coords + 4))))
    h.uc.mem_write(mouse, _dword(vtable))
    h.uc.mem_write(camera + 0xc8, _dword(_bits(2.0)))
    h.uc.mem_write(camera + 0xdc, _dword(_bits(4.0)))
    h.uc.mem_write(obj + mouse_off, _dword(mouse))
    h.uc.mem_write(obj + camera_off, _dword(camera))
    _hook(h, INVERSE, _inverse_stub(log, matrix))

    diffs = h.compare(fn, args=(origin, direction), regs={UC_X86_REG_ECX: obj}, ret='eax', mem=False)
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]

    h.uc.mem_write(log, bytes(0x40))
    h.uc.mem_write(origin, b'\xCC' * 0x0c)
    h.uc.mem_write(direction, b'\xCC' * 0x0c)
    result = h.call(fn, args=(origin, direction), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['%s: %s' % (label, result['fault'])]

    problems = []
    if result['eax'] != origin:
        problems.append('%s: return is %#x, want origin %#x' % (label, result['eax'], origin))
    if _u32(h, log + 0x04) != 1 or _u32(h, log + 0x0c) != 1 or _u32(h, log + 0x2c) != 1:
        problems.append('%s: call counts are wrong' % label)
    if _u32(h, log + 0x00) != mouse or _u32(h, log + 0x08) != mouse:
        problems.append('%s: virtual coordinate self is wrong' % label)
    if not _u32(h, log + 0x20) or _u32(h, log + 0x24) != 0 or _u32(h, log + 0x28) != camera + 0x88:
        problems.append('%s: inverse arguments are wrong' % label)
    for i, value in enumerate(MATRIX[12:15]):
        if _u32(h, origin + 4 * i) != _bits(value):
            problems.append('%s: origin[%d] is wrong' % (label, i))
    for i, value in enumerate(want_dir):
        if _u32(h, direction + 4 * i) != _bits(value):
            problems.append('%s: direction[%d] is %#x, want %#x' %
                            (label, i, _u32(h, direction + 4 * i), _bits(value)))
    return problems


def test_mouse_ray_unprojection(h):
    heap0 = h.heap_ptr
    try:
        _patch(h, WIDTH, _dword(_bits(256.0)))
        _patch(h, HEIGHT, _dword(_bits(256.0)))
        _patch(h, ONE, struct.pack('<d', 1.0))
        problems = []
        problems += _case(h, 0x00424A90, 0x4c, 0x50, 160.0, 160.0,
                          (1.546875, 2.328125, -2.71875), 'controls')
        problems += _case(h, 0x00507670, 0x70, 0x74, 320.0, 64.0,
                          (1.90625, 1.84375, -1.5625), 'battle')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
