"""0x4740C0 mask-texture constructor; bitmap, pixel and allocation routines are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004740C0
BITMAP_CTOR = 0x00458AF0
BITMAP_OPEN = 0x00458B50
BITMAP_DTOR = 0x00458B20
NEW_ARRAY = 0x005E3B10
DELETE_ARRAY = 0x005E3EBA
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


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _log_ecx(log, offset):
    return b'\x89\x0D' + _dword(log + offset) + b'\xFF\x05' + _dword(log + offset + 4)


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _fixture(h):
    log = h.alloc(0x60, bytes(0x60))
    obj = h.alloc(0x20, bytes(0x20))
    source = h.alloc(0x20, bytes(0x20))
    mask = h.alloc(0x20, bytes(0x20))
    old_mask = h.alloc(0x20, bytes(0x20))
    colors = h.alloc(0x10, struct.pack('<IIII', 0x00112233, 0x00445566, 0x00778899, 0x00AABBCC))

    pixel = _stub(h, _log_ecx(log, 0x14) + _arg(4, log + 0x1c) + _arg(8, log + 0x20) +
                  _arg(0x0c, log + 0x24) + b'\x8B\x44\x24\x0C\xD1\xE0\x03\x44\x24\x08' +
                  b'\x8D\x04\x85' + _dword(colors) + b'\xC2\x0C\x00')
    _hook(h, BITMAP_CTOR, _log_ecx(log, 0x00) + b'\xC3')
    _hook(h, BITMAP_OPEN, _log_ecx(log, 0x08) + _arg(4, log + 0x10) +
          b'\x8B\xC1' + b'\xA1' + _dword(log + 0x40) + b'\x89\x41\x18' +
          b'\xA1' + _dword(log + 0x44) + b'\x89\x41\x1C' +
          b'\xC7\x41\x08' + _dword(pixel) + b'\xC2\x04\x00')
    _hook(h, BITMAP_DTOR, _log_ecx(log, 0x28) + b'\xC3')
    _hook(h, NEW_ARRAY, _arg(4, log + 0x38) + b'\xFF\x05' + _dword(log + 0x3c) +
          b'\xB8' + _dword(mask) + b'\xC3')
    _hook(h, DELETE_ARRAY, _arg(4, log + 0x30) + b'\xFF\x05' + _dword(log + 0x34) + b'\xC3')
    return log, obj, source, mask, old_mask


def _check(h, fixture, width, height, with_old):
    log, obj, source, mask, old_mask = fixture
    h.uc.mem_write(obj, bytes(0x20))
    h.uc.mem_write(obj + 0x0c, _dword(old_mask if with_old else 0))
    h.uc.mem_write(obj + 0x10, _dword(0xDEADBEEF))
    h.uc.mem_write(log + 0x40, _dword(width))
    h.uc.mem_write(log + 0x44, _dword(height))
    label = '%dx%d old %d' % (width, height, with_old)
    diffs = h.compare(FN, args=(source,), regs={UC_X86_REG_ECX: obj}, ret='eax', mem=False)
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]
    h.uc.mem_write(log, bytes(0x40))
    result = h.call(FN, args=(source,), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['%s: %s' % (label, result['fault'])]
    problems = []
    size = width * height
    expected_fields = ((0, 0x0060E9D0), (4, 0), (8, 0x0060E9C8),
                       (0x0c, mask if size else 0), (0x10, size), (0x14, width), (0x18, height))
    for offset, want in expected_fields:
        got = _u32(h, obj + offset)
        if got != want:
            problems.append('%s: field +%#x is %#x, want %#x' % (label, offset, got, want))
    if result['eax'] != obj:
        problems.append('%s: return value is %#x, want %#x' % (label, result['eax'], obj))
    expected_logs = ((0x04, 1, 'bitmap constructor calls'), (0x0c, 1, 'bitmap open calls'),
                     (0x10, source, 'bitmap source'), (0x18, size, 'pixel calls'),
                     (0x2c, 1, 'bitmap destructor calls'), (0x30, 0, 'deleted buffer'),
                     (0x34, 0, 'delete calls'), (0x38, size if size else 0, 'allocation size'),
                     (0x3c, int(bool(size)), 'allocation calls'))
    for offset, want, name in expected_logs:
        got = _u32(h, log + offset)
        if got != want:
            problems.append('%s: %s is %#x, want %#x' % (label, name, got, want))
    if size:
        if _u32(h, log + 0x1c) == 0 or _u32(h, log + 0x20) != width - 1 or _u32(h, log + 0x24) != height - 1:
            problems.append('%s: pixel callback arguments are wrong' % label)
        expected = bytes((0x22, 0x55, 0x88, 0xBB)) * (size // 4)
        expected += bytes((0x22, 0x55, 0x88))[:size % 4]
        got = bytes(h.uc.mem_read(mask, size))
        if got != expected:
            problems.append('%s: mask bytes are %s, want %s' % (label, got.hex(), expected.hex()))
    return problems


def test_mask_texture_constructor(h):
    heap0 = h.heap_ptr
    try:
        fixture = _fixture(h)
        problems = []
        for case in ((2, 2, True), (2, 2, False), (0, 3, True)):
            problems += _check(h, fixture, *case)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
