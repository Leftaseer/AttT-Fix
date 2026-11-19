"""0x5A2410 (thiscall, ECX and two 4-byte arguments, 8 bytes popped): sets the visibility of a dialog element group.
The dialog's 13 group records (12 bytes, list head at +4) hold circular {next, prev, element} nodes; the list of
record 12 is walked first with 0 (with 1 and a 12-group limit when hiding group 1), then the group's own list gets
the virtual +0x40 with the value while the index walks down (non-zero value) or up (zero) inside the table; an index
at or past the count throws the std::string of 0x62058C through 0x5E3EC0.  The visitor and the throw are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x005A2410
THROW = 0x005E3EC0
THROW_INFO = 0x0069916C
MSG_LIT = 0x0062058C

ORDER = 0x04                         # log+0 is _tag's call counter
VIS_N = 0x44
VIS_THIS = 0x48                      # 16 entries
VIS_ARG = 0x88                       # 16 entries
TH_N = 0xC8
TH_OBJ = 0xCC
TH_TI = 0xD0
LOG_SIZE = 0xE0
VIS_MAX = 16

RECORDS = 13
ALL_LIST = 12
LAYOUT = (('A1', 12), ('A2', 12), ('D', 0), ('F', 1), ('B1', 2), ('B2', 2), ('B3', 2),
          ('C', 3), ('E1', 4), ('E2', 4), ('K', 11))

VIS_OP, TH_OP = 1, 2
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


def _mov_eax(offset):
    return b'\x8B\x44\x24' + bytes([offset])


def _arg(offset, address):
    return _mov_eax(offset) + b'\xA3' + _dword(address)


def _ecx_store(address):
    return b'\x89\x0D' + _dword(address)


def _inc(address):
    return b'\xFF\x05' + _dword(address)


def _arr_ecx(counter, address):
    return b'\x8B\x15' + _dword(counter) + b'\x89\x0C\x95' + _dword(address)


def _arr(offset, counter, address):
    return _mov_eax(offset) + b'\x8B\x15' + _dword(counter) + b'\x89\x04\x95' + _dword(address)


def _fixture(h, log, visit):
    vtable = h.alloc(0x48, bytes(0x48))
    h.uc.mem_write(vtable + 0x40, _dword(visit))
    self_ = h.alloc(0x2A0, bytes(0x2A0))
    table = h.alloc(RECORDS * 12, bytes(RECORDS * 12))
    h.uc.mem_write(self_ + 0x294, _dword(table))
    h.uc.mem_write(self_ + 0x298, _dword(table + RECORDS * 12))
    elems = {}
    for name, _ in LAYOUT:
        p = h.alloc(8, bytes(8))
        h.uc.mem_write(p, _dword(vtable))
        elems[name] = p
    for rec in range(RECORDS):
        names = [name for name, r in LAYOUT if r == rec]
        head = h.alloc(12, bytes(12))
        nodes = []
        for name in names:
            node = h.alloc(12, bytes(12))
            h.uc.mem_write(node + 8, _dword(elems[name]))
            nodes.append(node)
        for i, node in enumerate(nodes):
            h.uc.mem_write(node, _dword(nodes[i + 1] if i + 1 < len(nodes) else head))
        h.uc.mem_write(head, _dword(nodes[0] if nodes else head))
        h.uc.mem_write(head + 4, _dword(nodes[-1] if nodes else head))
        h.uc.mem_write(table + rec * 12 + 4, _dword(head))
    return self_, elems


def _run(h, group, visible):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        visit = _stub(h, _tag(log, VIS_OP) + _arr_ecx(log + VIS_N, log + VIS_THIS) +
                      _arr(4, log + VIS_N, log + VIS_ARG) + _inc(log + VIS_N) + b'\xC2\x04\x00')
        _hook(h, THROW, _tag(log, TH_OP) + _arg(4, log + TH_OBJ) + _arg(8, log + TH_TI) +
              _inc(log + TH_N) + b'\xC2\x08\x00')
        self_, elems = _fixture(h, log, visit)

        # the thrown string lives in the caller frame; its address is logged, so compare memory only off that path
        mem = group < RECORDS
        diffs = h.compare(FN, args=[group, visible], regs={UC_X86_REG_ECX: self_}, ret=None, mem=mem)
        if diffs:
            return diffs, None
        h.uc.mem_write(log, bytes(LOG_SIZE))
        result = h.call(FN, args=[group, visible], regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']], None
        count = _u32(h, log + VIS_N)
        if count > VIS_MAX:
            return ['%d visitor calls' % count], None
        got = {
            'esp': result['esp'],
            'count': count,
            'vis': [(_u32(h, log + VIS_THIS + 4 * i), _u32(h, log + VIS_ARG + 4 * i))
                    for i in range(count)],
            'th_n': _u32(h, log + TH_N), 'th_obj': _u32(h, log + TH_OBJ),
            'th_ti': _u32(h, log + TH_TI),
            'elems': elems,
            'msg': bytes(h.uc.mem_read(MSG_LIT, 0x80)).split(b'\0')[0],
        }
        if got['th_n']:
            got['th_str'] = h._str_get(got['th_obj'])
        return [], got
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _check(got, calls, problems, thrown=0, message=None):
    if got['esp'] != 0xC:
        problems.append('stack delta is %#x' % got['esp'])
    want = [(got['elems'][name], value) for name, value in calls]
    if got['vis'] != want:
        problems.append('visitor calls are %s, want %s'
                        % ([(hex(t), v) for t, v in got['vis']], [(hex(t), v) for t, v in want]))
    if got['th_n'] != thrown:
        problems.append('throw called %d times, want %d' % (got['th_n'], thrown))
    if thrown:
        if got['th_ti'] != THROW_INFO:
            problems.append('throw info is %#x' % got['th_ti'])
        if got['th_str'] != message:
            problems.append('thrown string is %r, want %r' % (got['th_str'], message))


def test_group_visibility(h):
    problems = []
    cases = (
        (2, 1, [('A1', 0), ('A2', 0), ('B1', 1), ('B2', 1), ('B3', 1), ('F', 1), ('D', 1)], 0),
        (4, 0, [('A1', 0), ('A2', 0), ('E1', 0), ('E2', 0), ('K', 0), ('A1', 0), ('A2', 0)], 0),
        (1, 0, [('A1', 1), ('A2', 1), ('F', 0), ('B1', 0), ('B2', 0), ('B3', 0), ('C', 0),
                ('E1', 0), ('E2', 0), ('K', 0)], 0),
        (0, 1, [('A1', 0), ('A2', 0), ('D', 1)], 0),
        (-1, 0, [('A1', 0), ('A2', 0)], 0),
        (13, 0, [('A1', 0), ('A2', 0)], 1),
    )
    for group, visible, calls, thrown in cases:
        diffs, got = _run(h, group, visible)
        if diffs:
            return ['group %d visible %d: %s' % (group, visible, d) for d in diffs]
        before = len(problems)
        _check(got, calls, problems, thrown, got['msg'] if thrown else None)
        if len(problems) != before:
            return ['group %d visible %d: %s' % (group, visible, problems[before])]
    return problems or None
