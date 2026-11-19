"""0x0045E4D0 (thiscall + ECX, one script-table pointer at +4): builds the 0x374-byte CNpc (0x00533E30) from the
table, the registry [0x006C8E40] and this object.  With the world screen up ([world of 0x006C88D8 +0x40] not
zero) the npc goes through 0x0045E230 (this +0x1B4 list) and 0x005AD210 on the world; otherwise 0x004ACE70
supplies the pose floats (+0x30/+0x34/+0x38), which replace the npc's +0x64/+0x68/+0x6C (the old values move to
+0x58/+0x5C/+0x60), +0x70/+0x80 are set, +0x1BC is cleared, the parent point and this object's +0x78 join the
npc's +0x78, a {list, first, npc} node (0x005AD6C0) is prepended to [this +0x204] (0x004E0EF0 grows it) and the
npc's +0x1FC is registered through 0x00425390.  Every callee is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x0045E4D0
WORLD_GLOBAL = 0x006C88D8
REG_GLOBAL = 0x006C8E40
NEW = 0x005E3EAE
CTOR = 0x00533E30
ATTACH = 0x0045E230
WORLD_ADD = 0x005AD210
POSE = 0x004ACE70
NODE = 0x005AD6C0
GROW = 0x004E0EF0
REGISTER = 0x00425390

NPC_SIZE = 0x374
SELF_VEC_Y = 0x42480000             # 50.0f at this +0x78
PARENT_VEC_Y = 0x41C80000           # 25.0f at parent +0x78
NPC_VEC_Y = 0x42C80000              # 100.0f at npc +0x78
NPC_OLD0, NPC_OLD1, NPC_OLD2 = 0x3F800000, 0x40000000, 0x40400000
POSE0, POSE1, POSE2 = 0x40A00000, 0x40E00000, 0x41100000      # 5.0f, 7.0f, 9.0f
WANT_VEC_Y = 0x432F0000             # 25 + 50 + 100 = 175.0f

ORDER = 0x04
NEW_OP, CTOR_OP, ATT_OP, WADD_OP, POSE_OP, NODE_OP, GROW_OP, REG_OP = range(1, 9)
NEW_SIZE = 0x44
CTOR_N, CTOR_THIS, CTOR_TBL, CTOR_REG, CTOR_SELF = 0x48, 0x4C, 0x50, 0x54, 0x58
ATT_N, ATT_THIS, ATT_NPC = 0x5C, 0x60, 0x64
WADD_N, WADD_THIS, WADD_NPC = 0x68, 0x6C, 0x70
POSE_N, POSE_THIS, POSE_BUF = 0x74, 0x78, 0x7C
NODE_N, NODE_LIST, NODE_FIRST, NODE_OBJ = 0x80, 0x84, 0x88, 0x8C
GROW_N, GROW_THIS, GROW_ARG = 0x90, 0x94, 0x98
REG_N, REG_THIS, REG_OBJ = 0x9C, 0xA0, 0xA4
LOG_SIZE = 0xC0

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
    return stub


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


def _run(h, log, world_up, new_ok):
    heap0 = h.heap_ptr
    try:
        self_ = h.alloc(0x210, bytes(0x210))
        parent = h.alloc(0x80, bytes(0x80))
        list_ = h.alloc(0x10, bytes(0x10))
        first = h.alloc(0x10, bytes(0x10))
        npc = h.alloc(NPC_SIZE, bytes(NPC_SIZE))
        world = h.alloc(0x48, bytes(0x48))
        node = h.alloc(0x10, bytes(0x10))
        tbl = h.alloc(0x0C, bytes(0x0C))
        registry = h.alloc(4, bytes(4))
        newret = h.alloc(4, _dword(npc))
        nodep = h.alloc(4, _dword(node))

        _hook(h, NEW, _tag(log, NEW_OP) + _arg(4, log + NEW_SIZE) + b'\x8B\x05' + _dword(newret) + b'\xC3')
        _hook(h, CTOR, _tag(log, CTOR_OP) + _inc(log + CTOR_N) + _ecx_store(log + CTOR_THIS) +
              _arg(4, log + CTOR_TBL) + _arg(8, log + CTOR_REG) + _arg(0xC, log + CTOR_SELF) +
              b'\x8B\xC1' + b'\xC2\x0C\x00')
        _hook(h, ATTACH, _tag(log, ATT_OP) + _inc(log + ATT_N) + _ecx_store(log + ATT_THIS) +
              _arg(4, log + ATT_NPC) + b'\xC2\x04\x00')
        _hook(h, WORLD_ADD, _tag(log, WADD_OP) + _inc(log + WADD_N) + _ecx_store(log + WADD_THIS) +
              _arg(4, log + WADD_NPC) + b'\xC2\x04\x00')
        _hook(h, POSE, _tag(log, POSE_OP) + _inc(log + POSE_N) + _ecx_store(log + POSE_THIS) +
              _arg(4, log + POSE_BUF) + b'\x8B\x54\x24\x04' +
              b'\xC7\x42\x30' + _dword(POSE0) + b'\xC7\x42\x34' + _dword(POSE1) +
              b'\xC7\x42\x38' + _dword(POSE2) + b'\xC2\x04\x00')
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
            h.uc.mem_write(newret, _dword(npc if new_ok else 0))
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(self_, bytes(0x210))
            h.uc.mem_write(parent, bytes(0x80))
            h.uc.mem_write(list_, bytes(0x10))
            h.uc.mem_write(list_ + 4, _dword(first))
            h.uc.mem_write(first, bytes(0x10))
            h.uc.mem_write(npc, bytes(NPC_SIZE))
            h.uc.mem_write(world, bytes(0x48))
            h.uc.mem_write(node, bytes(0x10))
            h.uc.mem_write(self_ + 0x78, _dword(SELF_VEC_Y))
            h.uc.mem_write(self_ + 0x1bc, _dword(parent))
            h.uc.mem_write(self_ + 0x204, _dword(list_))
            h.uc.mem_write(parent + 0x78, _dword(PARENT_VEC_Y))
            h.uc.mem_write(npc + 0x64, _dword(NPC_OLD0))
            h.uc.mem_write(npc + 0x68, _dword(NPC_OLD1))
            h.uc.mem_write(npc + 0x6c, _dword(NPC_OLD2))
            h.uc.mem_write(npc + 0x78, _dword(NPC_VEC_Y))
            h.uc.mem_write(world + 0x40, bytes([1 if world_up else 0]))

        setup()
        diffs = h.compare(FN, args=[tbl], regs={UC_X86_REG_ECX: self_}, ret=None, mem=True)
        if diffs:
            return diffs, None
        setup()
        result = h.call(FN, args=[tbl], regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']], None
        got = {
            'esp': result['esp'],
            'self': self_, 'tbl': tbl, 'world': world, 'registry': registry,
            'npc_ptr': npc, 'node_addr': node, 'list_ptr': list_, 'first_ptr': first,
            'order': [_u32(h, log + ORDER + 4 * i) for i in range(_u32(h, log))],
            'new_size': _u32(h, log + NEW_SIZE),
            'ctor': (_u32(h, log + CTOR_N), _u32(h, log + CTOR_THIS), _u32(h, log + CTOR_TBL),
                     _u32(h, log + CTOR_REG), _u32(h, log + CTOR_SELF)),
            'att': (_u32(h, log + ATT_N), _u32(h, log + ATT_THIS), _u32(h, log + ATT_NPC)),
            'wadd': (_u32(h, log + WADD_N), _u32(h, log + WADD_THIS), _u32(h, log + WADD_NPC)),
            'pose': (_u32(h, log + POSE_N), _u32(h, log + POSE_THIS)),
            'node_args': (_u32(h, log + NODE_N), _u32(h, log + NODE_LIST), _u32(h, log + NODE_FIRST),
                          _u32(h, log + NODE_OBJ)),
            'grow': (_u32(h, log + GROW_N), _u32(h, log + GROW_THIS), _u32(h, log + GROW_ARG)),
            'reg': (_u32(h, log + REG_N), _u32(h, log + REG_THIS), _u32(h, log + REG_OBJ)),
            'fields': {off: _u32(h, npc + off) for off in (0x58, 0x5c, 0x60, 0x64, 0x68, 0x6c, 0x78, 0x1bc)},
            'npc70': bytes(h.uc.mem_read(npc + 0x70, 1)),
            'npc80': bytes(h.uc.mem_read(npc + 0x80, 1)),
            'node': (_u32(h, node), _u32(h, node + 4), _u32(h, node + 8)),
            'list_head': _u32(h, list_ + 4),
            'first': _u32(h, first),
        }
        return [], got
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _check_common(got, tag, problems):
    if got['esp'] != 0x8:
        problems.append('%s: stack delta is %#x' % (tag, got['esp']))
    if got['new_size'] != NPC_SIZE:
        problems.append('%s: npc allocated with %#x bytes' % (tag, got['new_size']))
    if got['ctor'][0] not in (0, 1):
        problems.append('%s: constructor called %d times' % (tag, got['ctor'][0]))


def test_npc_spawn(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    problems = []

    diffs, got = _run(h, log, True, True)
    if diffs:
        return ['world up: %s' % d for d in diffs]
    tag = 'world up'
    _check_common(got, tag, problems)
    if got['order'] != [NEW_OP, CTOR_OP, ATT_OP, WADD_OP]:
        problems.append('%s: call order %s' % (tag, got['order']))
    npc = got['npc_ptr']
    if got['ctor'] != (1, npc, got['tbl'], got['registry'], got['self']):
        problems.append('%s: constructor %s' % (tag, tuple(hex(x) for x in got['ctor'])))
    if got['att'] != (1, got['self'], npc):
        problems.append('%s: attach %s' % (tag, tuple(hex(x) for x in got['att'])))
    if got['wadd'] != (1, got['world'], npc):
        problems.append('%s: world add %s' % (tag, tuple(hex(x) for x in got['wadd'])))
    if got['pose'][0] or got['node_args'][0] or got['grow'][0] or got['reg'][0]:
        problems.append('%s: long-path work ran on the short path' % tag)
    if dict(got['fields']) != {0x58: 0, 0x5c: 0, 0x60: 0, 0x64: NPC_OLD0, 0x68: NPC_OLD1,
                               0x6c: NPC_OLD2, 0x78: NPC_VEC_Y, 0x1bc: 0}:
        problems.append('%s: npc touched %s' % (tag, {hex(k): hex(v) for k, v in got['fields'].items()}))

    diffs, got = _run(h, log, False, True)
    if diffs:
        return problems + ['world down: %s' % d for d in diffs]
    tag = 'world down'
    _check_common(got, tag, problems)
    npc = got['npc_ptr']
    if got['order'] != [NEW_OP, CTOR_OP, POSE_OP, NODE_OP, GROW_OP, REG_OP]:
        problems.append('%s: call order %s' % (tag, got['order']))
    if got['pose'] != (1, npc):
        problems.append('%s: pose %s' % (tag, tuple(hex(x) for x in got['pose'])))
    f = got['fields']
    if (f[0x58], f[0x5c], f[0x60]) != (NPC_OLD0, NPC_OLD1, NPC_OLD2):
        problems.append('%s: old npc values %s' % (tag, [hex(f[o]) for o in (0x58, 0x5c, 0x60)]))
    if (f[0x64], f[0x68], f[0x6c]) != (POSE0, POSE1, POSE2):
        problems.append('%s: pose values %s' % (tag, [hex(f[o]) for o in (0x64, 0x68, 0x6c)]))
    if f[0x78] != WANT_VEC_Y:
        problems.append('%s: npc +0x78 is %#x' % (tag, f[0x78]))
    if f[0x1bc] != 0 or got['npc70'] != b'\x01' or got['npc80'] != b'\x01':
        problems.append('%s: flags %#x/%r/%r' % (tag, f[0x1bc], got['npc70'], got['npc80']))
    if got['att'][0] or got['wadd'][0]:
        problems.append('%s: short-path calls ran' % tag)
    n = got['node_args']
    if n[0] != 1 or n[1] != got['list_ptr'] or n[2] != got['first_ptr'] or n[3] != npc:
        problems.append('%s: node args %s' % (tag, [hex(x) for x in n]))
    if got['node'] != (got['list_ptr'], got['first_ptr'], npc):
        problems.append('%s: node holds %s' % (tag, [hex(x) for x in got['node']]))
    if got['list_head'] != got['node_addr'] or got['first'] != got['node_addr']:
        problems.append('%s: list head %#x, first %#x, node %#x'
                        % (tag, got['list_head'], got['first'], got['node_addr']))
    if got['grow'] != (1, got['self'] + 0x200, 1):
        problems.append('%s: grow %s' % (tag, [hex(x) for x in got['grow']]))
    if got['reg'] != (1, got['registry'], npc + 0x1fc):
        problems.append('%s: registry %s' % (tag, [hex(x) for x in got['reg']]))

    diffs, got = _run(h, log, True, False)
    if diffs:
        return problems + ['no memory: %s' % d for d in diffs]
    tag = 'no memory'
    _check_common(got, tag, problems)
    if got['order'] != [NEW_OP, ATT_OP, WADD_OP]:
        problems.append('%s: call order %s' % (tag, got['order']))
    if got['att'] != (1, got['self'], 0) or got['wadd'] != (1, got['world'], 0):
        problems.append('%s: attach/world add %s/%s' % (tag, got['att'], got['wadd']))
    return problems or None
