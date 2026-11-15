"""0x42E330 (projectile destructor): the trail's vtable slot 0, the mesh list and the base destructor are stubbed."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

DTOR = 0x0042E330
BASE_DTOR = 0x004AD020
DELETE = 0x005E3E9C
VTABLE = 0x00608B5C

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


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


def _trail_dtor_stub(h, log):
    """vtable slot 0 of the trail: logs (this, flag)"""
    code = _log_ecx(log) + b'\x8B\x44\x24\x04' + _log_eax(log + 4) + b'\xC2\x04\x00'
    return _stub(h, code)


def _base_dtor_stub(h, log):
    return _stub(h, _log_ecx(log) + b'\xC3')


def _delete_stub(h, log):
    return _stub(h, b'\x8B\x44\x24\x04' + _log_eax(log) + b'\xC3')


def _setup(h, trail, meshes, empty_list=False):
    s = h.alloc(0x300, bytes(0x300))
    h.uc.mem_write(s, _dword(0x11111111))
    h.uc.mem_write(s + 0x2c8, _dword(trail))
    h.uc.mem_write(s + 0x1d0, _dword(0xDDDDDDDD))
    buf = 0
    if meshes is not None:
        buf = h.alloc(4 * max(len(meshes), 1), bytes(4 * max(len(meshes), 1)))
        for i, m in enumerate(meshes):
            h.uc.mem_write(buf + 4 * i, _dword(m))
        h.uc.mem_write(s + 0x1c8, _dword(buf))
        h.uc.mem_write(s + 0x1cc, _dword(buf + (0 if empty_list else 4 * len(meshes))))
    return s, buf


def _trail_setup(h, slot0):
    trail = h.alloc(0x300, bytes(0x300))
    vt = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(vt, _dword(slot0))
    h.uc.mem_write(trail, _dword(vt))
    return trail


def test_projectile_dtor(h):
    heap0 = h.heap_ptr
    log = h.alloc(0x20, bytes(0x20))
    slot0 = _trail_dtor_stub(h, log)
    base = _base_dtor_stub(h, log + 0x8)
    delete = _delete_stub(h, log + 0xc)
    _hook(h, BASE_DTOR, base)
    _hook(h, DELETE, delete)
    try:
        problems = []
        for name, with_trail, n_meshes, empty_list in (
                ('trail, 3 meshes', True, 3, False),
                ('no trail, 1 mesh', False, 1, False),
                ('trail, no list', True, None, False),
                ('trail, empty list', True, 1, True),
                ('no trail, no list', False, None, False)):
            trail = _trail_setup(h, slot0) if with_trail else 0
            meshes = [h.alloc(0x40, bytes(0x40)) for _ in range(n_meshes or 0)]
            for m in meshes:
                h.uc.mem_write(m + 0x24, b'\x99' * 4)
            s, buf = _setup(h, trail, meshes, empty_list)
            h.uc.mem_write(log, bytes(0x20))
            diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: s}, ret=None)
            if diffs:
                problems.append('%s: %s' % (name, '; '.join(diffs)))
                continue
            res = h.call(DTOR, regs={UC_X86_REG_ECX: s})
            if res['fault']:
                problems.append('%s: %s' % (name, res['fault']))
                continue
            if _u32(h, s) != h.to_rebuilt(VTABLE):
                problems.append('%s: the vtable is %#x' % (name, _u32(h, s)))
            if with_trail:
                if _u32(h, log) != trail or _u32(h, log + 4) != 1:
                    problems.append('%s: the trail dtor got (%#x, %#x)' % (name, _u32(h, log), _u32(h, log + 4)))
            elif _u32(h, log) or _u32(h, log + 4):
                problems.append('%s: the trail dtor was called' % name)
            if meshes is None:
                if _u32(h, log + 0xc):
                    problems.append('%s: something was freed' % name)
            else:
                if _u32(h, log + 0xc) != buf:
                    problems.append('%s: the array %#x is not freed (got %#x)' % (name, buf, _u32(h, log + 0xc)))
                for i, m in enumerate(meshes):
                    marked = h.uc.mem_read(m + 0x24, 1)[0]
                    if marked != (0x99 if empty_list else 1):
                        problems.append('%s: mesh %d is marked %#x' % (name, i, marked))
            if _u32(h, s + 0x1c8) or _u32(h, s + 0x1cc) or _u32(h, s + 0x1d0):
                problems.append('%s: the mesh vector is (%#x, %#x, %#x)'
                                % (name, _u32(h, s + 0x1c8), _u32(h, s + 0x1cc), _u32(h, s + 0x1d0)))
            if _u32(h, log + 8) != s:
                problems.append('%s: the base dtor got %#x' % (name, _u32(h, log + 8)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
