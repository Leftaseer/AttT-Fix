"""0x478700 mesh .gdl open and node visit; the CGameFile reader, the visitor and the exception path are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00478700
OPEN = 0x00459290
CLOSE = 0x00459010
KILL = 0x00459170
VISIT = 0x00475AF0
EXC2 = 0x00421220
THROW = 0x005E3EC0
PREFIX_LIT = 0x0060EB3C
FILE_LIT = 0x0060EA44
THROW_INFO = 0x0069916C
LINE = 0x690
VALUE = 0x3F800000

ORDER = 0x04                      # log+0 is _tag's call counter
OPEN_SELF, OPEN_NAME, OPEN_NOLOAD, OPEN_COUNT = 0x40, 0x44, 0x48, 0x4C
CLOSE_SELF, CLOSE_COUNT = 0x50, 0x54
KILL_SELF, KILL_COUNT = 0x58, 0x5C
VF1_SELF, VF1_SCRATCH, VF1_VALUE, VF1_COUNT = 0x60, 0x64, 0x68, 0x6C
VF2_SELF, VF2_SCRATCH, VF2_VALUE, VF2_COUNT = 0x70, 0x74, 0x78, 0x7C
VISIT_COUNT = 0x80
VISIT_SELFS, VISIT_SCRATCHES, VISIT_VALUES = 0x90, 0xA0, 0xB0
EXC_SELF, EXC_MSG, EXC_FILE, EXC_LINE, EXC_COUNT = 0xC0, 0xC4, 0xC8, 0xCC, 0xD0
TH_OBJ, TH_TI, TH_COUNT = 0xD4, 0xD8, 0xDC
LOG_SIZE = 0xF0

OPEN_OP, VF_OP, VISIT_OP, CLOSE_OP, KILL_OP, EXC2_OP, THROW_OP = range(1, 8)
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


def _arr(offset, count_slot, array, log):
    # log+array[calls-1] = the stub argument (the caller has just counted the call)
    return b'\x8B\x44\x24' + bytes([offset]) + b'\x8B\x15' + _dword(log + count_slot) + b'\x83\xEA\x01' + \
        b'\x89\x04\x95' + _dword(log + array)


def _arr_ecx(count_slot, array, log):
    return b'\x8B\x15' + _dword(log + count_slot) + b'\x83\xEA\x01' + b'\x89\x0C\x95' + _dword(log + array)


def _inc(log, offset):
    return b'\xFF\x05' + _dword(log + offset)


def _stub_call(log, op, self_offs, arg_offs, count_offs, pop):
    code = _tag(log, op) + _store_ecx(log, self_offs)
    for off, dest in arg_offs:
        code += _arg(off, log + dest)
    return code + _inc(log, count_offs) + (b'\xC3' if pop == 0 else b'\xC2' + struct.pack('<H', pop))


def _build(h, log, name, nodes):
    """nodes: list of (child count, vf slot) with at most two nodes; returns the mesh, interfaces and children"""
    this_ = h.alloc(0x48, bytes(0x48))
    h._str_set(this_, name)
    n = max(len(nodes), 1)
    table = h.alloc(0x44 * n, bytes(0x44 * n))
    slots = [(VF1_SELF, VF1_SCRATCH, VF1_VALUE, VF1_COUNT), (VF2_SELF, VF2_SCRATCH, VF2_VALUE, VF2_COUNT)]
    interfaces, children = [], []
    for i, (nchild, slot) in enumerate(nodes):
        node = table + i * 0x44
        itf = h.alloc(0x40, bytes(0x40))
        vt = h.alloc(0x20, bytes(0x20))
        vf = _stub(h, _stub_call(log, VF_OP, *slots[slot][:1], [(4, slots[slot][1]), (8, slots[slot][2])],
                                 slots[slot][3], 8))
        h.uc.mem_write(vt + 0x18, _dword(vf))
        h.uc.mem_write(itf, _dword(vt))
        h.uc.mem_write(node + 0x2C, _dword(itf))
        h.uc.mem_write(node + 0x3C, _dword(nchild))
        cb = h.alloc(max(0x44 * nchild, 0x10), bytes(max(0x44 * nchild, 0x10)))
        h.uc.mem_write(node + 0x40, _dword(cb))
        interfaces.append(itf)
        children.append(cb)
    h.uc.mem_write(this_ + 0x30, _dword(len(nodes)))
    h.uc.mem_write(this_ + 0x34, _dword(table))
    h.uc.mem_write(this_ + 0x38, _dword(VALUE))
    return this_, interfaces, children


def _run(h, name, nodes, opened):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        this_, interfaces, children = _build(h, log, name, nodes)
        _hook(h, OPEN, _tag(log, OPEN_OP) + _store_ecx(log, OPEN_SELF) + _arg(4, log + OPEN_NAME) +
              _arg(8, log + OPEN_NOLOAD) + _inc(log, OPEN_COUNT) + b'\xC6\x41\x2C' +
              bytes([1 if opened else 0]) + b'\xC2\x08\x00')
        _hook(h, CLOSE, _stub_call(log, CLOSE_OP, CLOSE_SELF, [], CLOSE_COUNT, 0))
        _hook(h, KILL, _stub_call(log, KILL_OP, KILL_SELF, [], KILL_COUNT, 0))
        _hook(h, VISIT, _tag(log, VISIT_OP) + _inc(log, VISIT_COUNT) + _arr_ecx(VISIT_COUNT, VISIT_SELFS, log) +
              _arr(4, VISIT_COUNT, VISIT_SCRATCHES, log) + _arr(8, VISIT_COUNT, VISIT_VALUES, log) + b'\xC2\x08\x00')
        _hook(h, EXC2, _stub_call(log, EXC2_OP, EXC_SELF, [(4, EXC_MSG), (8, EXC_FILE), (0xC, EXC_LINE)],
                                  EXC_COUNT, 0xC))
        _hook(h, THROW, _tag(log, THROW_OP) + _arg(4, log + TH_OBJ) + _arg(8, log + TH_TI) +
              _inc(log, TH_COUNT) + b'\xC2\x08\x00')
        diffs = h.compare(FN, args=[], regs={UC_X86_REG_ECX: this_}, ret=None, mem=False)
        if diffs:
            return diffs, None, None
        h.uc.mem_write(log, bytes(LOG_SIZE))
        result = h.call(FN, args=[], regs={UC_X86_REG_ECX: this_})
        if result['fault']:
            return [result['fault']], None, None
        nvisit = _u32(h, log + VISIT_COUNT)
        got = {
            'order': [_u32(h, log + ORDER + 4 * i) for i in range(_u32(h, log))],
            'open_self': _u32(h, log + OPEN_SELF), 'open_name': _u32(h, log + OPEN_NAME),
            'open_noload': _u32(h, log + OPEN_NOLOAD), 'open_count': _u32(h, log + OPEN_COUNT),
            'close_self': _u32(h, log + CLOSE_SELF), 'close_count': _u32(h, log + CLOSE_COUNT),
            'kill_self': _u32(h, log + KILL_SELF), 'kill_count': _u32(h, log + KILL_COUNT),
            'vf1_self': _u32(h, log + VF1_SELF), 'vf1_scratch': _u32(h, log + VF1_SCRATCH),
            'vf1_value': _u32(h, log + VF1_VALUE), 'vf1_count': _u32(h, log + VF1_COUNT),
            'vf2_self': _u32(h, log + VF2_SELF), 'vf2_scratch': _u32(h, log + VF2_SCRATCH),
            'vf2_value': _u32(h, log + VF2_VALUE), 'vf2_count': _u32(h, log + VF2_COUNT),
            'visit_count': nvisit,
            'visit_selfs': [_u32(h, log + VISIT_SELFS + 4 * i) for i in range(min(nvisit, 4))],
            'visit_scratch_args': [_u32(h, log + VISIT_SCRATCHES + 4 * i) for i in range(min(nvisit, 4))],
            'visit_values': [_u32(h, log + VISIT_VALUES + 4 * i) for i in range(min(nvisit, 4))],
            'exc_self': _u32(h, log + EXC_SELF), 'exc_msg': _u32(h, log + EXC_MSG),
            'exc_file': _u32(h, log + EXC_FILE), 'exc_line': _u32(h, log + EXC_LINE),
            'exc_count': _u32(h, log + EXC_COUNT),
            'th_obj': _u32(h, log + TH_OBJ), 'th_ti': _u32(h, log + TH_TI), 'th_count': _u32(h, log + TH_COUNT),
        }
        if got['open_name']:
            got['open_text'] = h._str_get(got['open_name'])
        if got['exc_msg']:
            got['exc_text'] = h._str_get(got['exc_msg'])
        return [], got, (interfaces, children)
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _check_common(got, problems):
    if got['open_count'] != 1 or got['open_noload'] != 1:
        problems.append('the reader was not opened once')
    if got['close_count'] != 1 or got['kill_count'] != 1:
        problems.append('the reader was not closed once')
    if got['close_self'] != got['kill_self'] or got['close_self'] != got['open_self']:
        problems.append('the reader was not the same object throughout')


def test_visit_nodes(h):
    diffs, got, fake = _run(h, b'mesh', [(2, 0), (1, 1)], True)
    if diffs:
        return diffs
    interfaces, children = fake
    problems = []
    _check_common(got, problems)
    if got.get('open_text') != b'mesh.gdl':
        problems.append('opened name is %r' % (got.get('open_text'),))
    want = [OPEN_OP, VF_OP, VISIT_OP, VISIT_OP, VF_OP, VISIT_OP, CLOSE_OP, KILL_OP]
    if got['order'] != want:
        problems.append('call order is %s' % ([hex(x) for x in got['order']],))
    if got['vf1_self'] != interfaces[0] or got['vf1_count'] != 1:
        problems.append('first node interface is %#x' % got['vf1_self'])
    if got['vf2_self'] != interfaces[1] or got['vf2_count'] != 1:
        problems.append('second node interface is %#x' % got['vf2_self'])
    if got['vf1_value'] != VALUE or got['vf2_value'] != VALUE:
        problems.append('interface value is %#x/%#x' % (got['vf1_value'], got['vf2_value']))
    if not got['vf1_scratch'] or got['vf1_scratch'] != got['vf2_scratch']:
        problems.append('interfaces got different scratch records')
    if got['visit_count'] != 3:
        problems.append('visited %d children' % got['visit_count'])
    if got['visit_selfs'] != [children[0], children[0] + 0x44, children[1]]:
        problems.append('visited children at %s' % ([hex(x) for x in got['visit_selfs']],))
    if got['visit_values'] != [VALUE] * 3:
        problems.append('child values are %s' % ([hex(x) for x in got['visit_values']],))
    if got['visit_scratch_args'] != [got['vf1_scratch']] * 3:
        problems.append('the children were not given the interface scratch record')
    if got['exc_count'] or got['th_count']:
        problems.append('unexpected exception path')
    return problems or None


def test_open_failure(h):
    diffs, got, fake = _run(h, b'mesh', [(1, 0)], False)
    if diffs:
        return diffs
    interfaces, children = fake
    problems = []
    if got['order'] != [OPEN_OP, EXC2_OP, THROW_OP, VF_OP, VISIT_OP, CLOSE_OP, KILL_OP]:
        problems.append('call order is %s' % ([hex(x) for x in got['order']],))
    if got['exc_file'] != FILE_LIT or got['exc_line'] != LINE or got['exc_count'] != 1:
        problems.append('exception is (%#x, %#x)' % (got['exc_file'], got['exc_line']))
    if got['th_obj'] != got['exc_self'] or got['th_ti'] != THROW_INFO or got['th_count'] != 1:
        problems.append('thrown object is %#x/%#x' % (got['th_obj'], got['th_ti']))
    prefix = bytes(h.uc.mem_read(PREFIX_LIT, 0x40)).split(b'\0')[0]
    if got.get('exc_text') != prefix + b'mesh':
        problems.append('exception message is %r' % (got.get('exc_text'),))
    if got['vf1_self'] != interfaces[0] or got['visit_count'] != 1:
        problems.append('the nodes were not visited after the failure')
    return problems or None


def test_empty_mesh(h):
    diffs, got, fake = _run(h, b'empty', [], True)
    if diffs:
        return diffs
    problems = []
    _check_common(got, problems)
    if got.get('open_text') != b'empty.gdl':
        problems.append('opened name is %r' % (got.get('open_text'),))
    if got['order'] != [OPEN_OP, CLOSE_OP, KILL_OP]:
        problems.append('call order is %s' % ([hex(x) for x in got['order']],))
    if got['vf1_count'] or got['vf2_count'] or got['visit_count']:
        problems.append('an empty mesh was visited')
    return problems or None
