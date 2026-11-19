"""0x476BB0 (_ST_ANIM_MESH buffer creation): with flag 1, every index subset gets a 16-bit index buffer
(6 bytes per index, format 0x65, usage/pool from +0x44/+0x40) filled from its data or through the stream
(seek to the entry's offset, read); the vertex buffer at +0x2C (8 bytes per vertex) and every entry of the
second table (0x18 bytes per vertex) follow.  The device, the buffers and the stream are stubbed; the
creation, lock, seek and read arguments and their order are logged, and the copies are checked."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

FN = 0x00476BB0
DEV_GLOBAL = 0x006C8C10
CHECK = 0x00458940
READ = 0x00458F80
MESH_CPP = 0x0060EA44         # ".\Mesh.cpp"

USAGE = 8
POOL = 1
FMT_INDEX = 0x65
IN_EAX = 0x5A5A5A5A
SEQ_SIZE = 0x200

TAG_CREATE_IDX = 1
TAG_CREATE_VTX = 2
TAG_CHECK = 3
TAG_SEEK = 4
TAG_READ = 5

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


def _patch_callee(h, address, stub):
    """the original body calls the entry; the rebuilt code may call the glue implementation directly"""
    _thunk_to(h, address, stub)
    target = h.symbols.get('_sub_%08X' % address)
    if target is not None and target != address:
        _thunk_to(h, target, stub)


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


def _store_index(base, stride):
    """eax = base + edx * stride (stride 8, 0xC or 0x20)"""
    if stride == 8:
        return b'\x8B\xC2' + b'\xC1\xE0\x03' + b'\x05' + _dword(base)
    if stride == 0xC:
        return b'\x8D\x04\x52' + b'\xC1\xE0\x02' + b'\x05' + _dword(base)
    return b'\x8B\xC2' + b'\xC1\xE0\x05' + b'\x05' + _dword(base)


def _next(cnt):
    return b'\x8B\x15' + _dword(cnt) + b'\xFF\x05' + _dword(cnt)      # mov edx,[cnt]; inc [cnt]


def _mov_ecx_arg(offset):
    return b'\x8B\x4C\x24' + bytes([offset])                          # mov ecx,[esp+offset]


def _mov_mem_eax(offset, value):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(value)  # mov eax,[esp+n]; mov [value],eax


def _create_stub(h, seq, tag, log, cnt, objs):
    """vf0x68/vf0x6C(dev, len, usage, fmt, pool, &out, h): logs every argument (0x20-byte entries),
    writes objs[call] into *out and returns 0"""
    code = _tag(seq, tag)
    code += _next(cnt)
    code += _store_index(log, 0x20)
    for slot, arg in ((0x00, 0x04), (0x04, 0x08), (0x08, 0x0C), (0x0C, 0x10), (0x10, 0x14),
                      (0x14, 0x18), (0x18, 0x1C)):
        code += _mov_ecx_arg(arg)
        code += (b'\x89\x08' if slot == 0 else b'\x89\x48' + bytes([slot]))
    code += b'\x8B\x0C\x95' + _dword(objs)                            # mov ecx,[edx*4+objs]
    code += b'\x8B\x44\x24\x18'                                       # mov eax,[esp+0x18] (out)
    code += b'\x89\x08'                                               # mov [eax],ecx
    code += b'\x33\xC0' + b'\xC2\x1C\x00'                             # xor eax,eax; ret 0x1C
    return _stub(h, code)


def _lock_stub(h, seq, tag, log, data):
    """vf0x2C(buf, off, size, &data, flags): logs the arguments and hands out data"""
    code = _tag(seq, tag)
    code += _mov_mem_eax(0x04, log)                                   # self
    code += _mov_mem_eax(0x08, log + 4)                               # off
    code += _mov_mem_eax(0x0C, log + 8)                               # size
    code += _mov_mem_eax(0x14, log + 0xC)                             # flags
    code += _mov_ecx_arg(0x10) + b'\xC7\x01' + _dword(data)           # mov dword [ecx],data
    code += b'\x33\xC0' + b'\xC2\x14\x00'                             # xor eax,eax; ret 0x14
    return _stub(h, code)


def _unlock_stub(h, seq, tag, log, value):
    """vf0x30(buf): logs buf and returns value"""
    code = _tag(seq, tag)
    code += _mov_mem_eax(0x04, log)                                   # self
    code += b'\xB8' + _dword(value) + b'\xC2\x04\x00'                 # mov eax,value; ret 4
    return _stub(h, code)


def _seek_stub(h, seq, tag, log, cnt):
    """file vf0x8(reader, off): logs reader and off, returns nothing"""
    code = _tag(seq, tag)
    code += _next(cnt) + _store_index(log, 8)
    code += b'\x89\x08'                                               # mov [eax],ecx (reader)
    code += _mov_ecx_arg(0x04) + b'\x89\x48\x04'                      # off
    code += b'\xC2\x04\x00'                                           # ret 4
    return _stub(h, code)


def _read_stub(h, seq, tag, log, cnt, marker):
    """0x458F80(stream, dst, size): logs the arguments and writes marker at dst"""
    code = _tag(seq, tag)
    code += _next(cnt) + _store_index(log, 0xC)
    code += b'\x89\x08'                                               # stream
    code += _mov_ecx_arg(0x04) + b'\x89\x48\x04'                      # dst
    code += _mov_ecx_arg(0x08) + b'\x89\x48\x08'                      # size
    code += _mov_ecx_arg(0x04) + b'\xC7\x01' + _dword(marker)         # mov dword [ecx],marker
    code += b'\xC2\x08\x00'                                           # ret 8
    return _stub(h, code)


def _check_stub(h, seq, tag, log, cnt):
    """0x458940(hr, file, line): logs the three arguments (0xC-byte entries)"""
    code = _tag(seq, tag)
    code += _next(cnt) + _store_index(log, 0xC)
    code += _mov_ecx_arg(0x04) + b'\x89\x08'
    code += _mov_ecx_arg(0x08) + b'\x89\x48\x04'
    code += _mov_ecx_arg(0x0C) + b'\x89\x48\x08'
    code += b'\xC3'
    return _stub(h, code)


class Scene:
    def __init__(self, h, counts, subsrc, vcount, vsrc, second):
        self.counts, self.subsrc, self.vcount, self.vsrc, self.second = \
            counts, subsrc, vcount, vsrc, second
        self.seq = h.alloc(SEQ_SIZE, bytes(SEQ_SIZE))
        self.idx_log = h.alloc(0x100, bytes(0x100))
        self.idx_cnt = h.alloc(0x10, bytes(0x10))
        self.vtx_log = h.alloc(0x100, bytes(0x100))
        self.vtx_cnt = h.alloc(0x10, bytes(0x10))
        self.check_log = h.alloc(0x100, bytes(0x100))
        self.check_cnt = h.alloc(0x10, bytes(0x10))
        self.seek_log = h.alloc(0x40, bytes(0x40))
        self.seek_cnt = h.alloc(0x10, bytes(0x10))
        self.read_log = h.alloc(0x100, bytes(0x100))
        self.read_cnt = h.alloc(0x10, bytes(0x10))
        total = len(counts) + 1 + len(second)
        self.total = total
        self.lock_logs = h.alloc(total * 0x10, bytes(total * 0x10))
        self.unlock_logs = h.alloc(total * 0x10, bytes(total * 0x10))

        self.this = h.alloc(0x100, bytes(0x100))
        self.idxarr = h.alloc(0x40, bytes(0x40))
        self.secarr = h.alloc(0x40, bytes(0x40))
        self.stream = h.alloc(0x40, bytes(0x40))
        reader = h.alloc(0x10, bytes(0x10))
        reader_vt = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(reader, _dword(reader_vt))
        h.uc.mem_write(reader_vt + 0x8, _dword(_seek_stub(h, self.seq, TAG_SEEK, self.seek_log, self.seek_cnt)))
        h.uc.mem_write(self.stream + 0x24, _dword(reader))

        for i, n in enumerate(counts):
            e = self.idxarr + i * 0x10
            h.uc.mem_write(e + 0, _dword(n))
            h.uc.mem_write(e + 4, _dword(subsrc[i]))
            h.uc.mem_write(e + 0xC, _dword(0x1111 + i))
        h.uc.mem_write(self.this + 0x8, _dword(self.idxarr))
        h.uc.mem_write(self.this + 0xC, _dword(len(counts)))
        h.uc.mem_write(self.this + 0x24, _dword(vcount))
        h.uc.mem_write(self.this + 0x28, _dword(vsrc))
        h.uc.mem_write(self.this + 0x30, _dword(0x3333))
        h.uc.mem_write(self.this + 0x34, _dword(len(second)))
        h.uc.mem_write(self.this + 0x38, _dword(self.secarr))
        h.uc.mem_write(self.this + 0x40, _dword(POOL))
        h.uc.mem_write(self.this + 0x44, _dword(USAGE))
        for j, src in enumerate(second):
            e = self.secarr + j * 0xC
            h.uc.mem_write(e + 0, _dword(src))
            h.uc.mem_write(e + 8, _dword(0x4444 + j))

        self.data = [h.alloc(0x100, b'\xCC' * 0x100) for _ in range(total)]
        self.buffers = []
        for i in range(total):
            vt = h.alloc(0x40, bytes(0x40))
            obj = h.alloc(0x10, bytes(0x10))
            h.uc.mem_write(obj, _dword(vt))
            lock_code = _lock_stub(h, self.seq, 0x10 + i, self.lock_logs + i * 0x10, self.data[i])
            h.uc.mem_write(vt + 0x2C, _dword(lock_code))
            unlock_code = _unlock_stub(h, self.seq, 0x20 + i, self.unlock_logs + i * 0x10, 0x100 + i)
            h.uc.mem_write(vt + 0x30, _dword(unlock_code))
            self.buffers.append(obj)

        idx_objs = h.alloc(0x10, bytes(0x10))
        for i in range(len(counts)):
            h.uc.mem_write(idx_objs + i * 4, _dword(self.buffers[i]))
        vtx_objs = h.alloc(0x10, bytes(0x10))
        for i in range(1 + len(second)):
            h.uc.mem_write(vtx_objs + i * 4, _dword(self.buffers[len(counts) + i]))

        device = h.alloc(0x10, bytes(0x10))
        dev_vt = h.alloc(0x80, bytes(0x80))
        h.uc.mem_write(device, _dword(dev_vt))
        h.uc.mem_write(dev_vt + 0x6C, _dword(_create_stub(h, self.seq, TAG_CREATE_IDX, self.idx_log,
                                                          self.idx_cnt, idx_objs)))
        h.uc.mem_write(dev_vt + 0x68, _dword(_create_stub(h, self.seq, TAG_CREATE_VTX, self.vtx_log,
                                                          self.vtx_cnt, vtx_objs)))
        self.device = device
        _patch(h, DEV_GLOBAL, _dword(device))
        _patch_callee(h, CHECK, _check_stub(h, self.seq, TAG_CHECK, self.check_log, self.check_cnt))
        _patch_callee(h, READ, _read_stub(h, self.seq, TAG_READ, self.read_log, self.read_cnt, 0xA0))

    def creation(self):
        """(tags, buffer sizes, sources) in creation order"""
        sizes, sources, tags = [], [], []
        for i, n in enumerate(self.counts):
            sizes.append(n * 6)
            sources.append(self.subsrc[i])
        sizes.append(self.vcount * 8)
        sources.append(self.vsrc)
        for src in self.second:
            sizes.append(self.vcount * 0x18)
            sources.append(src)
        for i, src in enumerate(sources):
            tags.append(TAG_CREATE_IDX if i < len(self.counts) else TAG_CREATE_VTX)
            tags.append(TAG_CHECK)
            tags.append(0x10 + i)
            if not src:
                tags.append(TAG_SEEK)
                tags.append(TAG_READ)
            tags.append(0x20 + i)
        return tags, sizes, sources

    def slots(self, h):
        """the buffer-pointer slots (where each creation wrote its object)"""
        found = [self.idxarr + i * 0x10 + 8 for i in range(len(self.counts))]
        found.append(self.this + 0x2C)
        found += [self.secarr + j * 0xC + 4 for j in range(len(self.second))]
        return found

    def reset(self, h):
        """clears the logs and the destination buffers the compare run filled"""
        h.uc.mem_write(self.seq, bytes(SEQ_SIZE))
        for log, size in ((self.idx_log, 0x100), (self.vtx_log, 0x100), (self.check_log, 0x100),
                          (self.seek_log, 0x40), (self.read_log, 0x100),
                          (self.lock_logs, self.total * 0x10), (self.unlock_logs, self.total * 0x10)):
            h.uc.mem_write(log, bytes(size))
        for cnt in (self.idx_cnt, self.vtx_cnt, self.check_cnt, self.seek_cnt, self.read_cnt):
            h.uc.mem_write(cnt, bytes(0x10))
        for data in self.data:
            h.uc.mem_write(data, b'\xCC' * 0x100)
        for slot in self.slots(h):
            h.uc.mem_write(slot, _dword(0))


def _run(h, scene, flags):
    tags, sizes, sources = scene.creation()
    if not flags & 1:
        tags = []
    diffs = h.compare(FN, args=[scene.stream, flags], regs={UC_X86_REG_ECX: scene.this,
                                                            UC_X86_REG_EAX: IN_EAX}, ret='eax')
    if diffs:
        return diffs
    scene.reset(h)
    result = h.call(FN, args=[scene.stream, flags], regs={UC_X86_REG_ECX: scene.this,
                                                          UC_X86_REG_EAX: IN_EAX})
    if result['fault']:
        return [result['fault']]
    problems = []
    got = [_u32(h, scene.seq + 4 + i * 4) for i in range(_u32(h, scene.seq))]
    if got != tags:
        problems.append('calls %r' % got)
        return problems
    if not flags & 1:
        if result['eax'] != IN_EAX:
            problems.append('flag 0 returns %#x' % result['eax'])
        return problems
    idx_n = len(scene.counts)
    for i in range(idx_n):
        if (_u32(h, scene.idx_log + i * 0x20), _u32(h, scene.idx_log + i * 0x20 + 4),
                _u32(h, scene.idx_log + i * 0x20 + 8), _u32(h, scene.idx_log + i * 0x20 + 0xC),
                _u32(h, scene.idx_log + i * 0x20 + 0x10), _u32(h, scene.idx_log + i * 0x20 + 0x14),
                _u32(h, scene.idx_log + i * 0x20 + 0x18)) != \
                (scene.device, sizes[i], USAGE, FMT_INDEX, POOL, scene.idxarr + i * 0x10 + 8, 0):
            problems.append('index create %d %r' % (i, [_u32(h, scene.idx_log + i * 0x20 + 4 * k)
                                                       for k in range(7)]))
    for i in range(1 + len(scene.second)):
        k = idx_n + i
        if (_u32(h, scene.vtx_log + i * 0x20), _u32(h, scene.vtx_log + i * 0x20 + 4),
                _u32(h, scene.vtx_log + i * 0x20 + 8), _u32(h, scene.vtx_log + i * 0x20 + 0xC),
                _u32(h, scene.vtx_log + i * 0x20 + 0x10), _u32(h, scene.vtx_log + i * 0x20 + 0x14),
                _u32(h, scene.vtx_log + i * 0x20 + 0x18)) != \
                (scene.device, sizes[k], USAGE, 0, POOL, scene.slots(h)[k], 0):
            problems.append('vertex create %d %r' % (i, [_u32(h, scene.vtx_log + i * 0x20 + 4 * k2)
                                                         for k2 in range(7)]))
    for i, size in enumerate(sizes):
        self_ptr = _u32(h, scene.lock_logs + i * 0x10)
        if self_ptr != scene.buffers[i] or (_u32(h, scene.lock_logs + i * 0x10 + 4),
                                            _u32(h, scene.lock_logs + i * 0x10 + 8),
                                            _u32(h, scene.lock_logs + i * 0x10 + 0xC)) != (0, size, 0):
            problems.append('lock %d %r' % (i, [_u32(h, scene.lock_logs + i * 0x10 + 4 * k)
                                                for k in range(4)]))
        if _u32(h, scene.unlock_logs + i * 0x10) != scene.buffers[i]:
            problems.append('unlock %d %r' % (i, _u32(h, scene.unlock_logs + i * 0x10)))
        if _u32(h, scene.slots(h)[i]) != scene.buffers[i]:
            problems.append('slot %d %#x' % (i, _u32(h, scene.slots(h)[i])))
        area = bytes(h.uc.mem_read(scene.data[i], 0x100))
        if sources[i]:
            want = bytes(h.uc.mem_read(sources[i], size))
            if area[:size] != want or area[size] != 0xCC:
                problems.append('buffer %d not copied' % i)
        else:
            if _u32(h, scene.data[i]) != 0xA0 or area[4] != 0xCC:
                problems.append('buffer %d not read' % i)
    seeks = [_u32(h, scene.seek_log + i * 8) for i in range(_u32(h, scene.seek_cnt))]
    offs = [_u32(h, scene.seek_log + i * 8 + 4) for i in range(_u32(h, scene.seek_cnt))]
    want = [0x1111 + i for i, src in enumerate(scene.subsrc) if not src]
    if not scene.vsrc:
        want.append(0x3333)
    want += [0x4444 + j for j, src in enumerate(scene.second) if not src]
    if offs != want:
        problems.append('seeks %r' % offs)
    if any(reader != _u32(h, scene.stream + 0x24) for reader in seeks):
        problems.append('seek targets %r' % seeks)
    reads = [_u32(h, scene.read_log + i * 0xC + 8) for i in range(_u32(h, scene.read_cnt))]
    if reads != [size for i, size in enumerate(sizes) if not sources[i]]:
        problems.append('read sizes %r' % reads)
    if any(_u32(h, scene.read_log + i * 0xC) != scene.stream for i in range(_u32(h, scene.read_cnt))):
        problems.append('read streams differ')
    if result['eax'] != 0x100 + len(sizes) - 1:
        problems.append('returns %#x' % result['eax'])
    return problems


def _case(h, counts, subsrc, vcount, vsrc, second, flags=1):
    heap0 = h.heap_ptr
    try:
        scene = Scene(h, counts, subsrc, vcount, vsrc, second)
        return _run(h, scene, flags)
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_memory_sources(h):
    """two index subsets, the vertex buffer and one second-table entry, all with CPU data"""
    s0 = h.alloc(0x40, bytes(range(0x24)))
    s1 = h.alloc(0x40, bytes(range(0x24, 0x48)))
    sv = h.alloc(0x40, bytes(range(0x48, 0x68)))
    st = h.alloc(0x80, bytes(range(0x68, 0xE8)))
    return _case(h, [6, 9], [s0, s1], 4, sv, [st]) or None


def test_stream_sources(h):
    """everything without CPU data is seeked and read from the stream"""
    sv = h.alloc(0x40, bytes(range(0x48, 0x68)))
    st = h.alloc(0x80, bytes(range(0x68, 0xE8)))
    return _case(h, [6, 9], [0, 0], 4, 0, [0, st]) or None


def test_empty_tables(h):
    sv = h.alloc(0x40, bytes(range(0x20)))
    return _case(h, [], [], 2, sv, []) or None


def test_flag_clear(h):
    sv = h.alloc(0x40, bytes(range(0x20)))
    return _case(h, [6], [sv], 4, sv, [sv], flags=0) or None
