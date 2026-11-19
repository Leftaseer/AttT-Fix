"""0x0045E630 (thiscall + ECX, one script-table pointer): builds the 0x380-byte object through operator new
(0x005E3EAE) and 0x004B0E80 with the table, [0x006C8E40], [0x006C8E4C] and this object.  With the world screen up
([world of 0x006C88D8 +0x40] not zero) the object goes through 0x0045E230 and 0x005AD210 on the world; otherwise
0x004ACE70 supplies the pose floats (+0x30/+0x34/+0x38) which replace the object's +0x64/+0x68/+0x6C (old values
move to +0x58/+0x5C/+0x60), +0x70/+0x80 are set, +0x1BC is cleared, the parent point and this object's +0x78 join
the object's +0x78, and the name built by 0x0045BB70 from field 1 of the table is compared with "saoMagicBarrier":
a match prepends a 0x005AD6C0 node to [this +0x240] (grown on this +0x23C), otherwise to [this +0x210] (this
+0x20C), and the object's +0x1FC is registered through 0x00425390.  All callees are recording stubs; the name
stub builds a real std::string through the emulated MSVCP80 constructor at game slot 0x00607324, so the emulated
operator==(const string&, const char*) at 0x006071E4 picks the branch."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x0045E630
WORLD_GLOBAL = 0x006C88D8
REG_GLOBAL = 0x006C8E40
OTHER_GLOBAL = 0x006C8E4C
NEW = 0x005E3EAE
CTOR = 0x004B0E80
ATTACH = 0x0045E230
WORLD_ADD = 0x005AD210
POSE = 0x004ACE70
NAME = 0x0045BB70
NODE = 0x005AD6C0
GROW = 0x004E0EF0
REGISTER = 0x00425390
STR_CTOR_SLOT = 0x00607324

OBJ_SIZE = 0x380
SELF_VEC_Y = 0x42480000             # 50.0f at this +0x78
PARENT_VEC_Y = 0x41C80000           # 25.0f at parent +0x78
OBJ_VEC_Y = 0x42C80000              # 100.0f at object +0x78
OBJ_OLD0, OBJ_OLD1, OBJ_OLD2 = 0x3F800000, 0x40000000, 0x40400000
POSE0, POSE1, POSE2 = 0x40A00000, 0x40E00000, 0x41100000      # 5.0f, 7.0f, 9.0f
WANT_VEC_Y = 0x432F0000             # 25 + 50 + 100 = 175.0f

ORDER = 0x04
NEW_OP, CTOR_OP, ATT_OP, WADD_OP, POSE_OP, NAME_OP, NODE_OP, GROW_OP, REG_OP = range(1, 10)
NEW_N, NEW_SIZE = 0x64, 0x68
CTOR_N, CTOR_THIS, CTOR_A1, CTOR_A2, CTOR_A3, CTOR_A4 = 0x6C, 0x70, 0x74, 0x78, 0x7C, 0x80
ATT_N, ATT_THIS, ATT_OBJ = 0x84, 0x88, 0x8C
WADD_N, WADD_THIS, WADD_OBJ = 0x90, 0x94, 0x98
POSE_N, POSE_THIS, POSE_BUF = 0x9C, 0xA0, 0xA4
NAME_N, NAME_OUT, NAME_LIT = 0xA8, 0xAC, 0xB0
NODE_N, NODE_LIST, NODE_FIRST, NODE_OBJ = 0xB4, 0xB8, 0xBC, 0xC0
GROW_N, GROW_THIS, GROW_ARG = 0xC4, 0xC8, 0xCC
REG_N, REG_THIS, REG_OBJ = 0xD0, 0xD4, 0xD8
LOG_SIZE = 0xF0

MATCH_NAME = b'saoMagicBarrier\0'
OTHER_NAME = b'anotherObject\0'

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


def _arr(offset, counter, address):
    return _mov_eax(offset) + b'\x8B\x15' + _dword(counter) + b'\x89\x04\x95' + _dword(address)


def _run(h, log, world_up, new_ok, match):
    heap0 = h.heap_ptr
    try:
        self_ = h.alloc(0x250, bytes(0x250))
        parent = h.alloc(0x80, bytes(0x80))
        list_a = h.alloc(0x10, bytes(0x10))
        list_b = h.alloc(0x10, bytes(0x10))
        first_a = h.alloc(0x10, bytes(0x10))
        first_b = h.alloc(0x10, bytes(0x10))
        obj = h.alloc(OBJ_SIZE, bytes(OBJ_SIZE))
        world = h.alloc(0x48, bytes(0x48))
        node = h.alloc(0x10, bytes(0x10))
        tbl = h.alloc(0x0C, bytes(0x0C))
        registry = h.alloc(4, bytes(4))
        other = h.alloc(4, bytes(4))
        newret = h.alloc(4, bytes(4))
        bblit = h.alloc(4, bytes(4))
        nodep = h.alloc(4, _dword(node))
        lit_match = h.alloc(len(MATCH_NAME), MATCH_NAME)
        lit_other = h.alloc(len(OTHER_NAME), OTHER_NAME)

        _hook(h, NEW, _tag(log, NEW_OP) + _arg(4, log + NEW_SIZE) + _inc(log + NEW_N) +
              b'\x8B\x05' + _dword(newret) + b'\xC3')
        _hook(h, CTOR, _tag(log, CTOR_OP) + _inc(log + CTOR_N) + _ecx_store(log + CTOR_THIS) +
              _arg(4, log + CTOR_A1) + _arg(8, log + CTOR_A2) + _arg(0xC, log + CTOR_A3) +
              _arg(0x10, log + CTOR_A4) + b'\x8B\xC1' + b'\xC2\x10\x00')
        _hook(h, ATTACH, _tag(log, ATT_OP) + _inc(log + ATT_N) + _ecx_store(log + ATT_THIS) +
              _arg(4, log + ATT_OBJ) + b'\xC2\x04\x00')
        _hook(h, WORLD_ADD, _tag(log, WADD_OP) + _inc(log + WADD_N) + _ecx_store(log + WADD_THIS) +
              _arg(4, log + WADD_OBJ) + b'\xC2\x04\x00')
        _hook(h, POSE, _tag(log, POSE_OP) + _inc(log + POSE_N) + _ecx_store(log + POSE_THIS) +
              _arg(4, log + POSE_BUF) + b'\x8B\x54\x24\x04' +
              b'\xC7\x42\x30' + _dword(POSE0) + b'\xC7\x42\x34' + _dword(POSE1) +
              b'\xC7\x42\x38' + _dword(POSE2) + b'\xC2\x04\x00')
        _hook(h, NAME, _tag(log, NAME_OP) + _inc(log + NAME_N) + _arg(4, log + NAME_OUT) +
              b'\x8B\x05' + _dword(bblit) + b'\xA3' + _dword(log + NAME_LIT) +
              b'\xFF\x35' + _dword(bblit) + b'\x8B\x0D' + _dword(log + NAME_OUT) +
              b'\xFF\x15' + _dword(STR_CTOR_SLOT) + b'\x8B\x05' + _dword(log + NAME_OUT) +
              b'\xC2\x04\x00')
        _hook(h, NODE, _tag(log, NODE_OP) + _arr(4, log + NODE_N, log + NODE_LIST) +
              _arr(8, log + NODE_N, log + NODE_FIRST) + b'\x8B\x54\x24\x0C' + b'\x8B\x12' +
              b'\x89\x15' + _dword(log + NODE_OBJ) + b'\x8B\x05' + _dword(nodep) +
              b'\x8B\x4C\x24\x04' + b'\x89\x08' + b'\x8B\x4C\x24\x08' + b'\x89\x48\x04' +
              b'\x8B\x4C\x24\x0C' + b'\x8B\x09' + b'\x89\x48\x08' + _inc(log + NODE_N) +
              b'\x8B\x05' + _dword(nodep) + b'\xC2\x0C\x00')
        _hook(h, GROW, _tag(log, GROW_OP) + _inc(log + GROW_N) + _ecx_store(log + GROW_THIS) +
              _arg(4, log + GROW_ARG) + b'\xC2\x04\x00')
        _hook(h, REGISTER, _tag(log, REG_OP) + _inc(log + REG_N) + _ecx_store(log + REG_THIS) +
              _arg(4, log + REG_OBJ) + b'\xC2\x04\x00')

        def setup():
            h.uc.mem_write(WORLD_GLOBAL, _dword(world))
            h.uc.mem_write(REG_GLOBAL, _dword(registry))
            h.uc.mem_write(OTHER_GLOBAL, _dword(other))
            h.uc.mem_write(newret, _dword(obj if new_ok else 0))
            h.uc.mem_write(bblit, _dword(lit_match if match else lit_other))
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(self_, bytes(0x250))
            h.uc.mem_write(parent, bytes(0x80))
            h.uc.mem_write(list_a, bytes(0x10))
            h.uc.mem_write(list_b, bytes(0x10))
            h.uc.mem_write(first_a, bytes(0x10))
            h.uc.mem_write(first_b, bytes(0x10))
            h.uc.mem_write(obj, bytes(OBJ_SIZE))
            h.uc.mem_write(world, bytes(0x48))
            h.uc.mem_write(node, bytes(0x10))
            h.uc.mem_write(self_ + 0x78, _dword(SELF_VEC_Y))
            h.uc.mem_write(self_ + 0x1bc, _dword(parent))
            h.uc.mem_write(self_ + 0x210, _dword(list_b))
            h.uc.mem_write(self_ + 0x240, _dword(list_a))
            h.uc.mem_write(list_a + 4, _dword(first_a))
            h.uc.mem_write(list_b + 4, _dword(first_b))
            h.uc.mem_write(parent + 0x78, _dword(PARENT_VEC_Y))
            h.uc.mem_write(obj + 0x64, _dword(OBJ_OLD0))
            h.uc.mem_write(obj + 0x68, _dword(OBJ_OLD1))
            h.uc.mem_write(obj + 0x6c, _dword(OBJ_OLD2))
            h.uc.mem_write(obj + 0x78, _dword(OBJ_VEC_Y))
            h.uc.mem_write(world + 0x40, bytes([1 if world_up else 0]))

        setup()
        diffs = h.compare(FN, args=[tbl], regs={UC_X86_REG_ECX: self_}, ret=None, mem=False)
        if diffs:
            return diffs, None
        setup()
        result = h.call(FN, args=[tbl], regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']], None
        got = {
            'esp': result['esp'],
            'self': self_, 'tbl': tbl, 'world': world, 'registry': registry, 'other': other,
            'obj_ptr': obj, 'node_addr': node, 'list_a': list_a, 'list_b': list_b,
            'first_a': first_a, 'first_b': first_b, 'lit': lit_match if match else lit_other,
            'order': [_u32(h, log + ORDER + 4 * i) for i in range(_u32(h, log))],
            'new_size': _u32(h, log + NEW_SIZE),
            'ctor': (_u32(h, log + CTOR_N), _u32(h, log + CTOR_THIS), _u32(h, log + CTOR_A1),
                     _u32(h, log + CTOR_A2), _u32(h, log + CTOR_A3), _u32(h, log + CTOR_A4)),
            'att': (_u32(h, log + ATT_N), _u32(h, log + ATT_THIS), _u32(h, log + ATT_OBJ)),
            'wadd': (_u32(h, log + WADD_N), _u32(h, log + WADD_THIS), _u32(h, log + WADD_OBJ)),
            'pose': (_u32(h, log + POSE_N), _u32(h, log + POSE_THIS)),
            'name': (_u32(h, log + NAME_N), _u32(h, log + NAME_OUT), _u32(h, log + NAME_LIT)),
            'node_args': (_u32(h, log + NODE_N), _u32(h, log + NODE_LIST), _u32(h, log + NODE_FIRST),
                          _u32(h, log + NODE_OBJ)),
            'grow': (_u32(h, log + GROW_N), _u32(h, log + GROW_THIS), _u32(h, log + GROW_ARG)),
            'reg': (_u32(h, log + REG_N), _u32(h, log + REG_THIS), _u32(h, log + REG_OBJ)),
            'fields': {off: _u32(h, obj + off) for off in (0x58, 0x5c, 0x60, 0x64, 0x68, 0x6c, 0x78, 0x1bc)},
            'obj70': bytes(h.uc.mem_read(obj + 0x70, 1)),
            'obj80': bytes(h.uc.mem_read(obj + 0x80, 1)),
            'node': (_u32(h, node), _u32(h, node + 4), _u32(h, node + 8)),
            'list_head': (_u32(h, list_a + 4), _u32(h, list_b + 4)),
            'first': (_u32(h, first_a), _u32(h, first_b)),
        }
        return [], got
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _check_alloc(got, tag, problems, expect_ctor):
    if got['esp'] != 0x8:
        problems.append('%s: stack delta is %#x' % (tag, got['esp']))
    if got['new_size'] != OBJ_SIZE:
        problems.append('%s: object allocated with %#x bytes' % (tag, got['new_size']))
    if got['ctor'][0] != expect_ctor:
        problems.append('%s: constructor called %d times' % (tag, got['ctor'][0]))


def test_world_up(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    problems = []

    diffs, got = _run(h, log, True, True, False)
    if diffs:
        return ['allocated: %s' % d for d in diffs]
    _check_alloc(got, 'allocated', problems, 1)
    if got['order'] != [NEW_OP, CTOR_OP, ATT_OP, WADD_OP]:
        problems.append('allocated: call order %s' % (got['order'],))
    obj = got['obj_ptr']
    if got['ctor'] != (1, obj, got['tbl'], got['registry'], got['other'], got['self']):
        problems.append('allocated: constructor %s' % (tuple(hex(x) for x in got['ctor']),))
    if got['att'] != (1, got['self'], obj) or got['wadd'] != (1, got['world'], obj):
        problems.append('allocated: attach/world add %s/%s' % (got['att'], got['wadd']))
    if got['pose'][0] or got['name'][0] or got['node_args'][0] or got['grow'][0] or got['reg'][0]:
        problems.append('allocated: long-path work ran on the short path')
    if got['fields'] != {0x58: 0, 0x5c: 0, 0x60: 0, 0x64: OBJ_OLD0, 0x68: OBJ_OLD1,
                         0x6c: OBJ_OLD2, 0x78: OBJ_VEC_Y, 0x1bc: 0}:
        problems.append('allocated: object touched %s' % ({hex(k): hex(v) for k, v in got['fields'].items()},))

    diffs, got = _run(h, log, True, False, False)
    if diffs:
        return problems + ['no memory: %s' % d for d in diffs]
    _check_alloc(got, 'no memory', problems, 0)
    if got['order'] != [NEW_OP, ATT_OP, WADD_OP]:
        problems.append('no memory: call order %s' % (got['order'],))
    if got['att'] != (1, got['self'], 0) or got['wadd'] != (1, got['world'], 0):
        problems.append('no memory: attach/world add %s/%s' % (got['att'], got['wadd']))
    return problems or None


def _check_long(got, tag, problems, list_, first, base):
    obj = got['obj_ptr']
    if got['order'] != [NEW_OP, CTOR_OP, POSE_OP, NAME_OP, NODE_OP, GROW_OP, REG_OP]:
        problems.append('%s: call order %s' % (tag, got['order']))
    if got['pose'] != (1, obj):
        problems.append('%s: pose %s' % (tag, tuple(hex(x) for x in got['pose'])))
    if got['name'][0] != 1 or got['name'][1] == 0 or got['name'][2] != got['lit']:
        problems.append('%s: name %s' % (tag, tuple(hex(x) for x in got['name'])))
    f = got['fields']
    if (f[0x58], f[0x5c], f[0x60]) != (OBJ_OLD0, OBJ_OLD1, OBJ_OLD2):
        problems.append('%s: old values %s' % (tag, [hex(f[o]) for o in (0x58, 0x5c, 0x60)]))
    if (f[0x64], f[0x68], f[0x6c]) != (POSE0, POSE1, POSE2):
        problems.append('%s: pose values %s' % (tag, [hex(f[o]) for o in (0x64, 0x68, 0x6c)]))
    if f[0x78] != WANT_VEC_Y:
        problems.append('%s: object +0x78 is %#x' % (tag, f[0x78]))
    if f[0x1bc] != 0 or got['obj70'] != b'\x01' or got['obj80'] != b'\x01':
        problems.append('%s: flags %#x/%r/%r' % (tag, f[0x1bc], got['obj70'], got['obj80']))
    if got['att'][0] or got['wadd'][0]:
        problems.append('%s: short-path calls ran' % tag)
    n = got['node_args']
    if n != (1, list_, first, obj):
        problems.append('%s: node args %s' % (tag, [hex(x) for x in n]))
    if got['node'] != (list_, first, obj):
        problems.append('%s: node holds %s' % (tag, [hex(x) for x in got['node']]))
    idx = 0 if list_ == got['list_a'] else 1
    if got['list_head'][idx] != got['node_addr'] or got['first'][idx] != got['node_addr']:
        problems.append('%s: list head %#x, first %#x, node %#x'
                        % (tag, got['list_head'][idx], got['first'][idx], got['node_addr']))
    if got['grow'] != (1, base, 1):
        problems.append('%s: grow %s' % (tag, [hex(x) for x in got['grow']]))
    if got['reg'] != (1, got['registry'], obj + 0x1fc):
        problems.append('%s: registry %s' % (tag, [hex(x) for x in got['reg']]))


def test_magic_barrier_name(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    problems = []
    diffs, got = _run(h, log, False, True, True)
    if diffs:
        return ['matching name: %s' % d for d in diffs]
    _check_alloc(got, 'matching name', problems, 1)
    _check_long(got, 'matching name', problems, got['list_a'], got['first_a'], got['self'] + 0x23c)
    return problems or None


def test_other_name(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    problems = []
    diffs, got = _run(h, log, False, True, False)
    if diffs:
        return ['other name: %s' % d for d in diffs]
    _check_alloc(got, 'other name', problems, 1)
    _check_long(got, 'other name', problems, got['list_b'], got['first_b'], got['self'] + 0x20c)
    return problems or None
