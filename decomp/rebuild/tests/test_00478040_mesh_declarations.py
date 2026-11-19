"""0x478040 (animated mesh vertex declarations): the first call (the dword counter at 0x6CA0A8 is zero)
creates the two declarations through device vtable +0x158, one over five elements followed by a terminator
(stream 0: TEXCOORD0; stream 1: POSITION0, NORMAL0) and one that also names stream 2 with usage index 1,
stores them at 0x6CA0A0 / 0x6CA09C and reports both results through 0x458940(".\\Mesh.cpp", 0x343/0x344);
then the counter is bumped and, with the pool at +0x40 clear, 0x476BB0 is called with (EAX=stream, ECX=this,
stream, flags).  The creation, lock and mesh entry points, the check callee and the device are stubbed."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

FN = 0x00478040
DEV_GLOBAL = 0x006C8C10
DECL1 = 0x006CA0A0
DECL2 = 0x006CA09C
COUNTER = 0x006CA0A8
CHECK = 0x00458940
MESH = 0x00476BB0
MESH_CPP = 0x0060EA44

UNUSED = 0x77777777
STREAM = 0x60000000
HR1 = 0x8007000E
FAKE = 0x4A4A0000

TAG_CREATE = 1
TAG_CHECK = 2
TAG_MESH = 3

ELEMENTS = [
    (0, 0, 1, 0, 5, 0),
    (1, 0, 2, 0, 0, 0),
    (1, 12, 2, 0, 3, 0),
    (255, 0, 17, 0, 0, 0),
    (0, 0, 1, 0, 5, 0),
    (1, 0, 2, 0, 0, 0),
    (1, 12, 2, 0, 3, 0),
    (2, 0, 2, 0, 0, 1),
    (2, 12, 2, 0, 3, 1),
    (255, 0, 17, 0, 0, 0),
]
ELEMENT_BYTES = b''.join(struct.pack('<HHBBBB', *e) for e in ELEMENTS)
COPY = 0x30                     # the stub logs this many bytes of each declaration

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


def _thunk_to(h, address, stub):
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _tag(seq, tag):
    """appends tag to the sequence at seq (count at +0, entries from +4)"""
    return (b'\xA1' + _dword(seq) +                                   # mov eax,[seq]
            b'\xFF\x05' + _dword(seq) +                               # inc dword [seq]
            b'\xC7\x04\x85' + _dword(seq + 4) + _dword(tag))          # mov dword [seq+4+eax*4],tag


def _create_stub(h, seq, log, cnt):
    """vf0x158(dev, elems, &decl): logs dev, &decl and COPY bytes of the elements (0x40-byte entries),
    stores FAKE + call into *decl and returns HR1 for the first call, 0 for the second"""
    code = _tag(seq, TAG_CREATE)
    code += b'\x8B\x15' + _dword(cnt) + b'\xFF\x05' + _dword(cnt)     # mov edx,[cnt]; inc [cnt]
    code += b'\x8B\xC2' + b'\xC1\xE0\x06' + b'\x05' + _dword(log)    # eax = log + edx*0x40
    code += b'\x8B\x4C\x24\x04' + b'\x89\x08'                         # dev
    code += b'\x8B\x4C\x24\x0C' + b'\x89\x48\x04'                     # &decl
    code += b'\x8B\x4C\x24\x08'                                       # mov ecx,[esp+8] (elements)
    for k in range(0, COPY, 4):
        code += (b'\x8B\x11' if k == 0 else b'\x8B\x91' + _dword(k))
        code += b'\x89\x90' + _dword(8 + k)                           # mov [eax+8+k],edx
    code += b'\x8B\x15' + _dword(cnt) + b'\x83\xEA\x01'               # mov edx,[cnt]; sub edx,1
    code += b'\x81\xC2' + _dword(FAKE)                                # add edx,FAKE
    code += b'\x8B\x4C\x24\x0C' + b'\x89\x11'                         # mov ecx,[esp+0xC]; mov [ecx],edx
    code += b'\xA1' + _dword(cnt) + b'\x83\xE8\x01'                   # mov eax,[cnt]; sub eax,1
    code += b'\x85\xC0' + b'\xB8' + _dword(0)                         # test eax,eax; mov eax,0
    code += b'\x75\x05'                                               # jnz past the first-call HRESULT
    code += b'\xB8' + _dword(HR1)                                     # mov eax,HR1
    code += b'\xC2\x0C\x00'                                           # ret 0xC
    return _stub(h, code)


def _check_stub(h, seq, log, cnt):
    """0x458940(hr, file, line): logs the three arguments (0xC-byte entries)"""
    code = _tag(seq, TAG_CHECK)
    code += b'\x8B\x15' + _dword(cnt) + b'\xFF\x05' + _dword(cnt)     # mov edx,[cnt]; inc [cnt]
    code += b'\x8D\x04\x52' + b'\xC1\xE0\x02' + b'\x05' + _dword(log)  # eax = log + edx*12
    code += b'\x8B\x4C\x24\x04' + b'\x89\x08'
    code += b'\x8B\x4C\x24\x08' + b'\x89\x48\x04'
    code += b'\x8B\x4C\x24\x0C' + b'\x89\x48\x08'
    code += b'\xC3'
    return _stub(h, code)


def _mesh_stub(h, seq, log):
    """0x476BB0 entry: logs EAX, ECX and both stack arguments, returns 0x1234"""
    code = b'\xA3' + _dword(log)                                     # mov [log],eax (before _tag reuses EAX)
    code += _tag(seq, TAG_MESH)
    code += b'\x89\x0D' + _dword(log + 4)                             # mov [log+4],ecx
    code += b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 8)           # mov eax,[esp+4]; mov [log+8],eax
    code += b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 0xC)         # mov eax,[esp+8]; mov [log+0xC],eax
    code += b'\xB8\x34\x12\x00\x00' + b'\xC2\x08\x00'                 # mov eax,0x1234; ret 8
    return _stub(h, code)


class Scene:
    def __init__(self, h, counter, pool):
        self.seq = h.alloc(0x40, bytes(0x40))
        self.create_log = h.alloc(0x80, bytes(0x80))
        self.create_cnt = h.alloc(0x10, bytes(0x10))
        self.check_log = h.alloc(0x40, bytes(0x40))
        self.check_cnt = h.alloc(0x10, bytes(0x10))
        self.mesh_log = h.alloc(0x10, bytes(0x10))
        self.this = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(self.this + 0x40, _dword(pool))
        device = h.alloc(0x10, bytes(0x10))
        dev_vt = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(device, _dword(dev_vt))
        h.uc.mem_write(dev_vt + 0x158, _dword(_create_stub(h, self.seq, self.create_log, self.create_cnt)))
        self.device = device
        _patch(h, DEV_GLOBAL, _dword(device))
        _patch(h, COUNTER, _dword(counter))
        # both callees resolve to their original addresses; 0x476BB0's call also goes through the build's
        # cdecl shim on that entry, which must keep running, so only the entry itself is redirected
        _thunk_to(h, CHECK, _check_stub(h, self.seq, self.check_log, self.check_cnt))
        _thunk_to(h, MESH, _mesh_stub(h, self.seq, self.mesh_log))


def _run(h, scene, flags):
    start = _u32(h, COUNTER)
    creates = 2 if start == 0 else 0
    tags = []
    for _ in range(creates):
        tags += [TAG_CREATE, TAG_CHECK]
    if not _u32(h, scene.this + 0x40):
        tags.append(TAG_MESH)
    diffs = h.compare(FN, args=[STREAM, UNUSED, flags], regs={UC_X86_REG_ECX: scene.this}, ret=None)
    if diffs:
        return diffs
    result = h.call(FN, args=[STREAM, UNUSED, flags], regs={UC_X86_REG_ECX: scene.this})
    if result['fault']:
        return [result['fault']]
    problems = []
    got = [_u32(h, scene.seq + 4 + i * 4) for i in range(_u32(h, scene.seq))]
    if got != tags:
        problems.append('calls %r' % got)
        return problems
    if result['esp'] != 0x10:
        problems.append('esp delta %#x' % result['esp'])
    if _u32(h, COUNTER) != start + 1:
        problems.append('counter %d -> %d' % (start, _u32(h, COUNTER)))
    if creates:
        for i, (want_out, chunk) in enumerate(((DECL1, ELEMENT_BYTES[:COPY]),
                                               (DECL2, ELEMENT_BYTES[4 * 8:4 * 8 + COPY]))):
            e = scene.create_log + i * 0x40
            if (_u32(h, e), _u32(h, e + 4)) != (scene.device, want_out):
                problems.append('create %d args %r' % (i, [_u32(h, e), _u32(h, e + 4)]))
            if bytes(h.uc.mem_read(e + 8, COPY)) != chunk:
                problems.append('create %d elements %s' % (i, bytes(h.uc.mem_read(e + 8, COPY)).hex()))
        if _u32(h, DECL1) != FAKE or _u32(h, DECL2) != FAKE + 1:
            problems.append('declarations %#x, %#x' % (_u32(h, DECL1), _u32(h, DECL2)))
        for i, (want_hr, want_line) in enumerate(((HR1, 0x343), (0, 0x344))):
            e = scene.check_log + i * 0xC
            if (_u32(h, e), _u32(h, e + 4), _u32(h, e + 8)) != (want_hr, MESH_CPP, want_line):
                problems.append('check %d %r' % (i, [_u32(h, e + 4 * k) for k in range(3)]))
    if not _u32(h, scene.this + 0x40):
        want = (STREAM, scene.this, STREAM, flags)
        got = tuple(_u32(h, scene.mesh_log + 4 * k) for k in range(4))
        if got != want:
            problems.append('mesh call %r' % (got,))
    return problems


def _case(h, counter, pool, flags=1):
    heap0 = h.heap_ptr
    try:
        scene = Scene(h, counter, pool)
        return _run(h, scene, flags) or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_creates_declarations_and_fills_buffers(h):
    """fresh counter, no pool: both declarations are created and 0x476BB0 is called"""
    return _case(h, 0, 0)


def test_skips_declaration_creation(h):
    """a non-zero counter skips the declarations but the mesh buffers are still set up"""
    return _case(h, 3, 0)


def test_skips_everything_but_the_counter(h):
    """a non-zero counter and a pool set: only the counter moves"""
    return _case(h, 5, 0x10)


def test_creates_declarations_without_mesh(h):
    """a fresh counter with the pool already set creates the declarations only"""
    return _case(h, 0, 8)

