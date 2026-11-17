"""0x4268C0 pass renderer; the manager, scene, texture and device virtual methods are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004268C0
MANAGER_INIT = 0x004357F0
MANAGER_SLOT = 0x006CA2C4
DEVICE_SLOT = 0x006C8C10
TEXTURE_VALUE = 0x89ABCDEF
saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


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


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _inc(log):
    return b'\xFF\x05' + _dword(log)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _fixture(h):
    log = h.alloc(0x90, bytes(0x90))
    manager = h.alloc(4, bytes(4))
    _patch(h, MANAGER_SLOT, _dword(manager))
    _hook(h, MANAGER_INIT, b'\x89\x0D' + _dword(log) + _inc(log + 4) + b'\xC3')

    transform = (_arg(4, log + 8) + _arg(8, log + 0x0c) + _arg(12, log + 0x10) +
                 _inc(log + 0x14) + b'\xC2\x0C\x00')
    stream = (_arg(4, log + 0x74) + _arg(8, log + 0x68) + _arg(12, log + 0x18) +
              _arg(16, log + 0x1c) + _arg(20, log + 0x20) + _inc(log + 0x24) + b'\xC2\x14\x00')
    set_texture = (_arg(4, log + 0x6c) + _arg(8, log + 0x4c) + _arg(12, log + 0x50) +
                   _inc(log + 0x54) + b'\xC2\x0C\x00')
    draw = (_arg(4, log + 0x70) + _arg(8, log + 0x58) + _arg(12, log + 0x5c) +
            _arg(16, log + 0x60) + _inc(log + 0x64) + b'\xC2\x10\x00')
    device_vtable = h.alloc(0x194, bytes(0x194))
    for offset, code in ((0xb0, transform), (0x190, stream), (0x104, set_texture), (0x144, draw)):
        h.uc.mem_write(device_vtable + offset, _dword(_stub(h, code)))
    device = h.alloc(4, _dword(device_vtable))
    _patch(h, DEVICE_SLOT, _dword(device))

    scene = h.alloc(4)
    scene_vtable = h.alloc(0x28, bytes(0x28))
    h.uc.mem_write(scene, _dword(scene_vtable))
    count = (b'\x89\x0D' + _dword(log + 0x28) + _arg(8, log + 0x2c) + _inc(log + 0x30) +
             b'\x8B\x4C\x24\x04\xA1' + _dword(log + 0x80) + b'\x89\x01\xC2\x08\x00')
    begin = _arg(4, log + 0x34) + _inc(log + 0x38) + b'\xC2\x04\x00'
    h.uc.mem_write(scene_vtable + 0x18, _dword(_stub(h, count)))
    h.uc.mem_write(scene_vtable + 0x20, _dword(_stub(h, begin)))
    h.uc.mem_write(scene_vtable + 0x24, _dword(_stub(h, _inc(log + 0x3c) + b'\xC3')))
    h.uc.mem_write(scene_vtable + 0x1c, _dword(_stub(h, _inc(log + 0x40) + b'\xC3')))

    getter = (b'\x89\x0D' + _dword(log + 0x44) + _inc(log + 0x48) +
              b'\xB8' + _dword(TEXTURE_VALUE) + b'\xC3')
    texture_vtable = h.alloc(0x2c, bytes(0x2c))
    h.uc.mem_write(texture_vtable + 0x28, _dword(_stub(h, getter)))
    texture = h.alloc(4, _dword(texture_vtable))
    stream_data = h.alloc(0x20, bytes(0x20))
    obj = h.alloc(0x220, bytes(0x220))
    h.uc.mem_write(obj + 0x3c, _dword(scene))
    h.uc.mem_write(obj + 0x208, _dword(stream_data))
    return log, manager, device, scene, texture, stream_data, obj


def test_pass_renderer(h):
    heap0 = h.heap_ptr
    try:
        log, manager, device, scene, texture, stream_data, obj = _fixture(h)
        problems = []
        for passes, with_texture in ((0, True), (2, True), (2, False)):
            h.uc.mem_write(log + 0x80, _dword(passes))
            h.uc.mem_write(obj + 0x44, _dword(texture if with_texture else 0))
            diffs = h.compare(FN, regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
            label = 'passes %d texture %d' % (passes, with_texture)
            if diffs:
                problems += ['%s: %s' % (label, d) for d in diffs]
                continue
            h.uc.mem_write(log, bytes(0x80))
            result = h.call(FN, regs={UC_X86_REG_ECX: obj})
            if result['fault']:
                problems.append('%s: %s' % (label, result['fault']))
                continue
            texture_calls = passes if with_texture else 0
            expected = (
                (0, manager, 'manager'), (4, 1, 'manager calls'),
                (8, device, 'transform device'), (0x0c, 0x100, 'transform state'),
                (0x10, obj + 0x140, 'matrix'), (0x14, 1, 'transform calls'),
                (0x18, stream_data, 'stream data'), (0x1c, 0, 'stream offset'),
                (0x20, 0x14, 'stream stride'), (0x24, 1, 'stream calls'),
                (0x28, scene, 'scene'), (0x2c, 0, 'unused count argument'), (0x30, 1, 'count calls'),
                (0x34, passes - 1 if passes else 0, 'last pass'), (0x38, passes, 'begin calls'),
                (0x3c, passes, 'end calls'), (0x40, 1, 'finish calls'),
                (0x44, texture if texture_calls else 0, 'texture object'),
                (0x48, texture_calls, 'texture getter calls'), (0x4c, 0 if texture_calls else 0, 'texture stage'),
                (0x50, TEXTURE_VALUE if texture_calls else 0, 'texture value'),
                (0x54, texture_calls, 'device texture calls'),
                (0x58, 5 if passes else 0, 'primitive'), (0x5c, 0, 'first vertex'),
                (0x60, 2 if passes else 0, 'primitive count'), (0x64, passes, 'draw calls'),
                (0x68, 0, 'stream index'), (0x6c, device if texture_calls else 0, 'texture device'),
                (0x70, device if passes else 0, 'draw device'), (0x74, device, 'stream device'),
            )
            for offset, want, name in expected:
                got = _u32(h, log + offset)
                if got != want:
                    problems.append('%s: %s is %#x, want %#x' % (label, name, got, want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
