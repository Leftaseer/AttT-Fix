"""0x461A80 Glow::Render; the hero/camera accessors, D3DXMatrixMultiply, the exception constructor, the throw and
the Glow vtable are stubs.  The exception stub also stores the Glow object into 0x006C8E74, modelling that a real
throw never returns, so the post-throw code has a defined continuation in both images."""
import struct

FN = 0x00461A80
HERO = 0x00425F60
CAMERA = 0x00424E70
MUL = 0x005B8020
EXC = 0x00421220
THROW = 0x005E3EC0
GLOW_SLOT = 0x006C8E74
THROW_INFO = 0x0069916C
WV_LIT = 0x0060BC80
PROJ_LIT = 0x0060BC74
NULL_LIT = 0x0060BCD0
INIT_LIT = 0x0060BC8C
FILE_LIT = 0x0060BCC4

ORDER = 0x04
F60_N = 0x64
E70_N = 0x68
MUL_N, MUL_OUT, MUL_A, MUL_B = 0x6C, 0x70, 0x74, 0x78
EXC_N, EXC_THIS, EXC_MSG, EXC_FILE, EXC_LINE = 0x7C, 0x80, 0x84, 0x88, 0x8C
TH_N, TH_OBJ, TH_TI = 0x90, 0x94, 0x98
SET_N, SET_NAME, SET_M = 0x9C, 0xA0, 0xA8
BEG_N, BEG_THIS, BEG_CNT, BEG_ZERO, BEG_VAL = 0xB0, 0xB4, 0xB8, 0xBC, 0xC0
PASS_N, PASS_THIS, PASS_I = 0xC4, 0xC8, 0xD0
DRAW_N, DRAW_THIS = 0xD8, 0xDC
ENDP_N, ENDP_THIS = 0xE4, 0xE8
EFF_N, EFF_THIS = 0xF0, 0xF4
LOG_SIZE = 0x100

F60_OP, E70_OP, MUL_OP, EXC_OP, TH_OP, SET_OP, BEG_OP, PASS_OP, DRAW_OP, ENDP_OP, EFF_OP = range(1, 12)
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


def _tag(log, op):
    return b'\x8B\x15' + _dword(log) + b'\xFF\x05' + _dword(log) + \
        b'\xC7\x04\x95' + _dword(log + ORDER) + _dword(op)


def _store_ecx(log, offset):
    return b'\x89\x0D' + _dword(log + offset)


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _inc(log, offset):
    return b'\xFF\x05' + _dword(log + offset)


def _set(log, offset, value):
    return b'\xC7\x05' + _dword(log + offset) + _dword(value)


def _self_stub(h, log, op, n_off, this_off):
    """__thiscall log of ECX into this_off[count], count in n_off; no stack args."""
    return _stub(h, _tag(log, op) +
                 b'\x8B\xD1' +                                                     # mov edx, ecx
                 b'\x8B\x0D' + _dword(log + n_off) +                               # mov ecx, [n]
                 b'\x89\x14\x8D' + _dword(log + this_off) +                        # mov [this+ecx*4], edx
                 _inc(log, n_off) + b'\xC3')


def _run(h, use_arg, set_glow, count):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        h.uc.mem_write(log + BEG_VAL, _dword(count))
        hero = h.alloc(0x200, bytes(0x200))
        cam = h.alloc(0x100, bytes(0x100))
        arg = h.alloc(0x20, bytes(0x20))
        glow = h.alloc(0x60, bytes(0x60))
        vt_arg = h.alloc(0xD0, bytes(0xD0))
        vt_glow = h.alloc(0x58, bytes(0x58))
        h.uc.mem_write(arg, _dword(vt_arg))
        h.uc.mem_write(glow, _dword(vt_glow))

        _hook(h, HERO, _tag(log, F60_OP) + _inc(log, F60_N) + b'\xB8' + _dword(hero) + b'\xC3')
        _hook(h, CAMERA, _tag(log, E70_OP) + _inc(log, E70_N) + b'\xB8' + _dword(cam) + b'\xC3')
        _hook(h, MUL, _tag(log, MUL_OP) + _arg(4, log + MUL_OUT) + _arg(8, log + MUL_A) +
              _arg(0xC, log + MUL_B) + _inc(log, MUL_N) + b'\x8B\x44\x24\x04' + b'\xC2\x0C\x00')
        _hook(h, EXC, _tag(log, EXC_OP) + _store_ecx(log, EXC_THIS) + _arg(4, log + EXC_MSG) +
              _arg(8, log + EXC_FILE) + _arg(0xC, log + EXC_LINE) + _inc(log, EXC_N) +
              b'\xC7\x05' + _dword(GLOW_SLOT) + _dword(glow) + b'\xC2\x0C\x00')
        _hook(h, THROW, _tag(log, TH_OP) + _arg(4, log + TH_OBJ) + _arg(8, log + TH_TI) +
              _inc(log, TH_N) + b'\xC2\x08\x00')

        setmat = _stub(h, _tag(log, SET_OP) +
                       b'\x8B\xD1' +
                       b'\x8B\x0D' + _dword(log + SET_N) +
                       b'\x8B\x44\x24\x04' + b'\x89\x04\x8D' + _dword(log + SET_NAME) +
                       b'\x8B\x44\x24\x08' + b'\x89\x04\x8D' + _dword(log + SET_M) +
                       _inc(log, SET_N) + b'\xC2\x08\x00')
        begin = _stub(h, _tag(log, BEG_OP) + _store_ecx(log, BEG_THIS) + _arg(4, log + BEG_CNT) +
                      _arg(8, log + BEG_ZERO) +
                      b'\x8B\x44\x24\x04' + b'\x8B\x15' + _dword(log + BEG_VAL) + b'\x89\x10' +
                      _inc(log, BEG_N) + b'\xC2\x08\x00')
        passing = _stub(h, _tag(log, PASS_OP) +
                        b'\x8B\xD1' +
                        b'\x8B\x0D' + _dword(log + PASS_N) +
                        b'\x89\x14\x8D' + _dword(log + PASS_THIS) +
                        b'\x8B\x44\x24\x04' + b'\x89\x04\x8D' + _dword(log + PASS_I) +
                        _inc(log, PASS_N) + b'\xC2\x04\x00')
        draw = _self_stub(h, log, DRAW_OP, DRAW_N, DRAW_THIS)
        endp = _self_stub(h, log, ENDP_OP, ENDP_N, ENDP_THIS)
        eff = _self_stub(h, log, EFF_OP, EFF_N, EFF_THIS)

        for offset, stub in ((0x50, setmat), (0x18, begin), (0x20, passing), (0x24, endp), (0x1C, eff)):
            _patch(h, vt_glow + offset, _dword(stub))
        _patch(h, vt_arg + 0xC8, _dword(draw))
        _patch(h, GLOW_SLOT, _dword(glow if set_glow else 0))
        args = [arg if use_arg else 0]

        diffs = h.compare(FN, args=args, ret=None, mem=False)
        if diffs:
            return diffs, None
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(log + BEG_VAL, _dword(count))
        result = h.call(FN, args=args)
        if result['fault']:
            return [result['fault']], None
        n = _u32(h, log)
        got = {
            'order': [_u32(h, log + ORDER + 4 * i) for i in range(n)],
            'f60_n': _u32(h, log + F60_N), 'e70_n': _u32(h, log + E70_N),
            'mul_n': _u32(h, log + MUL_N), 'mul_out': _u32(h, log + MUL_OUT),
            'mul_a': _u32(h, log + MUL_A), 'mul_b': _u32(h, log + MUL_B),
            'exc_n': _u32(h, log + EXC_N), 'exc_this': _u32(h, log + EXC_THIS),
            'exc_msg': _u32(h, log + EXC_MSG), 'exc_file': _u32(h, log + EXC_FILE),
            'exc_line': _u32(h, log + EXC_LINE),
            'th_n': _u32(h, log + TH_N), 'th_obj': _u32(h, log + TH_OBJ), 'th_ti': _u32(h, log + TH_TI),
            'set_n': _u32(h, log + SET_N),
            'set_name': [_u32(h, log + SET_NAME + 4 * i) for i in range(2)],
            'set_m': [_u32(h, log + SET_M + 4 * i) for i in range(2)],
            'beg_n': _u32(h, log + BEG_N), 'beg_this': _u32(h, log + BEG_THIS),
            'beg_cnt': _u32(h, log + BEG_CNT), 'beg_zero': _u32(h, log + BEG_ZERO),
            'beg_val': _u32(h, log + BEG_VAL),
            'pass_n': _u32(h, log + PASS_N),
            'pass_this': [_u32(h, log + PASS_THIS + 4 * i) for i in range(count)],
            'pass_i': [_u32(h, log + PASS_I + 4 * i) for i in range(count)],
            'draw_n': _u32(h, log + DRAW_N),
            'draw_this': [_u32(h, log + DRAW_THIS + 4 * i) for i in range(count)],
            'endp_n': _u32(h, log + ENDP_N),
            'endp_this': [_u32(h, log + ENDP_THIS + 4 * i) for i in range(count)],
            'eff_n': _u32(h, log + EFF_N), 'eff_this': _u32(h, log + EFF_THIS),
            'glow': glow, 'arg': arg, 'hero': hero, 'cam': cam,
        }
        got['beg_written'] = _u32(h, got['beg_cnt']) if got['beg_cnt'] else None
        return [], got
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _check_render(got, problems, count):
    if got['f60_n'] != 1 or got['mul_n'] != 1 or got['e70_n'] != 2:
        problems.append('hero/camera reads are %d/%d/%d' % (got['f60_n'], got['e70_n'], got['mul_n']))
    if got['mul_a'] != got['hero'] + 0x168 or got['mul_b'] != got['cam'] + 0x88:
        problems.append('multiply inputs are %#x/%#x' % (got['mul_a'], got['mul_b']))
    if got['set_n'] != 2:
        problems.append('matrix sets are %d' % got['set_n'])
        return
    if got['set_name'][0] != WV_LIT or got['set_name'][1] != PROJ_LIT:
        problems.append('matrix names are %#x/%#x' % tuple(got['set_name']))
    if got['set_m'][0] != got['mul_out'] or got['set_m'][1] != got['cam'] + 0xC8:
        problems.append('matrix values are %#x/%#x' % tuple(got['set_m']))
    if got['beg_n'] != 1 or got['beg_this'] != got['glow'] or got['beg_zero'] != 0:
        problems.append('begin is (%d, %#x, %#x)' % (got['beg_n'], got['beg_this'], got['beg_zero']))
    if got['beg_written'] != count:
        problems.append('pass count is %r' % (got['beg_written'],))
    if got['pass_n'] != count or got['pass_this'] != [got['glow']] * count or \
            got['pass_i'] != list(range(count)):
        problems.append('passes are %s/%s' % (got['pass_this'], got['pass_i']))
    if got['draw_n'] != count or got['draw_this'] != [got['arg']] * count:
        problems.append('draws are %d/%s' % (got['draw_n'], got['draw_this']))
    if got['endp_n'] != count or got['endp_this'] != [got['glow']] * count:
        problems.append('pass ends are %d/%s' % (got['endp_n'], got['endp_this']))
    if got['eff_n'] != 1 or got['eff_this'] != got['glow']:
        problems.append('effect end is %d/%#x' % (got['eff_n'], got['eff_this']))


def test_render(h):
    diffs, got = _run(h, True, True, 2)
    if diffs:
        return diffs
    problems = []
    _check_render(got, problems, 2)
    if got['order'] != [F60_OP, E70_OP, E70_OP, MUL_OP, SET_OP, SET_OP, BEG_OP,
                        PASS_OP, DRAW_OP, ENDP_OP, PASS_OP, DRAW_OP, ENDP_OP, EFF_OP]:
        problems.append('call order is %s' % (got['order'],))
    if got['exc_n'] or got['th_n']:
        problems.append('unexpected exception path')
    return problems or None


def test_render_without_argument(h):
    diffs, got = _run(h, False, True, 0)
    if diffs:
        return diffs
    problems = []
    if got['order'][:2] != [EXC_OP, TH_OP]:
        problems.append('call order is %s' % (got['order'],))
        return problems
    if got['order'][2:] != [F60_OP, E70_OP, E70_OP, MUL_OP, SET_OP, SET_OP, BEG_OP, EFF_OP]:
        problems.append('call order is %s' % (got['order'],))
    if got['exc_file'] != FILE_LIT or got['exc_line'] != 0xa or got['exc_n'] != 1:
        problems.append('exception is (%#x, %#x)' % (got['exc_file'], got['exc_line']))
    if h._str_get(got['exc_msg']) != b'Glow::Render : Argument cannot be NULL':
        problems.append('exception message is %r' % (h._str_get(got['exc_msg']),))
    if got['th_obj'] != got['exc_this'] or got['th_ti'] != THROW_INFO or got['th_n'] != 1:
        problems.append('thrown object is %#x/%#x' % (got['th_obj'], got['th_ti']))
    _check_render(got, problems, 0)
    return problems or None


def test_render_without_glow(h):
    diffs, got = _run(h, True, False, 2)
    if diffs:
        return diffs
    problems = []
    if got['order'][:2] != [EXC_OP, TH_OP]:
        problems.append('call order is %s' % (got['order'],))
        return problems
    if got['exc_file'] != FILE_LIT or got['exc_line'] != 0xb or got['exc_n'] != 1:
        problems.append('exception is (%#x, %#x)' % (got['exc_file'], got['exc_line']))
    if h._str_get(got['exc_msg']) != b'Glow::Render : Class must be initialized before call':
        problems.append('exception message is %r' % (h._str_get(got['exc_msg']),))
    if got['th_obj'] != got['exc_this'] or got['th_ti'] != THROW_INFO or got['th_n'] != 1:
        problems.append('thrown object is %#x/%#x' % (got['th_obj'], got['th_ti']))
    _check_render(got, problems, 2)
    return problems or None
