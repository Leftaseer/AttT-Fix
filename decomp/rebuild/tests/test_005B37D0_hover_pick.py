"""0x005B37D0 (ECX, no arguments): the world map tool's hover highlight.  The cursor position (input object
0x00421680, slot 0x88) is unprojected in place with the camera manager's matrices (0x00424E70: view +0x88,
projection +0xC8, viewport +0x22C; world 0x006C8478) through the D3DX thunk 0x005B80F2 and passed by value to
the object at +0xC0 (0x004258C0).  The last entry of the {distance, object} vector at +0x80 is deactivated
(0x00591B80) and the vector emptied; the circular list at +0x48 is walked and every object whose type (+0x354)
matches the tool's (+0x68 +0x354: type 2 when the tool's is 1, type 1 otherwise) is tested under the screen
cursor (0x00591640, the tool's type in EAX) and appended with distance 0 (0x0043E2D0).  If anything was
appended, the reference points (0x005AD280), each object's distance (0x0058EBE0) and the sort (0x005B2E50)
fill and order the vector, whose nearest entry is activated (0x00591AF0); the tool's own stream (+0x68) is
activated last.  Every callee is replaced by a stub, so the arguments and the call order are checked."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x005B37D0
INPUT_FN = 0x00421680
CAMERA_FN = 0x00424E70
UNPROJECT = 0x005B80F2
EMIT = 0x004258C0
CLEAR = 0x00591B80
PICK = 0x00591640
PUSH = 0x0043E2D0
REFS = 0x005AD280
DIST = 0x0058EBE0
SORT = 0x005B2E50
ACT = 0x00591AF0

TAG_UNPROJECT = 1
TAG_EMIT = 2
TAG_CLEAR = 3
TAG_PICK = 4
TAG_PUSH = 5
TAG_REFS = 6
TAG_DIST = 7
TAG_SORT = 8
TAG_ACT = 9

MX = 123.5
MY = -456.25
UNPROJ = (11.5, -22.25, 33.75)
REF_A = (1.0, 2.0, 3.0)
REF_B = (4.0, 5.0, 6.0)

saved = {}


def _u(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _f(value):
    return struct.pack('<f', value)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _f32(h, address):
    return struct.unpack('<f', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, stub):
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _tag(seq, tag):
    return b'\xA1' + _u(seq) + b'\xFF\x05' + _u(seq) + b'\xC7\x04\x85' + _u(seq + 4) + _u(tag)


def _next(cnt):
    return b'\x8B\x15' + _u(cnt) + b'\xFF\x05' + _u(cnt)


def _base(log, unit):
    """eax = log + edx * unit (the call index in edx)"""
    return b'\x8B\xC2' + b'\x6B\xC0' + bytes([unit]) + b'\x05' + _u(log)


def _store(disp, src):
    """mov [eax+disp], src (src: 0=eax, 1=ecx, 2=edx)"""
    if disp == 0:
        return bytes([0x89, src << 3])
    return bytes([0x89, 0x40 | (src << 3), disp])


def _put(dst_reg, disp, value):
    """mov dword [dst_reg+disp], imm32 (dst_reg: 1=ecx, 2=edx)"""
    if disp:
        return b'\xC7' + bytes([0x40 | dst_reg, disp]) + _u(value)
    return b'\xC7' + bytes([dst_reg]) + _u(value)


class Scene:
    def __init__(self, h):
        self.h = h
        self.seq = h.alloc(4 + 4 * 40, bytes(4 + 4 * 40))
        self.cnt = {name: h.alloc(4, bytes(4)) for name in
                    ('un', 'emit', 'clear', 'pick', 'push', 'sort', 'act', 'dist')}
        self.l_un = h.alloc(40 * 7 * 4, bytes(40 * 7 * 4))
        self.l_emit = h.alloc(40 * 4 * 4, bytes(40 * 4 * 4))
        self.l_clear = h.alloc(40 * 2 * 4, bytes(40 * 2 * 4))
        self.l_pick = h.alloc(40 * 5 * 4, bytes(40 * 5 * 4))
        self.l_push = h.alloc(40 * 3 * 4, bytes(40 * 3 * 4))
        self.l_dist = h.alloc(40 * 3 * 4, bytes(40 * 3 * 4))
        self.l_sort = h.alloc(40 * 3 * 4, bytes(40 * 3 * 4))
        self.l_act = h.alloc(40 * 2 * 4, bytes(40 * 2 * 4))
        self.this = h.alloc(0x100, bytes(0x100))
        self.tool = h.alloc(0x400, bytes(0x400))
        self.camera = h.alloc(0x300, bytes(0x300))
        self.input = h.alloc(0x100, bytes(0x100))
        self.vt_in = h.alloc(0x100, bytes(0x100))
        self.cursor = h.alloc(0x10, bytes(0x10))
        self.objs = [h.alloc(0x400, bytes(0x400)) for _ in range(3)]
        self.old = [h.alloc(0x40, bytes(0x40)) for _ in range(2)]
        self.head = h.alloc(0x10, bytes(0x10))
        self.nodes = [h.alloc(0x10, bytes(0x10)) for _ in range(3)]
        self.elems = h.alloc(0x40, bytes(0x40))
        self.scratch = h.alloc(8, bytes(8))
        self.pick_code = h.alloc(0x100, bytes(0x100))
        self._install()

    def reset(self, mode, types, passing, preload, null_vector=False):
        h = self.h
        # 0x00591640 (ECX = object, EAX = tool type, [esp+4] = point, ret 4): logs the call and lets only
        # `passing` report a hit, so the other objects fail the screen test.
        pick = b'\x89\x0D' + _u(self.scratch) + b'\xA3' + _u(self.scratch + 4)
        pick += _tag(self.seq, TAG_PICK) + _next(self.cnt['pick']) + _base(self.l_pick, 0x14)
        pick += b'\x8B\x0D' + _u(self.scratch + 4) + _store(0, 1)
        pick += b'\x8B\x0D' + _u(self.scratch) + _store(4, 1)
        pick += b'\x8B\x4C\x24\x04' + b'\x8B\x11' + _store(8, 2)
        pick += b'\x8B\x51\x04' + _store(0x0C, 2)
        pick += b'\x8B\x51\x08' + _store(0x10, 2)
        pick += b'\x8B\x0D' + _u(self.scratch) + b'\x81\xF9' + _u(passing) + b'\x0F\x94\xC0\xC2\x04\x00'
        h.uc.mem_write(self.pick_code, pick)
        h.uc.ctl_remove_cache(self.pick_code, self.pick_code + len(pick))
        h.uc.mem_write(self.seq, bytes(4 + 4 * 40))
        for c in self.cnt.values():
            h.uc.mem_write(c, b'\0' * 4)
        for block, size in ((self.this, 0x100), (self.tool, 0x400), (self.camera, 0x300),
                            (self.input, 0x100), (self.vt_in, 0x100), (self.elems, 0x40),
                            (self.head, 0x10)):
            h.uc.mem_write(block, bytes(size))
        for o in self.objs:
            h.uc.mem_write(o, bytes(0x400))
        for o in self.old:
            h.uc.mem_write(o, bytes(0x40))
        for n in self.nodes:
            h.uc.mem_write(n, bytes(0x10))
        h.uc.mem_write(self.cursor, _f(MX) + _f(MY) + b'\0' * 8)
        h.uc.mem_write(self.this + 0x48, _u(self.head))
        h.uc.mem_write(self.this + 0x68, _u(self.tool))
        h.uc.mem_write(self.this + 0xc0, _u(self.input))
        h.uc.mem_write(self.this + 0x80, _u(0))
        if null_vector:
            h.uc.mem_write(self.this + 0x84, _u(0) + _u(0) + _u(0))
        else:
            h.uc.mem_write(self.this + 0x84, _u(self.elems) + _u(self.elems + 8 * preload) + _u(self.elems + 0x40))
        for i in range(preload):
            h.uc.mem_write(self.elems + 8 * i, _f(1.5 + i) + _u(self.old[i]))
        h.uc.mem_write(self.tool + 0x354, _u(mode))
        h.uc.mem_write(self.input, _u(self.vt_in))
        h.uc.mem_write(self.vt_in + 0x88, _u(self.stub_cursor))
        for obj, kind in zip(self.objs, types):
            h.uc.mem_write(obj + 0x354, _u(kind))
        h.uc.mem_write(self.head, _u(self.nodes[0]))
        for i, n in enumerate(self.nodes):
            h.uc.mem_write(n, _u(self.nodes[i + 1] if i < 2 else self.head) + _u(0) + _u(self.objs[i]))

    def _install(self):
        h = self.h
        self.stub_cursor = _stub(h, b'\xB8' + _u(self.cursor) + b'\xC3')
        _hook(h, INPUT_FN, _stub(h, b'\xB8' + _u(self.input) + b'\xC3'))
        _hook(h, CAMERA_FN, _stub(h, b'\xB8' + _u(self.camera) + b'\xC3'))

        code = _tag(self.seq, TAG_UNPROJECT) + _next(self.cnt['un']) + _base(self.l_un, 0x1C)
        for k, off in enumerate((0x0C, 0x10, 0x14, 0x18)):
            code += b'\x8B\x4C\x24' + bytes([off]) + _store(4 * k, 1)
        code += b'\x8B\x54\x24\x08' + b'\x8B\x0A' + _store(0x10, 1)
        code += b'\x8B\x4A\x04' + _store(0x14, 1)
        code += b'\x8B\x4A\x08' + _store(0x18, 1)
        code += b'\x8B\x54\x24\x04'
        code += _put(2, 0, 0x41380000) + _put(2, 4, 0xC1B20000) + _put(2, 8, 0x42070000)
        code += b'\xC2\x18\x00'
        _hook(h, UNPROJECT, _stub(h, code))

        code = b'\x89\x0D' + _u(self.scratch) + _tag(self.seq, TAG_EMIT) + _next(self.cnt['emit'])
        code += _base(self.l_emit, 0x10) + _store(0, 1)
        for k, off in enumerate((0x04, 0x08, 0x0C)):
            code += b'\x8B\x4C\x24' + bytes([off]) + _store(4 * k + 4, 1)
        code += b'\x33\xC0' + b'\xC2\x0C\x00'
        _hook(h, EMIT, _stub(h, code))

        code = _tag(self.seq, TAG_CLEAR) + _next(self.cnt['clear']) + _base(self.l_clear, 0x08)
        code += _store(0, 1) + b'\x8B\x4C\x24\x04' + _store(4, 1) + b'\xC2\x04\x00'
        _hook(h, CLEAR, _stub(h, code))

        # the pick stub itself is rebuilt by reset() with the object that should report a hit
        _hook(h, PICK, self.pick_code)

        code = b'\x8B\x41\x08' + b'\x8B\x54\x24\x04' + b'\x89\x15' + _u(self.scratch)
        code += b'\x8B\x12' + b'\x89\x10'
        code += b'\x8B\x15' + _u(self.scratch) + b'\x8B\x52\x04' + b'\x89\x50\x04'
        code += b'\x8D\x50\x08' + b'\x89\x51\x08'
        code += _tag(self.seq, TAG_PUSH) + _next(self.cnt['push']) + _base(self.l_push, 0x0C)
        code += _store(0, 1) + b'\x8B\x51\x08' + b'\x8B\x52\xF8' + _store(4, 2)
        code += b'\x8B\x51\x08' + b'\x8B\x52\xFC' + _store(8, 2) + b'\xC2\x04\x00'
        _hook(h, PUSH, _stub(h, code))

        code = _tag(self.seq, TAG_REFS) + b'\x8B\x4C\x24\x04'
        for k, v in enumerate(REF_A + REF_B):
            if k == 3:
                code += b'\x8B\x4C\x24\x08'
            code += _put(1, 4 * (k % 3), struct.unpack('<I', _f(v))[0])
        code += b'\xC2\x08\x00'
        _hook(h, REFS, _stub(h, code))

        code = b'\x89\x0D' + _u(self.scratch) + _tag(self.seq, TAG_DIST) + _next(self.cnt['dist'])
        code += _base(self.l_dist, 0x0C) + _store(0, 1)
        code += b'\x8B\x54\x24\x04' + b'\x8B\x0A' + _store(4, 1)
        code += b'\x8B\x54\x24\x08' + b'\x8B\x0A' + _store(8, 1)
        code += b'\x8B\x54\x24\x04' + b'\xD9\x02' + b'\x8B\x4C\x24\x08' + b'\xD8\x01'
        code += b'\xC2\x08\x00'
        _hook(h, DIST, _stub(h, code))

        code = _tag(self.seq, TAG_SORT) + _next(self.cnt['sort']) + _base(self.l_sort, 0x0C)
        for k, off in enumerate((0x04, 0x08, 0x0C)):
            code += b'\x8B\x4C\x24' + bytes([off]) + _store(4 * k, 1)
        code += b'\xC3'
        _hook(h, SORT, _stub(h, code))

        code = _tag(self.seq, TAG_ACT) + _next(self.cnt['act']) + _base(self.l_act, 0x08)
        code += _store(0, 1) + b'\x8B\x4C\x24\x04' + _store(4, 1) + b'\xC2\x04\x00'
        _hook(h, ACT, _stub(h, code))

    def tags(self):
        n = _u32(self.h, self.seq)
        return list(struct.unpack('<%dI' % n, self.h.uc.mem_read(self.seq + 4, 4 * n)))


def _entries(h, log, cnt, width):
    n = _u32(h, cnt)
    data = h.uc.mem_read(log, width * 4 * n)
    return [struct.unpack('<%dI' % width, data[i * width * 4:(i + 1) * width * 4]) for i in range(n)]


def _run(h, scene):
    diffs = h.compare(FN, regs={UC_X86_REG_ECX: scene.this}, ret=None)
    if diffs:
        return diffs
    res = h.call(FN, regs={UC_X86_REG_ECX: scene.this})
    if res['fault']:
        return ['the replacement faulted: %s' % res['fault']]
    return None


def test_005B37D0(h):
    heap0 = h.heap_ptr
    try:
        scene = Scene(h)
        scenarios = [
            (1, (2, 1, 2), 0, 2),
            (2, (1, 2, 1), 2, 2),
            (4, (1, 2, 3), 0, 1),
        ]
        for mode, types, passing, preload in scenarios:
            scene.reset(mode, types, scene.objs[passing], preload)
            diffs = _run(h, scene)
            if diffs:
                return ['mode %d: %s' % (mode, d) for d in diffs]
            tested = [i for i, t in enumerate(types) if (t == 2 if mode == 1 else t == 1)]
            expect = [TAG_UNPROJECT, TAG_EMIT]
            if preload:
                expect.append(TAG_CLEAR)
            for i in tested:
                expect.append(TAG_PICK)
                if i == passing:
                    expect.append(TAG_PUSH)
            expect += [TAG_REFS, TAG_DIST, TAG_SORT, TAG_ACT, TAG_ACT]
            if scene.tags() != expect:
                return ['mode %d: the call order is %s, expected %s' % (mode, scene.tags(), expect)]
            un = _entries(h, scene.l_un, scene.cnt['un'], 7)
            if len(un) != 1:
                return ['mode %d: the unprojection ran %d times' % (mode, len(un))]
            if un[0][0] != scene.camera + 0x22c or un[0][1] != scene.camera + 0xc8 or un[0][2] != scene.camera + 0x88:
                return ['mode %d: the unprojection got %08X/%08X/%08X' % (mode, un[0][0], un[0][1], un[0][2])]
            if un[0][3] == 0:
                return ['mode %d: the world matrix is null' % mode]
            if struct.unpack('<3f', struct.pack('<3I', *un[0][4:7])) != (MX, MY, 0.0):
                return ['mode %d: the unprojection input is %r' % (mode, un[0][4:7])]
            emit = _entries(h, scene.l_emit, scene.cnt['emit'], 4)
            if len(emit) != 1 or emit[0][0] != scene.input:
                return ['mode %d: the object at +0xC0 is %s' % (mode, emit)]
            if struct.unpack('<3f', struct.pack('<3I', *emit[0][1:4])) != UNPROJ:
                return ['mode %d: the unprojected point is %r, expected %r' % (mode, emit[0][1:4], UNPROJ)]
            picks = _entries(h, scene.l_pick, scene.cnt['pick'], 5)
            if [p[1] for p in picks] != [scene.objs[i] for i in tested]:
                return ['mode %d: the tested objects are %s, expected %s'
                        % (mode, [p[1] for p in picks], [scene.objs[i] for i in tested])]
            for p in picks:
                if p[0] != mode:
                    return ['mode %d: the pick got the tool type %d' % (mode, p[0])]
                if struct.unpack('<3f', struct.pack('<3I', *p[2:5])) != (MX, MY, 0.0):
                    return ['mode %d: the pick point is %r' % (mode, p[2:5])]
            if preload:
                clear = _entries(h, scene.l_clear, scene.cnt['clear'], 2)
                if clear != [(scene.old[preload - 1], 0)]:
                    return ['mode %d: the clear calls are %s' % (mode, clear)]
            pushes = _entries(h, scene.l_push, scene.cnt['push'], 3)
            if len(pushes) != 1 or pushes[0][0] != scene.this + 0x80 or pushes[0][1] != 0:
                return ['mode %d: the append calls are %s' % (mode, pushes)]
            if pushes[0][2] != scene.objs[passing]:
                return ['mode %d: the appended object is %08X' % (mode, pushes[0][2])]
            if _u32(h, scene.this + 0x88) != scene.elems + 8 or _u32(h, scene.elems + 4) != scene.objs[passing]:
                return ['mode %d: the vector ends at %08X with %08X'
                        % (mode, _u32(h, scene.this + 0x88), _u32(h, scene.elems + 4))]
            if _f32(h, scene.elems) != REF_A[0] + REF_B[0]:
                return ['mode %d: the distance is %r' % (mode, _f32(h, scene.elems))]
            dist = _entries(h, scene.l_dist, scene.cnt['dist'], 3)
            if len(dist) != 1 or dist[0][0] != scene.objs[passing]:
                return ['mode %d: the distance calls are %s' % (mode, dist)]
            if dist[0][1] != struct.unpack('<I', _f(REF_A[0]))[0] or dist[0][2] != struct.unpack('<I', _f(REF_B[0]))[0]:
                return ['mode %d: the distance points are %r/%r' % (mode, dist[0][1], dist[0][2])]
            sort = _entries(h, scene.l_sort, scene.cnt['sort'], 3)
            if sort != [(scene.elems, scene.elems + 8, 1)]:
                return ['mode %d: the sort got %s' % (mode, sort)]
            act = _entries(h, scene.l_act, scene.cnt['act'], 2)
            if act != [(scene.objs[passing], 0), (scene.tool, 0)]:
                return ['mode %d: the activation calls are %s' % (mode, act)]

        scene.reset(1, (1, 1, 1), 0, 0, null_vector=True)
        diffs = _run(h, scene)
        if diffs:
            return ['no candidate: %s' % d for d in diffs]
        if scene.tags() != [TAG_UNPROJECT, TAG_EMIT, TAG_ACT]:
            return ['no candidate: the call order is %s' % scene.tags()]
        act = _entries(h, scene.l_act, scene.cnt['act'], 2)
        if act != [(scene.tool, 0)]:
            return ['no candidate: the activation is %s' % act]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0
