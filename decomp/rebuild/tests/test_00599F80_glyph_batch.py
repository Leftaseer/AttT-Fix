"""0x00599F80: the int (x, y) pairs plus the source object offsets make 28-byte vertices (u = 0.5, v = 1.0, the
color and two zero floats), the shared batch state is initialized once (nine zeroed dwords at 0x008D125C and
0x005E3F71(0x00606210)), and the global renderer runs its begin / state / strip / end slots before the vertices
are deleted.  operator new[], operator delete[] and the one-time guard are stubs; the renderer, its slots and the
out object are stubs that log their arguments."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00599F80
NEW = 0x005E3B10
DELETE = 0x005E3EBA
GUARD = 0x005E3F71
GUARD_OBJ = 0x00606210
RANGE = 0x008D125C
LOCK_GLOBAL = 0x008D1260
RENDERER_GLOBAL = 0x008D127C
FLAG = 0x008D1280
COLOR_GLOBAL = 0x006C8280

COLOR = 0xCAFEBABE
DX, DY = -5, 7
PAIRS = [(10, 20), (-3, 4), (70000, -70000)]
STRIDE = 0x1c

L_COUNT = 0x00
L_EVENTS = 0x08
LOG_SIZE = 0x200

E_LOCK = 0x01
E_BEGIN = 0x02
E_SET = 0x03
E_SETVAL = 0x04
E_STATE_A = 0x10
E_STATE_B = 0x11
E_STATE_C = 0x12
E_DRAW_TYPE = 0x20
E_DRAW_COUNT = 0x21
E_DRAW_PTR = 0x22
E_DRAW_STRIDE = 0x23
E_END = 0x30
E_RELEASE = 0x40
E_NEW = 0x50
E_DELETE = 0x51
E_GUARD = 0x60
E_RANGE = 0x61

SELF = b'\x8B\x44\x24\x04'
ARG1 = b'\x8B\x44\x24\x08'
ARG2 = b'\x8B\x44\x24\x0C'
ARG3 = b'\x8B\x44\x24\x10'
ARG4 = b'\x8B\x44\x24\x14'

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


def _lock_stub(log):
    return _ev(log, E_LOCK, SELF) + b'\xC2\x04\x00'


def _begin_stub(log, out_obj):
    return (b'\x8B\x44\x24\x08' + b'\xC7\x00' + _dword(out_obj) +
            _ev(log, E_BEGIN, SELF) + b'\xC2\x08\x00')


def _set_stub(log):
    return _ev(log, E_SET, SELF) + _ev(log, E_SETVAL, ARG1) + b'\xC2\x08\x00'


def _state_stub(log):
    return (_ev(log, E_STATE_A, ARG1) + _ev(log, E_STATE_B, ARG2) + _ev(log, E_STATE_C, ARG3) +
            b'\xC2\x10\x00')


def _draw_stub(log):
    return (_ev(log, E_DRAW_TYPE, ARG1) + _ev(log, E_DRAW_COUNT, ARG2) + _ev(log, E_DRAW_PTR, ARG3) +
            _ev(log, E_DRAW_STRIDE, ARG4) + b'\xC2\x14\x00')


def _end_stub(log):
    return _ev(log, E_END, ARG1) + b'\xC2\x08\x00'


def _release_stub(log):
    return _ev(log, E_RELEASE, SELF) + b'\xC2\x04\x00'


def _new_stub(log, buffer):
    return _ev(log, E_NEW, SELF) + b'\xB8' + _dword(buffer) + b'\xC3'


def _new_fail_stub(log):
    return _ev(log, E_NEW, SELF) + b'\x33\xC0\xC3'


def _delete_stub(log):
    return _ev(log, E_DELETE, SELF) + b'\xC3'


def _guard_stub(log, renderer, lock):
    """logs its argument and the nine dwords it should find zeroed, then installs the objects it stands for"""
    code = _ev(log, E_GUARD, SELF)
    for i in range(9):
        code += _ev(log, E_RANGE + i, b'\xA1' + _dword(RANGE + 4 * i))
    code += b'\xC7\x05' + _dword(RENDERER_GLOBAL) + _dword(renderer)
    code += b'\xC7\x05' + _dword(LOCK_GLOBAL) + _dword(lock)
    return code + b'\xC3'


def _case(h, count, fail=False, init=False, label=''):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    this = h.alloc(0x200, bytes(0x200))
    pairs = h.alloc(8 * max(count, 1), b''.join(struct.pack('<ii', *p) for p in PAIRS[:count]) +
                    bytes(8 * max(count - len(PAIRS), 0)))
    verts = h.alloc(STRIDE * max(count, 1) + 8, b'\xCC' * (STRIDE * max(count, 1) + 8))
    out_obj = h.alloc(0x40, b'\xDD' * 0x40)
    lock = h.alloc(0x20, b'\x11' * 0x20)
    renderer = h.alloc(0x40, b'\x22' * 0x40)
    lock_vt = h.alloc(0x40, bytes(0x40))
    renderer_vt = h.alloc(0x180, bytes(0x180))
    out_vt = h.alloc(0x20, bytes(0x20))
    h.uc.mem_write(lock, _dword(lock_vt))
    h.uc.mem_write(lock_vt + 0x28, _dword(_stub(h, _lock_stub(log))))
    h.uc.mem_write(renderer, _dword(renderer_vt))
    for offset, code in ((0x160, _begin_stub(log, out_obj)), (0x164, _set_stub(log)),
                         (0x10c, _state_stub(log)), (0x14c, _draw_stub(log)), (0x15c, _end_stub(log))):
        h.uc.mem_write(renderer_vt + offset, _dword(_stub(h, code)))
    h.uc.mem_write(out_obj, _dword(out_vt))
    h.uc.mem_write(out_vt + 0x08, _dword(_stub(h, _release_stub(log))))
    _hook(h, NEW, _new_fail_stub(log) if fail else _new_stub(log, verts))
    _hook(h, DELETE, _delete_stub(log))
    _hook(h, GUARD, _guard_stub(log, renderer, lock))

    def setup():
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(this, bytes(0x200))
        h.uc.mem_write(this + 0x174, _dword(DX))
        h.uc.mem_write(this + 0x178, _dword(DY))
        h.uc.mem_write(verts, b'\xCC' * (STRIDE * max(count, 1) + 8))
        if init:
            h.uc.mem_write(RANGE, _dword(0xAAAAAAAA) * 9)
            h.uc.mem_write(FLAG, _dword(0x100))
        else:
            h.uc.mem_write(RANGE, _dword(0xAAAAAAAA) * 9)
            h.uc.mem_write(LOCK_GLOBAL, _dword(lock))
            h.uc.mem_write(RENDERER_GLOBAL, _dword(renderer))
            h.uc.mem_write(FLAG, _dword(1))
        h.uc.mem_write(COLOR_GLOBAL, _dword(COLOR))

    setup()
    diffs = h.compare(FN, args=(pairs, count, COLOR), regs={UC_X86_REG_ECX: this}, ret='eax')
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]

    setup()
    res = h.call(FN, args=(pairs, count, COLOR), regs={UC_X86_REG_ECX: this})
    if res['fault']:
        return ['%s: replacement faulted: %s' % (label, res['fault'])]
    want = 0x8007000E if fail else 0
    if res['eax'] != want:
        return ['%s: returned %08X, expected %08X' % (label, res['eax'], want)]

    events = [(E_NEW, STRIDE * count)]
    if init:
        events.append((E_GUARD, GUARD_OBJ))
        events += [(E_RANGE + i, 0) for i in range(9)]
    if not fail:
        events += [(E_LOCK, lock), (E_BEGIN, renderer), (E_SET, renderer), (E_SETVAL, COLOR)]
        events += [(E_STATE_A, 0), (E_STATE_B, 1), (E_STATE_C, 3)]
        events += [(E_STATE_A, 0), (E_STATE_B, 4), (E_STATE_C, 3)]
        events += [(E_DRAW_TYPE, 3), (E_DRAW_COUNT, (count - 1) & 0xFFFFFFFF), (E_DRAW_PTR, verts),
                   (E_DRAW_STRIDE, STRIDE)]
        events += [(E_STATE_A, 0), (E_STATE_B, 1), (E_STATE_C, 4)]
        events += [(E_STATE_A, 0), (E_STATE_B, 4), (E_STATE_C, 4)]
        events += [(E_END, out_obj), (E_RELEASE, out_obj), (E_DELETE, verts)]
    got = _events(h, log)
    if got != events:
        return ['%s: events %r, expected %r' % (label, got, events)]

    flag = _u32(h, FLAG)
    want_flag = 0x101 if init else 1
    if flag != want_flag:
        return ['%s: flag is %08X, expected %08X' % (label, flag, want_flag)]
    if init:
        if _u32(h, LOCK_GLOBAL) != lock or _u32(h, RENDERER_GLOBAL) != renderer:
            return ['%s: the guard did not install its objects' % label]
    if not fail:
        for i in range(count):
            x, y = PAIRS[i]
            got = struct.unpack('<7I', h.uc.mem_read(verts + i * STRIDE, STRIDE))
            want = (struct.unpack('<I', struct.pack('<f', float(x + DX)))[0],
                    struct.unpack('<I', struct.pack('<f', float(y + DY)))[0],
                    0x3F000000, 0x3F800000, COLOR, 0, 0)
            if got != want:
                return ['%s: vertex %d is %r, expected %r' % (label, i, got, want)]
        tail = bytes(h.uc.mem_read(verts + STRIDE * count, STRIDE * max(count, 1) + 8 - STRIDE * count))
        if tail != b'\xCC' * len(tail):
            return ['%s: the vertices past the last one were written' % label]
    elif bytes(h.uc.mem_read(verts, STRIDE * max(count, 1) + 8)) != b'\xCC' * (STRIDE * max(count, 1) + 8):
        return ['%s: the vertices were written on a failed allocation' % label]
    return None


def test_00599F80(h):
    heap0 = h.heap_ptr
    try:
        for case in (dict(count=3, label='three pairs'),
                     dict(count=0, label='no pairs'),
                     dict(count=1, label='one pair'),
                     dict(count=2, init=True, label='first use of the batch state'),
                     dict(count=2, fail=True, label='allocation failure')):
            result = _case(h, **case)
            if result:
                return result
    finally:
        _restore(h)
        h.heap_ptr = heap0
    return None
