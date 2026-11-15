"""0x42E1E0 (projectile step: base update, then either the trail's own step or the arc flight clock); the base update,
the carry handler, the arc evaluation and the trail's callbacks are stubbed so the test sees what it passes them.
The memory snapshot comparison is off: the log records stack addresses, which differ by the frame layout."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

STEP = 0x0042E1E0
BASE_UPDATE = 0x004AD110
CARRY = 0x0042E030
ARC = 0x0042D9E0
RATE_CONSTANT = 0x0068AE10                  # double divided by +0x2CC

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


def _log_eax(offset):
    return b'\xA3' + _dword(offset)


def _log_ecx(offset):
    return b'\x89\x0D' + _dword(offset)


def _base_stub(h, log):
    """logs (in_eax, this, t) and returns 0x111; the original pops the float"""
    code = _log_eax(log) + _log_ecx(log + 4)
    code += b'\x8B\x44\x24\x04' + _log_eax(log + 8)
    code += b'\xB8' + _dword(0x111) + b'\xC2\x04\x00'
    return _stub(h, code)


def _carry_stub(h, log):
    """logs (in_eax, this, t) and returns its t, so the caller's step is visible in the result"""
    code = _log_eax(log) + _log_ecx(log + 4)
    code += b'\x8B\x44\x24\x04' + _log_eax(log + 8)
    code += b'\x8B\x44\x24\x04' + b'\xC2\x04\x00'
    return _stub(h, code)


def _arc_stub(h, log):
    """logs (this, t); writes the point (1.5, 2.5, 3.5) into out and returns out"""
    code = _log_ecx(log)
    code += b'\x8B\x44\x24\x08' + _log_eax(log + 4)
    code += b'\x8B\x54\x24\x04'                                      # mov edx, [esp+4]
    code += b'\xC7\x02' + _dword(0x3FC00000)
    code += b'\xC7\x42\x04' + _dword(0x40200000)
    code += b'\xC7\x42\x08' + _dword(0x40600000)
    code += b'\x8B\xC2' + b'\xC2\x08\x00'                            # mov eax, edx; ret 8
    return _stub(h, code)


def _check_stub(h, log, value):
    """the trail's +0x220 handler: logs (this, ctx) and returns value"""
    code = _log_ecx(log)
    code += b'\x8B\x44\x24\x04' + _log_eax(log + 4)
    code += b'\xB8' + _dword(value) + b'\xC2\x04\x00'
    return _stub(h, code)


def _trail_step_stub(h, log):
    """the trail's vtable entry 1: logs (this, t) and returns 0xAB"""
    code = _log_ecx(log)
    code += b'\x8B\x44\x24\x04' + _log_eax(log + 4)
    code += b'\xB8' + _dword(0xAB) + b'\xC2\x04\x00'
    return _stub(h, code)


def _trail_setup(h, check_stub, step_stub):
    trail = h.alloc(0x300, bytes(0x300))
    vt = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(vt + 4, _dword(step_stub))
    h.uc.mem_write(trail, _dword(vt))
    h.uc.mem_write(trail + 0x21c, _dword(0x21C0))
    h.uc.mem_write(trail + 0x228, _dword(0x2280))
    h.uc.mem_write(trail + 0x220, _dword(check_stub))
    return trail


def _projectile_setup(h, flying, old_time, limit, rate, trail):
    s = h.alloc(0x300, bytes(0x300))
    h.uc.mem_write(s + 0x2c0, bytes([1 if flying else 0]))
    h.uc.mem_write(s + 0x2b8, _f32(old_time))
    h.uc.mem_write(s + 0x270, _f32(1.0))
    h.uc.mem_write(s + 0x274, _f32(limit))
    h.uc.mem_write(s + 0x2cc, _f32(rate))
    h.uc.mem_write(s + 0x2c8, _dword(trail))
    h.uc.mem_write(s + 0x244, b'\xCC' * 12)
    return s


def test_projectile_step(h):
    heap0 = h.heap_ptr
    log = h.alloc(0x80, bytes(0x80))
    base = _base_stub(h, log)
    carry = _carry_stub(h, log + 0x20)
    arc = _arc_stub(h, log + 0x10)
    step = _trail_step_stub(h, log + 0x40)
    _hook(h, BASE_UPDATE, base)
    _hook(h, CARRY, carry)
    _hook(h, ARC, arc)
    try:
        problems = []
        # path, flying, check result, old time, limit, rate, t
        cases = [
            ('trail idle', 'trail', False, 0, 0.0, 5.0, 2.0, 1.0),
            ('trail steps', 'trail', False, 1, 0.0, 5.0, 2.0, 1.0),
            ('mid-air', 'arc', True, 0, 1.0, 5.0, 2.0, 1.0),
            ('past the duration', 'past', True, 0, 4.5, 5.0, 2.0, 1.0),
            ('past the duration exactly', 'past', True, 0, 5.0, 5.0, 2.0, 1.0),
        ]
        for name, path, flying, check_ret, old, limit, rate, t in cases:
            check = _check_stub(h, log + 0x30, check_ret)
            trail = _trail_setup(h, check, step)
            s = _projectile_setup(h, flying, old, limit, rate, trail)
            h.uc.mem_write(log, bytes(0x80))
            h.uc.mem_write(trail + 0x24c, b'\x77' * 4)
            h.uc.mem_write(trail + 0x24, b'\x77' * 4)
            want = {'trail': 0 if not check_ret else 0xAB,
                    'arc': _bits(t),
                    'past': _bits(limit - old) if old < limit else 0x111}[path]
            diffs = h.compare(STEP, args=[_bits(t)], regs={UC_X86_REG_EAX: 0xE0E0, UC_X86_REG_ECX: s},
                              ret='eax', mem=False)
            if diffs:
                problems.append('%s: %s' % (name, '; '.join(diffs)))
                continue
            res = h.call(STEP, args=[_bits(t)], regs={UC_X86_REG_EAX: 0xE0E0, UC_X86_REG_ECX: s})
            if res['fault']:
                problems.append('%s: %s' % (name, res['fault']))
                continue
            if res['eax'] != want:
                problems.append('%s: result %#x, want %#x' % (name, res['eax'], want))
            if _u32(h, log) != 0xE0E0 or _u32(h, log + 4) != s or _u32(h, log + 8) != _bits(t):
                problems.append('%s: base update got (%#x, %#x, %#x)'
                                % (name, _u32(h, log), _u32(h, log + 4), _u32(h, log + 8)))
            if path == 'trail':
                if _u32(h, log + 0x30) != 0x2280 or _u32(h, log + 0x34) != trail + 0x21c:
                    problems.append('%s: the trail check got (%#x, %#x)'
                                    % (name, _u32(h, log + 0x30), _u32(h, log + 0x34)))
                if check_ret:
                    if _u32(h, log + 0x40) != trail or _u32(h, log + 0x44) != _bits(t):
                        problems.append('%s: the trail step got (%#x, %#x)'
                                        % (name, _u32(h, log + 0x40), _u32(h, log + 0x44)))
                elif any(_u32(h, log + 0x40 + 4 * i) for i in range(2)):
                    problems.append('%s: the trail was stepped' % name)
                if _u32(h, s + 0x2b8) != 0 or _u32(h, trail + 0x24) != 0x77777777:
                    problems.append('%s: the clock or the trail rate changed' % name)
            else:
                if any(_u32(h, log + 0x30 + 4 * i) for i in range(2)):
                    problems.append('%s: the trail was consulted' % name)
            if path == 'arc':
                if _u32(h, log + 0x10) != s + 0x254 or _u32(h, log + 0x14) != _bits(old + t):
                    problems.append('%s: the arc got (%#x, %#x)'
                                    % (name, _u32(h, log + 0x10), _u32(h, log + 0x14)))
                if _u32(h, log + 0x24) != s or _u32(h, log + 0x28) != _bits(t):
                    problems.append('%s: the carry got (%#x, %#x)'
                                    % (name, _u32(h, log + 0x24), _u32(h, log + 0x28)))
                point = _u32(h, log + 0x20)
                if [_u32(h, point + 4 * i) for i in range(3)] != [0x3FC00000, 0x40200000, 0x40600000]:
                    problems.append('%s: the carried point is not the arc point' % name)
                if (_u32(h, s + 0x244), _u32(h, s + 0x248), _u32(h, s + 0x24c)) != (0x3FC00000, 0x40200000,
                                                                                   0x40600000):
                    problems.append('%s: the point (+0x244) is (%#x, %#x, %#x)'
                                    % (name, _u32(h, s + 0x244), _u32(h, s + 0x248), _u32(h, s + 0x24c)))
                if _u32(h, s + 0x2b8) != _bits(old + t) or not h.uc.mem_read(s + 0x2c0, 1)[0]:
                    problems.append('%s: the time (+0x2B8) is %#x, flying %r'
                                    % (name, _u32(h, s + 0x2b8), h.uc.mem_read(s + 0x2c0, 1)[0]))
            if path == 'past':
                rest = limit - old
                if any(_u32(h, log + 0x10 + 4 * i) for i in range(2)):
                    problems.append('%s: the arc was walked' % name)
                if rest > 0:
                    if _u32(h, log + 0x24) != s or _u32(h, log + 0x28) != _bits(rest):
                        problems.append('%s: the carry got (%#x, %#x)'
                                        % (name, _u32(h, log + 0x24), _u32(h, log + 0x28)))
                elif any(_u32(h, log + 0x20 + 4 * i) for i in range(3)):
                    problems.append('%s: the carry was called' % name)
                rate_value = struct.unpack('<d', h.uc.mem_read(h.to_rebuilt(RATE_CONSTANT), 8))[0]
                if h.uc.mem_read(s + 0x2c0, 1)[0]:
                    problems.append('%s: still flying' % name)
                if _u32(h, trail + 0x24c) != 0x77777700:
                    problems.append('%s: the trail +0x24C is %#x' % (name, _u32(h, trail + 0x24c)))
                if _u32(h, trail + 0x24) != _bits(rate_value / rate):
                    problems.append('%s: the trail +0x24 is %#x, want %#x'
                                    % (name, _u32(h, trail + 0x24), _bits(rate_value / rate)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
