"""0x4C3080 wave file open; mmioOpenA, the mmapi imports and the wave header readers are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004C3080
FREE = 0x005E3EBA
EXC1 = 0x004C1D00
EXC2 = 0x00421220
THROW = 0x005E3EC0
POST1 = 0x004C1FB0
POST2 = 0x004C2410
MMIO_SLOT = 0x0060770C
MMIO_SYM = '__imp__mmioOpenA'
NAME_LIT = 0x006115AC
PREFIX_LIT = 0x00611590
SUFFIX_LIT = 0x0060B008
FILE_LIT = 0x006113F0
THROW_INFO = 0x0069916C
INVALIDARG = 0x80070057
MMIO_MAGIC = 0x4F494D4D
OPEN_FLAGS = 0x10000
HANDLE = 0xDEADBEEF
FIELD_0C = 0xC0FFEE11

ORDER = 0x04                      # log+0 is _tag's call counter
FREE_ARG, FREE_COUNT = 0x44, 0x48
E1_SELF, E1_HR, E1_MSG, E1_FILE, E1_LINE, E1_COUNT = 0x4C, 0x50, 0x54, 0x58, 0x5C, 0x60
MMIO_NAME, MMIO_INFO, MMIO_FLAGS, MMIO_COUNT = 0x64, 0x68, 0x6C, 0x70
E2_SELF, E2_MSG, E2_FILE, E2_LINE, E2_COUNT = 0x74, 0x78, 0x7C, 0x80, 0x84
TH_OBJ, TH_TI, TH_COUNT = 0x88, 0x8C, 0x90
P1_SELF, P1_COUNT = 0x94, 0x98
P2_SELF, P2_COUNT = 0x9C, 0xA0
LOG_SIZE = 0xC0

FREE_OP, EXC1_OP, MMIO_OP, EXC2_OP, THROW_OP, P1_OP, P2_OP = range(1, 8)
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


def _import(h, slot, symbol, code):
    stub = _stub(h, code)
    for address in (slot, h.symbols[symbol]):
        _patch(h, address, _dword(stub))


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


def _run(h, name_ptr, buffer, handle):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        self_ = h.alloc(0x80, bytes(0x80))
        h.uc.mem_write(self_, _dword(buffer))
        h.uc.mem_write(self_ + 0xC, _dword(FIELD_0C))
        _hook(h, FREE, _tag(log, FREE_OP) + _arg(4, log + FREE_ARG) + _inc(log, FREE_COUNT) + b'\xC3')
        _hook(h, EXC1, _tag(log, EXC1_OP) + _store_ecx(log, E1_SELF) + _arg(4, log + E1_HR) +
              _arg(8, log + E1_MSG) + _arg(0xC, log + E1_FILE) + _arg(0x10, log + E1_LINE) +
              _inc(log, E1_COUNT) + b'\xC2\x10\x00')
        _import(h, MMIO_SLOT, MMIO_SYM, _tag(log, MMIO_OP) + _arg(4, log + MMIO_NAME) +
                _arg(8, log + MMIO_INFO) + _arg(0xC, log + MMIO_FLAGS) + _inc(log, MMIO_COUNT) +
                b'\xB8' + _dword(handle) + b'\xC2\x0C\x00')
        _hook(h, EXC2, _tag(log, EXC2_OP) + _store_ecx(log, E2_SELF) + _arg(4, log + E2_MSG) +
              _arg(8, log + E2_FILE) + _arg(0xC, log + E2_LINE) + _inc(log, E2_COUNT) + b'\xC2\x0C\x00')
        _hook(h, THROW, _tag(log, THROW_OP) + _arg(4, log + TH_OBJ) + _arg(8, log + TH_TI) +
              _inc(log, TH_COUNT) + b'\xC2\x08\x00')
        _hook(h, POST1, _tag(log, P1_OP) + _store_ecx(log, P1_SELF) + _inc(log, P1_COUNT) + b'\xC3')
        _hook(h, POST2, _tag(log, P2_OP) + _store_ecx(log, P2_SELF) + _inc(log, P2_COUNT) + b'\xC3')

        diffs = h.compare(FN, args=[name_ptr], regs={UC_X86_REG_ECX: self_}, ret=None, mem=False)
        if diffs:
            return diffs, None
        h.uc.mem_write(log, bytes(LOG_SIZE))
        result = h.call(FN, args=[name_ptr], regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']], None
        got = {
            'order': [_u32(h, log + ORDER + 4 * i) for i in range(_u32(h, log))],
            'free_arg': _u32(h, log + FREE_ARG), 'free_count': _u32(h, log + FREE_COUNT),
            'e1_self': _u32(h, log + E1_SELF), 'e1_hr': _u32(h, log + E1_HR),
            'e1_msg': _u32(h, log + E1_MSG), 'e1_file': _u32(h, log + E1_FILE),
            'e1_line': _u32(h, log + E1_LINE), 'e1_count': _u32(h, log + E1_COUNT),
            'mmio_name': _u32(h, log + MMIO_NAME), 'mmio_info': _u32(h, log + MMIO_INFO),
            'mmio_flags': _u32(h, log + MMIO_FLAGS), 'mmio_count': _u32(h, log + MMIO_COUNT),
            'e2_self': _u32(h, log + E2_SELF), 'e2_msg': _u32(h, log + E2_MSG),
            'e2_file': _u32(h, log + E2_FILE), 'e2_line': _u32(h, log + E2_LINE),
            'e2_count': _u32(h, log + E2_COUNT),
            'th_obj': _u32(h, log + TH_OBJ), 'th_ti': _u32(h, log + TH_TI),
            'th_count': _u32(h, log + TH_COUNT),
            'p1_self': _u32(h, log + P1_SELF), 'p1_count': _u32(h, log + P1_COUNT),
            'p2_self': _u32(h, log + P2_SELF), 'p2_count': _u32(h, log + P2_COUNT),
            'handle_field': _u32(h, self_ + 4), 'buffer_field': _u32(h, self_),
            'state_field': _u32(h, self_ + 0x30), 'self': self_,
        }
        info = got['mmio_info']
        got['info'] = [_u32(h, info + 4 * i) for i in range(0x48 // 4)]
        return [], got
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _check_common(got, problems):
    if got['p1_self'] != got['self'] or got['p1_count'] != 1:
        problems.append('wave header descent is missing')
    if got['p2_self'] != got['self'] or got['p2_count'] != 1:
        problems.append('wave format read is missing')
    if got['handle_field'] != HANDLE:
        problems.append('handle field is %#x' % got['handle_field'])
    if got['state_field'] != FIELD_0C:
        problems.append('state field is %#x, want %#x' % (got['state_field'], FIELD_0C))
    if got['mmio_flags'] != OPEN_FLAGS:
        problems.append('open flags are %#x' % got['mmio_flags'])
    info = got['info']
    if info[0] != 0 or info[1] != MMIO_MAGIC or any(info[2:]):
        problems.append('MMIOINFO is %s' % ([hex(x) for x in info],))


def test_open_existing_buffer(h):
    buffer = h.alloc(0x40, bytes(0x40))
    name = h.alloc(0x20, b'C:\\wave\\boom.wav\0')
    diffs, got = _run(h, name, buffer, HANDLE)
    if diffs:
        return diffs
    problems = []
    _check_common(got, problems)
    if got['order'] != [FREE_OP, MMIO_OP, P1_OP, P2_OP]:
        problems.append('call order is %s' % (got['order'],))
    if got['free_arg'] != buffer or got['free_count'] != 1:
        problems.append('old buffer is not released')
    if got['buffer_field'] != 0:
        problems.append('buffer field is not cleared')
    if got['mmio_name'] != name or got['mmio_count'] != 1:
        problems.append('open name is %#x' % got['mmio_name'])
    if got['e1_count'] or got['e2_count'] or got['th_count']:
        problems.append('unexpected exception path')
    return problems or None


def test_open_without_buffer(h):
    name = h.alloc(0x10, b'wave.wav\0')
    diffs, got = _run(h, name, 0, HANDLE)
    if diffs:
        return diffs
    problems = []
    _check_common(got, problems)
    if got['order'] != [MMIO_OP, P1_OP, P2_OP]:
        problems.append('call order is %s' % (got['order'],))
    if got['free_count'] != 0:
        problems.append('empty buffer was released')
    return problems or None


def test_open_failure(h):
    name = h.alloc(0x20, b'C:\\wave\\boom.wav\0')
    diffs, got = _run(h, name, 0, 0)
    if diffs:
        return diffs
    problems = []
    if got['order'] != [MMIO_OP, EXC2_OP, THROW_OP, P1_OP, P2_OP]:
        problems.append('call order is %s' % (got['order'],))
    if got['e2_file'] != FILE_LIT or got['e2_line'] != 0x3E or got['e2_count'] != 1:
        problems.append('exception is (%#x, %#x)' % (got['e2_file'], got['e2_line']))
    if got['th_obj'] != got['e2_self'] or got['th_ti'] != THROW_INFO or got['th_count'] != 1:
        problems.append('thrown object is %#x/%#x' % (got['th_obj'], got['th_ti']))
    message = h._str_get(got['e2_msg'])
    want = b"Error opening wave file 'C:\\wave\\boom.wav'"
    if message != want:
        problems.append('exception message is %r, want %r' % (message, want))
    if got['handle_field'] != 0:
        problems.append('failed handle field is %#x' % got['handle_field'])
    if got['state_field'] != FIELD_0C:
        problems.append('state field is not set on the failure path')
    return problems or None


def test_open_without_name(h):
    buf = h.alloc(0x40, bytes(0x40))
    diffs, got = _run(h, 0, buf, HANDLE)
    if diffs:
        return diffs
    problems = []
    if got['order'] != [EXC1_OP, THROW_OP, FREE_OP, MMIO_OP, P1_OP, P2_OP]:
        problems.append('call order is %s' % (got['order'],))
    if got['e1_hr'] != INVALIDARG or got['e1_file'] != FILE_LIT or got['e1_line'] != 0x31:
        problems.append('exception is (%#x, %#x, %#x)' % (got['e1_hr'], got['e1_file'], got['e1_line']))
    if h._str_get(got['e1_msg']) != b'strFileName':
        problems.append('exception message is %r' % (h._str_get(got['e1_msg']),))
    if got['th_obj'] != got['e1_self'] or got['th_ti'] != THROW_INFO or got['th_count'] != 1:
        problems.append('thrown object is %#x/%#x' % (got['th_obj'], got['th_ti']))
    if got['free_arg'] != buf or got['free_count'] != 1:
        problems.append('old buffer is not released')
    if got['mmio_name'] != 0:
        problems.append('open name is %#x' % got['mmio_name'])
    _check_common(got, problems)
    return problems or None
