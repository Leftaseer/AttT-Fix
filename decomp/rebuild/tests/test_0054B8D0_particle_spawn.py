"""0x0054B8D0: one particle is initialized from the system's ranges.  rand, D3DXMatrixRotationYawPitchRoll and
D3DXVec3TransformCoord run in the harness's emulation (srand(1) makes both halves identical); the provider's
slot +4 and the callee 0x0054B2D0 are stubs that log their arguments, so the ten random draws, the angle and
scale chain and the argument layout of the callee are all under test.  The expected values replay the same
arithmetic in Python: the MSVC rand sequence and the row-vector matrix product D3DX uses."""
import math
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_FPCW

FN = 0x0054B8D0
CALLEE = 0x0054B2D0

PHASE = 2.0
POSITION = (1.5, 2.5, 3.5)
POSITION_SCALE = (1.5, 1.5)             # +0x2FC, +0x30C
RANGES = ((0x3b8, 0x3c8, 4.0, 4.0), (0x338, 0x348, -8.0, 8.0), (0x358, 0x368, -8.0, 8.0),
          (0x378, 0x388, 0.25, 0.25), (0x398, 0x3a8, 2.0, 2.0))
LIFETIME = (0.002, 3.0)                 # +0x450, +0x460: the range is 1000*(0.002..3.0)
LIFETIME_SCALE = (1000.0, 500.0)        # +0x430, +0x440
SCALE3 = (2.0, 0.5, 0.25, -0.5)         # +0x3F0, +0x3D8, +0x3DC, +0x3E0
BASE_VEC = (0.5, -0.5, 4.0, 8.0)        # +0x31C
OUT_VEC = (0x11111111, 0x22222222, 0x33333333)
TIME = 12.5
USER = 7
DRAWS = 10

L_COUNT = 0x00
L_EVENTS = 0x08
LOG_SIZE = 0x400

E_OWNER = 0x66
E_VT_X, E_VT_Y, E_VT_Z = 0x67, 0x68, 0x69
E_P1 = 0x70
E_P2 = 0x73
E_P3 = 0x76
E_P4PTR = 0x79
E_P4 = 0x7A
E_F5 = 0x80
E_U11 = 0x86
E_F12, E_F13 = 0x87, 0x88

saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


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


def _arg(offset):
    return b'\x8B\x44\x24' + bytes([offset])


def _arg_mem(offset, byte_offset):
    load = b'\x8B\x44\x24' + bytes([offset])
    if byte_offset < 0x80:
        return load + b'\x8B\x40' + bytes([byte_offset])
    return load + b'\x8B\x80' + _dword(byte_offset)


def _arg_u16(offset):
    return b'\x0F\xB7\x44\x24' + bytes([offset])


def _events(h, log):
    count = struct.unpack('<I', h.uc.mem_read(log + L_COUNT, 4))[0]
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def _provider_stub(log):
    """thiscall: ecx = provider, (owner, out, vec); fills the out vector and logs the owner and the vec"""
    code = _ev(log, E_OWNER, _arg(4))
    code += b'\x8B\x54\x24\x08'
    for i in range(3):
        code += b'\xC7\x82' + _dword(4 * i) + _dword(OUT_VEC[i])
    code += _ev(log, E_VT_X, _arg_mem(12, 0)) + _ev(log, E_VT_Y, _arg_mem(12, 4)) + _ev(log, E_VT_Z, _arg_mem(12, 8))
    return code + b'\xC2\x0C\x00'


def _callee_stub(log):
    code = b''
    for k in range(3):
        for i in range(3):
            code += _ev(log, E_P1 + 3 * k + i, _arg_mem(4 + 4 * k, 4 * i))
    code += _ev(log, E_P4PTR, _arg(16))
    for i in range(4):
        code += _ev(log, E_P4 + i, _arg_mem(16, 4 * i))
    for i in range(6):
        code += _ev(log, E_F5 + i, _arg(20 + 4 * i))
    code += _ev(log, E_U11, _arg_u16(44))
    code += _ev(log, E_F12, _arg(48)) + _ev(log, E_F13, _arg(52))
    return code + b'\xC2\x34\x00'


def _rand_draws(n):
    state, out = 1, []
    for _ in range(n):
        state = (state * 214013 + 2531011) & 0xFFFFFFFF
        out.append((state >> 16) & 0x7FFF)
    return out


def _jitter(lo, hi, draw, rand_max=32767.0):
    return _f32(lo + (hi - lo) * draw / rand_max)


def _rotation(axis, angle):
    c, s = math.cos(angle), math.sin(angle)
    m = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    i, j = {'x': (1, 2), 'y': (2, 0), 'z': (0, 1)}[axis]
    m[i][i], m[i][j], m[j][i], m[j][j] = c, s, -s, c
    return m


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _expected():
    draws = _rand_draws(DRAWS)
    lo, hi = _f32(-0.0 - PHASE), PHASE
    angles = [_f32(_jitter(lo, hi, draws[i]) / 1000.0) for i in range(3)]
    yaw, pitch, roll = angles
    m = _mul(_mul(_rotation('z', roll), _rotation('x', pitch)), _rotation('y', yaw))
    m = [[_f32(x) for x in row] for row in m]
    v = list(POSITION) + [1.0]
    r = [sum(v[k] * m[k][j] for k in range(4)) for j in range(4)]
    pos = [_f32(r[i] / r[3]) for i in range(3)]
    k = _jitter(POSITION_SCALE[0], POSITION_SCALE[1], draws[3])
    pos = [_f32(x * k) for x in pos]
    js = [_jitter(lo_, hi_, draws[4 + i]) for i, (_, _, lo_, hi_) in enumerate(RANGES)]
    life = _jitter(_f32(LIFETIME[0] * 1000.0), _f32(1000.0 * LIFETIME[1]), draws[9])
    sec = _f32(life / 1000.0)
    r430 = _f32(LIFETIME_SCALE[0] * sec)
    r440 = _f32(sec * LIFETIME_SCALE[1])
    a = SCALE3[0]
    sc = [_f32(a * SCALE3[1]), _f32(SCALE3[2] * a), _f32(a * SCALE3[3])]
    want = [(E_OWNER, 0)]
    want += [(E_VT_X + i, _bits(pos[i])) for i in range(3)]
    want += [(E_P1 + i, OUT_VEC[i]) for i in range(3)]
    want += [(E_P2 + i, _bits(pos[i])) for i in range(3)]
    want += [(E_P3 + i, _bits(sc[i])) for i in range(3)]
    want += [(E_P4PTR, 0)]
    want += [(E_P4 + i, _bits(BASE_VEC[i])) for i in range(4)]
    want += [(E_F5 + i, _bits(js[i])) for i in range(5)]
    want += [(E_F5 + 5, _bits(TIME)), (E_U11, USER), (E_F12, _bits(r430)), (E_F13, _bits(r440))]
    return want


def _case(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    system = h.alloc(0x600, bytes(0x600))
    particle = h.alloc(0x100, b'\xEE' * 0x100)
    provider = h.alloc(0x40, b'\x77' * 0x40)
    provider_vt = h.alloc(0x20, bytes(0x20))
    h.uc.mem_write(provider, _dword(provider_vt))
    h.uc.mem_write(provider_vt + 0x04, _dword(_stub(h, _provider_stub(log))))
    _patch(h, CALLEE, b'\xE9' + struct.pack('<i', _stub(h, _callee_stub(log)) - (CALLEE + 5)))

    def setup():
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(system, bytes(0x600))
        fields = {0x23c: PHASE, 0x2cc: POSITION[0], 0x2d0: POSITION[1], 0x2d4: POSITION[2],
                  0x2fc: POSITION_SCALE[0], 0x30c: POSITION_SCALE[1],
                  0x450: LIFETIME[0], 0x460: LIFETIME[1], 0x430: LIFETIME_SCALE[0], 0x440: LIFETIME_SCALE[1],
                  0x3f0: SCALE3[0], 0x3d8: SCALE3[1], 0x3dc: SCALE3[2], 0x3e0: SCALE3[3],
                  0x31c: BASE_VEC[0], 0x320: BASE_VEC[1], 0x324: BASE_VEC[2], 0x328: BASE_VEC[3],
                  0x5e4: TIME}
        for a, b, lo, hi in RANGES:
            fields[a], fields[b] = lo, hi
        for offset, value in fields.items():
            h.uc.mem_write(system + offset, struct.pack('<f', value))
        h.uc.mem_write(system + 0x4d0, struct.pack('<H', USER))
        h.uc.mem_write(system + 0x59c, _dword(provider))

    setup()
    diffs = h.compare(FN, args=(particle,), regs={UC_X86_REG_ECX: system}, ret=None)
    if diffs:
        return [str(d) for d in diffs]

    setup()
    res = h.call(FN, args=(particle,), regs={UC_X86_REG_ECX: system})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    final = 1
    for _ in range(DRAWS):
        final = (final * 214013 + 2531011) & 0xFFFFFFFF
    if struct.unpack('<I', h.uc.mem_read(h.RAND_STATE, 4))[0] != final:
        return ['rand was not drawn %d times' % DRAWS]
    want = [(code, system if code == E_OWNER else system + 0x31c if code == E_P4PTR else value)
            for code, value in _expected()]
    got = _events(h, log)
    if got != want:
        return ['events %r, expected %r' % (got, want)]
    return None


def test_0054B8D0(h):
    heap0 = h.heap_ptr
    # Unicorn starts with a control word that reads as 0, but a later test in the suite leaves a real value
    # behind; pin the precision (0x027F: masked, round to nearest, double) the way the game's CRT sets it.
    control = h.uc.reg_read(UC_X86_REG_FPCW)
    try:
        h.uc.reg_write(UC_X86_REG_FPCW, 0x027F)
        result = _case(h)
        if result:
            return result
    finally:
        _restore(h)
        h.uc.reg_write(UC_X86_REG_FPCW, control)
        h.heap_ptr = heap0
    return None
