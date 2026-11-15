"""The animation manager: its constructor (0x4C01B0), the singleton getter (0x4C0EE0) and its destructor
(0x4BFF70, entered through the deleting destructor 0x4C0220).

The manager is 0x54 bytes - the vtable, then two string maps (FsHashMap, 0x28 each): the loaded models at +04
and the animation clips at +2C.  Both maps start empty: mask and count 1, nine buckets aiming at the self-linked
sentinel.  The getter builds the manager once, keeps it in 0x6CA490 and throws when the 0x54-byte allocation
fails.  The destructor deletes each cached model's meshes through their vtable, destroys the model records and
keys, the clips (0x4BD430), the nodes, the bucket vectors and the sentinels."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x004C01B0
GET = 0x004C0EE0
DTOR = 0x004BFF70
DELETING_DTOR = 0x004C0220
MANAGER_GLOBAL = 0x006CA490
VFTABLE = 0x00611254
SINGLETON_VFTABLE = 0x00611238


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _check_map(h, mapobj):
    sentinel = _u32(h, mapobj + 8)
    if not sentinel:
        return 'no sentinel'
    if _u32(h, sentinel) != sentinel or _u32(h, sentinel + 4) != sentinel:
        return 'the sentinel does not link to itself'
    if _u32(h, mapobj + 0xC) != 0:
        return 'size %d' % _u32(h, mapobj + 0xC)
    if struct.unpack('<II', h.uc.mem_read(mapobj + 0x20, 8)) != (1, 1):
        return 'mask/count %r' % (h.uc.mem_read(mapobj + 0x20, 8),)
    begin = _u32(h, mapobj + 0x14)
    if _u32(h, mapobj + 0x18) - begin != 36:
        return 'bucket vector is %d bytes' % (_u32(h, mapobj + 0x18) - begin)
    for i in range(9):
        if _u32(h, begin + 4 * i) != sentinel:
            return 'bucket slot %d is %08X' % (i, _u32(h, begin + 4 * i))
    return None


def _check_manager(h, manager):
    if _u32(h, manager) != VFTABLE:
        return 'vtable %08X, want %08X' % (_u32(h, manager), VFTABLE)
    for name, base in (('models', manager + 4), ('animations', manager + 0x2C)):
        problem = _check_map(h, base)
        if problem:
            return '%s: %s' % (name, problem)
    return None


def test_manager_ctor(h):
    """Both map constructors only read one byte of the original's uninitialized stack slot, so the memory
    comparison is off (the byte leaks into the map's allocator field); the layout is checked by hand."""
    manager = h.alloc(0x54, bytes(0x54))
    diffs = h.compare(CTOR, regs={UC_X86_REG_ECX: manager}, ret='eax', mem=False)
    if diffs:
        return diffs
    res = h.call(CTOR, regs={UC_X86_REG_ECX: manager})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != manager:
        return ['returned %08X, want %08X' % (res['eax'], manager)]
    problem = _check_manager(h, manager)
    return [problem] if problem else []


def test_manager_getter(h):
    """the first call builds and stores the manager, later calls hand the same one back"""
    saved = bytes(h.uc.mem_read(MANAGER_GLOBAL, 4))
    try:
        h.uc.mem_write(MANAGER_GLOBAL, bytes(4))
        diffs = h.compare(GET, ret='eax')
        if diffs:
            return diffs
        res = h.call(GET)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        manager = _u32(h, MANAGER_GLOBAL)
        if not manager:
            return ['the getter did not store the manager']
        if res['eax'] != manager:
            return ['returned %08X, stored %08X' % (res['eax'], manager)]
        problem = _check_manager(h, manager)
        if problem:
            return [problem]
        again = h.call(GET)
        if again['fault']:
            return ['the second call faulted: %s' % again['fault']]
        if again['eax'] != manager or _u32(h, MANAGER_GLOBAL) != manager:
            return ['the second call returned %08X / stored %08X'
                    % (again['eax'], _u32(h, MANAGER_GLOBAL))]
        return []
    finally:
        h.uc.mem_write(MANAGER_GLOBAL, saved)


def _run_original(h, entry, args=(), regs=None):
    """call the original body the rebuilt entry jumps over (the jump is five bytes)"""
    original = bytes(h.orig.read(entry, 5))
    rebuilt = bytes(h.uc.mem_read(entry, 5))
    h.uc.mem_write(entry, original)
    try:
        return h.call(entry, args=args, regs=regs)
    finally:
        h.uc.mem_write(entry, rebuilt)


def test_manager_getter_throws_without_memory(h):
    """operator new failing (no manager) builds a CGameException and throws; nothing is stored"""
    saved = bytes(h.uc.mem_read(MANAGER_GLOBAL, 4))
    old = h.crt_new

    def fail_new():
        h._ret(0)

    h.crt_new = fail_new
    try:
        h.uc.mem_write(MANAGER_GLOBAL, bytes(4))
        original = _run_original(h, GET)
        if original['fault'] != 'threw':
            return ['the original did not throw: %r' % original['fault']]
        h.uc.mem_write(MANAGER_GLOBAL, bytes(4))
        res = h.call(GET)
        if res['fault'] != 'threw':
            return ['the replacement did not throw: %r' % res['fault']]
        stored = _u32(h, MANAGER_GLOBAL)
        if stored:
            return ['the getter stored %08X' % stored]
        return []
    finally:
        h.crt_new = old
        h.uc.mem_write(MANAGER_GLOBAL, saved)


def _put_inline_string(h, addr, text=b''):
    """a VC8 std::string that keeps its text inline (capacity 15, no heap buffer)"""
    assert len(text) < 16
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _thiscall_stub(h, code):
    area = h.alloc(len(code) + 4, bytes(len(code) + 4))
    h.uc.mem_write(area, code)
    return area


def _mesh(h, vtable):
    return h.alloc(0x74, struct.pack('<I', vtable) + bytes(0x70))


def _model_node(h, key, meshes):
    """a map node {next; prev; key; SkinModelRecord at +24} (0x44 bytes); meshes: the CSkinMesh pointers
    (null skips)"""
    node = h.alloc(0x44, bytes(0x44))
    _put_inline_string(h, node + 8, key)
    if meshes is not None:
        array = h.alloc(max(1, 4 * len(meshes)), b''.join(struct.pack('<I', m) for m in meshes) or bytes(4))
        h.uc.mem_write(node + 0x24 + 4, struct.pack('<III', array, array + 4 * len(meshes),
                                                   array + 4 * len(meshes)))
    return node


def _clip_node(h, key, clip):
    node = h.alloc(0x28, bytes(0x28))
    _put_inline_string(h, node + 8, key)
    h.uc.mem_write(node + 0x24, struct.pack('<I', clip))
    return node


def _ring(h, nodes):
    sentinel = h.alloc(0x10, bytes(0x10))
    ring = [sentinel] + nodes + [sentinel]
    for here, following in zip(ring, ring[1:]):
        h.uc.mem_write(here, struct.pack('<I', following))
    for here, previous in zip(ring[1:], ring):
        h.uc.mem_write(here + 4, struct.pack('<I', previous))
    return sentinel


def _map(h, base, sentinel, size):
    """the FsHashMap fields of a map: bucket vector, mask and count, the node ring at the sentinel"""
    buckets = h.alloc(36, struct.pack('<9I', *([sentinel] * 9)))
    h.uc.mem_write(base + 8, struct.pack('<II', sentinel, size))
    h.uc.mem_write(base + 0x14, struct.pack('<III', buckets, buckets + 36, buckets + 36))
    h.uc.mem_write(base + 0x20, struct.pack('<II', 1, 1))


def _populated_manager(h):
    """a manager holding one model (three mesh slots, one null) and two clips (one null), both maps 2 nodes"""
    dtor = _thiscall_stub(h, b'\x8b\xc1\xc2\x04\x00')  # mov eax, ecx; ret 4 (the mesh deleting dtor)
    vtable = h.alloc(8, struct.pack('<II', dtor, 0))
    mesh1, mesh2 = _mesh(h, vtable), _mesh(h, vtable)
    clip = h.alloc(0x38, bytes(0x38))

    manager = h.alloc(0x54, bytes(0x54))
    models = manager + 4
    models_sentinel = _ring(h, [_model_node(h, b'model1', [mesh1, 0, mesh2]),
                                _model_node(h, b'empty', None)])
    _map(h, models, models_sentinel, 2)

    animations = manager + 0x2C
    animations_sentinel = _ring(h, [_clip_node(h, b'clip1', clip), _clip_node(h, b'clip2', 0)])
    _map(h, animations, animations_sentinel, 2)
    return manager


def _check_destroyed(h, manager):
    if _u32(h, manager) != SINGLETON_VFTABLE:
        return 'vtable %08X, want %08X' % (_u32(h, manager), SINGLETON_VFTABLE)
    models, animations = manager + 4, manager + 0x2C
    for name, base in (('models', models), ('animations', animations)):
        if _u32(h, base + 8) != 0:
            return '%s sentinel %08X' % (name, _u32(h, base + 8))
        if _u32(h, base + 0xC) != 0:
            return '%s size %d' % (name, _u32(h, base + 0xC))
        if struct.unpack('<III', h.uc.mem_read(base + 0x14, 12)) != (0, 0, 0):
            return '%s vector %r' % (name, h.uc.mem_read(base + 0x14, 12))
        if struct.unpack('<II', h.uc.mem_read(base + 0x20, 8)) != (1, 1):
            return '%s mask/count %r' % (name, h.uc.mem_read(base + 0x20, 8))
    return None


def test_manager_dtor(h):
    manager = _populated_manager(h)
    diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: manager}, ret=None)
    if diffs:
        return diffs
    res = h.call(DTOR, regs={UC_X86_REG_ECX: manager})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    problem = _check_destroyed(h, manager)
    return [problem] if problem else []


def test_manager_deleting_dtor(h):
    manager = _populated_manager(h)
    args = [1]
    diffs = h.compare(DELETING_DTOR, args=args, regs={UC_X86_REG_ECX: manager}, ret='eax')
    if diffs:
        return diffs
    res = h.call(DELETING_DTOR, args=args, regs={UC_X86_REG_ECX: manager})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != manager:
        return ['returned %08X, want %08X' % (res['eax'], manager)]
    problem = _check_destroyed(h, manager)
    return [problem] if problem else []
