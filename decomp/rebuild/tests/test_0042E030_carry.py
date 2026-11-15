"""0x42E030 (projectile path sampling): D3DXVec3TransformCoord, the trail's +0x2F4 handler and the puff emitter
0x00551F60 are stubbed.  The memory snapshot is off: the logs keep the address of the local point."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

CARRY = 0x0042E030
TRANSFORM = 0x005B8026
EMIT = 0x00551F60
GRAVITY = 0x00608B40

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(v):
    return struct.pack('<f', v)


def _bits(v):
    return struct.unpack('<I', struct.pack('<f', v))[0]


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


def _transform_stub(h, log):
    """D3DXVec3TransformCoord: logs (out, v, matrix) and appends (v[0], v[1]) to samples[count++],
    writes 42.0 into out[0], returns out"""
    code = b'\x53'                                                    # push ebx (callee-saved)
    code += b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log)                # mov eax,[esp+8]; mov [log],eax
    code += b'\x8B\x54\x24\x0C' + b'\x89\x15' + _dword(log + 4)       # mov edx,[esp+0xC]; mov [log+4],edx
    code += b'\x8B\x54\x24\x10' + b'\x89\x15' + _dword(log + 8)       # mov edx,[esp+0x10]; mov [log+8],edx
    code += b'\x8B\x15' + _dword(log + 0x14)                           # mov edx,[log+0x14] (count)
    code += b'\x8B\x18' + b'\x89\x1C\xD5' + _dword(log + 0x18)         # mov ebx,[eax]; mov [edx*4+log+0x18],ebx
    code += b'\x8B\x58\x04' + b'\x89\x1C\xD5' + _dword(log + 0x1C)     # mov ebx,[eax+4]; mov [edx*4+log+0x1C],ebx
    code += b'\xFF\x05' + _dword(log + 0x14)                           # inc dword [log+0x14]
    code += b'\xC7\x00' + _dword(0x42280000)                            # mov dword [eax],42.0
    code += b'\x5B'                                                    # pop ebx
    code += b'\xC2\x0C\x00'                                            # ret 12
    return _stub(h, code)


def _trail_stub(h, log):
    """the trail's +0x2F4 handler: logs (this, ctx, point, point[0]) and returns 0x42"""
    code = (b'\x89\x0D' + _dword(log) +                               # mov [log],ecx
            b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4) +       # mov eax,[esp+4]; mov [log+4],eax
            b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 8) +       # mov eax,[esp+8]; mov [log+8],eax
            b'\x8B\x10' + b'\x89\x15' + _dword(log + 0xC) +         # mov edx,[eax]; mov [log+0xC],edx
            b'\xB8' + _dword(0x42) + b'\xC2\x08\x00')               # mov eax,0x42; ret 8
    return _stub(h, code)


def _emit_stub(h, log):
    """0x00551F60: logs the last this and every type argument (types[count], count at +4), returns 0x777"""
    code = (b'\x89\x0D' + _dword(log) +                               # mov [log],ecx
            b'\x8B\x0D' + _dword(log + 4) +                         # mov ecx,[log+4]
            b'\x8B\x54\x24\x04' +                                 # mov edx,[esp+4]
            b'\x89\x14\x8D' + _dword(log + 8) +                     # mov [ecx*4+log+8],edx
            b'\xFF\x05' + _dword(log + 4) +                         # inc dword [log+4]
            b'\xB8' + _dword(0x777) + b'\xC2\x04\x00')            # mov eax,0x777; ret 4
    return _stub(h, code)


def _setup(h, trail, s):
    h.uc.mem_write(s + 0x254, _f32(3.0))
    h.uc.mem_write(s + 0x270, _f32(2.0))
    h.uc.mem_write(s + 0x274, _f32(1.0))
    h.uc.mem_write(s + 0x2b8, _f32(0.0))
    h.uc.mem_write(s + 0x2c8, _dword(trail))
    h.uc.mem_write(s + 0x2cc, _f32(1000.0))
    h.uc.mem_write(s + 0x2d0, _f32(1000.0))
    h.uc.mem_write(s + 0x2d4, _f32(0.0))
    h.uc.mem_write(s + 0x2d8, _f32(0.0))


def test_carry_samples_the_path(h):
    """two steps of 1.0 out of a 2.5 budget: the point is transformed and handed to the trail, the puff is type 1
    then 3 (the counter restarted), and the budget is 0.5 afterwards"""
    heap0 = h.heap_ptr
    log = h.alloc(0x80, bytes(0x80))
    tr = _transform_stub(h, log)
    trail_cb = _trail_stub(h, log + 0x30)
    emit = _emit_stub(h, log + 0x50)
    _hook(h, TRANSFORM, tr)
    _hook(h, EMIT, emit)
    try:
        problems = []
        trail = h.alloc(0x300, bytes(0x300))
        h.uc.mem_write(trail + 0x2f4, _dword(trail_cb))
        h.uc.mem_write(trail + 0x2f8, _dword(0x2F800000))
        s = h.alloc(0x300, bytes(0x300))
        _setup(h, trail, s)
        diffs = h.compare(CARRY, args=[_bits(2.5)], regs={UC_X86_REG_ECX: s, UC_X86_REG_EAX: 0xE0E0},
                          ret='eax', mem=False)
        if diffs:
            return ['; '.join(diffs)]
        h.uc.mem_write(log, bytes(0x80))
        res = h.call(CARRY, args=[_bits(2.5)], regs={UC_X86_REG_ECX: s, UC_X86_REG_EAX: 0xE0E0})
        if res['fault']:
            return [res['fault']]
        if res['eax'] != 0x777:
            problems.append('returned %#x' % res['eax'])
        point = _u32(h, log)
        if point != _u32(h, log + 4) or point == 0:
            problems.append('the transform got (%#x, %#x)' % (_u32(h, log), _u32(h, log + 4)))
        if _u32(h, log + 8) != s + 0x278:
            problems.append('the matrix is %#x' % _u32(h, log + 8))
        if _u32(h, log + 0x14) != 2:
            problems.append('%d samples' % _u32(h, log + 0x14))
        xs = [(_u32(h, log + 0x18), _u32(h, log + 0x1c)), (_u32(h, log + 0x20), _u32(h, log + 0x24))]
        ys = [struct.unpack('<f', struct.pack('<I', p[1]))[0] for p in xs]
        if [p[0] for p in xs] != [0x3FC00000, 0x40600000] or [round(y, 7) for y in ys] != [-0.000135, -0.000735]:
            problems.append('the samples are %s' % ', '.join('(%#x, %#x)' % p for p in xs))
        if (_u32(h, log + 0x30), _u32(h, log + 0x34), _u32(h, log + 0x38)) != (0x2F800000, trail + 0x2e4, point):
            problems.append('the trail got (%#x, %#x, %#x)'
                            % (_u32(h, log + 0x30), _u32(h, log + 0x34), _u32(h, log + 0x38)))
        if _u32(h, log + 0x3C) != 0x42280000:
            problems.append('the trail point[0] is %#x' % _u32(h, log + 0x3C))
        if _u32(h, log + 0x54) != 2 or _u32(h, log + 0x58) != 1 or _u32(h, log + 0x5C) != 3:
            problems.append('the puff types are %#x, %#x'
                            % (_u32(h, log + 0x58), _u32(h, log + 0x5C)))
        if _u32(h, log + 0x50) != trail:
            problems.append('the puffs got %#x' % _u32(h, log + 0x50))
        if struct.unpack('<f', h.uc.mem_read(s + 0x2d4, 4))[0] != 0.5:
            problems.append('the budget is %r' % struct.unpack('<f', h.uc.mem_read(s + 0x2d4, 4))[0])
        if struct.unpack('<f', h.uc.mem_read(s + 0x2d8, 4))[0] != 1.0:
            problems.append('the counter is %r' % struct.unpack('<f', h.uc.mem_read(s + 0x2d8, 4))[0])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_carry_below_the_step(h):
    """a budget under one step does nothing but add up; EAX comes back untouched"""
    heap0 = h.heap_ptr
    log = h.alloc(0x80, bytes(0x80))
    tr = _transform_stub(h, log)
    trail_cb = _trail_stub(h, log + 0x30)
    emit = _emit_stub(h, log + 0x50)
    _hook(h, TRANSFORM, tr)
    _hook(h, EMIT, emit)
    try:
        problems = []
        trail = h.alloc(0x300, bytes(0x300))
        h.uc.mem_write(trail + 0x2f4, _dword(trail_cb))
        s = h.alloc(0x300, bytes(0x300))
        _setup(h, trail, s)
        diffs = h.compare(CARRY, args=[_bits(0.5)], regs={UC_X86_REG_ECX: s, UC_X86_REG_EAX: 0xE0E0},
                          ret='eax', mem=False)
        if diffs:
            return ['; '.join(diffs)]
        h.uc.mem_write(log, bytes(0x80))
        res = h.call(CARRY, args=[_bits(0.5)], regs={UC_X86_REG_ECX: s, UC_X86_REG_EAX: 0xE0E0})
        if res['fault']:
            return [res['fault']]
        if res['eax'] != 0xE0E0:
            problems.append('returned %#x' % res['eax'])
        if any(_u32(h, log + 4 * i) for i in range(0x20)):
            problems.append('something was called')
        if struct.unpack('<f', h.uc.mem_read(s + 0x2d4, 4))[0] != 0.5:
            problems.append('the budget is %r' % struct.unpack('<f', h.uc.mem_read(s + 0x2d4, 4))[0])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
