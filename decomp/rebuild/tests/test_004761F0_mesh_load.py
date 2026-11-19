"""0x4761F0 (animated mesh stream load): resets the subset vector at +0x4 to the leading count and, for every
entry (count +0, data +4, buffer +8, offset +0xC), reads its index count, records the reader's tell position
(reader at stream+0x24, vf+0x10), reads count*6 index bytes into a new CPU array (flag 2) and, with flag 1,
creates a 0x65-format index buffer, locks it, fills it from that array or straight from the stream and unlocks
it (checks go to 0x458940 with ".\\Mesh.cpp" line 0x61).  Entry 0 is copied to +0x10..+0x20, then the vertex
count (+0x24), its tell (+0x30) and, when positive, the 0x20-byte vertices are handled the same way (format
0x112, line 0x89, array +0x28, buffer +0x2C).  The stream reads replay a scripted byte buffer and advance a
shared cursor, so the recorded tell offsets and the copied bytes can be checked."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

FN = 0x004761F0
DEV_GLOBAL = 0x006C8C10
CHECK = 0x00458940
READ = 0x00458F80
MESH_CPP = 0x0060EA44

UNUSED = 0x77777777
USAGE = 8
FMT_INDEX = 0x65
FMT_VERTEX = 0x112
IN_EAX = 0x5A5A5A5A

TAG_CREATE = 1
TAG_CHECK = 2
TAG_LOCK = 3
TAG_UNLOCK = 4
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


def _next(cnt):
    return b'\x8B\x15' + _dword(cnt) + b'\xFF\x05' + _dword(cnt)      # mov edx,[cnt]; inc [cnt]


def _read_stub(h, seq, cnt, log, script, cursor):
    """0x458F80(stream, dst, size) thiscall: logs the stream and size (8-byte entries), copies size bytes from
    script + cursor to dst and advances the cursor"""
    code = _tag(seq, TAG_READ)
    code += _next(cnt)
    code += b'\x8B\xC2' + b'\xC1\xE0\x03' + b'\x05' + _dword(log)     # eax = log + edx*8
    code += b'\x89\x08'                                               # [eax] = ecx (stream)
    code += b'\x8B\x54\x24\x08' + b'\x89\x50\x04'                     # [eax+4] = size
    code += b'\x56' + b'\x57'                                         # push esi, edi
    code += b'\xBE' + _dword(script) + b'\x03\x35' + _dword(cursor)   # esi = script + [cursor]
    code += b'\x8B\x7C\x24\x0C'                                       # edi = [esp+0xC] dst
    code += b'\x8B\x4C\x24\x10'                                       # ecx = [esp+0x10] size
    code += b'\x01\x0D' + _dword(cursor)                              # [cursor] += ecx
    code += b'\xFC' + b'\xF3\xA4'                                     # cld; rep movsb
    code += b'\x5F' + b'\x5E'                                         # pop edi, esi
    code += b'\xC2\x08\x00'                                           # ret 8
    return _stub(h, code)


def _tell_stub(h, cursor):
    """reader vf0x10: returns the current script cursor"""
    return _stub(h, b'\xA1' + _dword(cursor) + b'\xC3')               # mov eax,[cursor]; ret


def _create_stub(h, seq, log, cnt, objs):
    """vf0x68/vf0x6C(dev, len, usage, fmt, pool, &out, shared): logs every argument (0x20-byte entries),
    stores objs[call] into *out and returns 0"""
    code = _tag(seq, TAG_CREATE)
    code += _next(cnt)
    code += b'\x8B\xC2' + b'\xC1\xE0\x05' + b'\x05' + _dword(log)     # eax = log + edx*0x20
    for k in range(7):
        code += b'\x8B\x4C\x24' + bytes([4 + 4 * k])
        code += (b'\x89\x08' if k == 0 else b'\x89\x48' + bytes([4 * k]))
    code += b'\x8B\x0C\x95' + _dword(objs)                            # ecx = objs[edx]
    code += b'\x8B\x54\x24\x18' + b'\x89\x0A'                         # mov edx,[esp+0x18]; mov [edx],ecx
    code += b'\x33\xC0' + b'\xC2\x1C\x00'                             # xor eax,eax; ret 0x1C
    return _stub(h, code)


def _lock_stub(h, seq, log, cnt, dataobjs):
    """vf0x2C(buf, off, size, &data, flags): logs buf/off/size/flags (0x10-byte entries) and hands out
    dataobjs[call] as the lockable data"""
    code = _tag(seq, TAG_LOCK)
    code += _next(cnt)
    code += b'\x8B\xC2' + b'\xC1\xE0\x04' + b'\x05' + _dword(log)     # eax = log + edx*0x10
    for k, esp_off in ((0, 0x04), (1, 0x08), (2, 0x0C), (3, 0x14)):
        code += b'\x8B\x4C\x24' + bytes([esp_off])
        code += (b'\x89\x08' if k == 0 else b'\x89\x48' + bytes([4 * k]))
    code += b'\x8B\x0C\x95' + _dword(dataobjs)                        # ecx = dataobjs[edx]
    code += b'\x8B\x54\x24\x10' + b'\x89\x0A'                         # mov edx,[esp+0x10]; mov [edx],ecx
    code += b'\x33\xC0' + b'\xC2\x14\x00'                             # xor eax,eax; ret 0x14
    return _stub(h, code)


def _unlock_stub(h, seq, log, cnt):
    """vf0x30(buf): logs the buffer pointer and returns 0"""
    return _stub(h, b'\x8B\x4C\x24\x04' + _tag(seq, TAG_UNLOCK) + _next(cnt) +
                 b'\x89\x0C\x95' + _dword(log) +                      # mov [log+edx*4],ecx
                 b'\x33\xC0' + b'\xC2\x04\x00')                       # xor eax,eax; ret 4


def _check_stub(h, seq, log, cnt):
    """0x458940(hr, file, line): logs the three arguments (0xC-byte entries)"""
    code = _tag(seq, TAG_CHECK)
    code += _next(cnt)
    code += b'\x8B\xC2' + b'\x8D\x04\x52' + b'\xC1\xE0\x02' + b'\x05' + _dword(log)
    code += b'\x8B\x4C\x24\x04' + b'\x89\x08'
    code += b'\x8B\x4C\x24\x08' + b'\x89\x48\x04'
    code += b'\x8B\x4C\x24\x0C' + b'\x89\x48\x08'
    code += b'\xC3'
    return _stub(h, code)


class Scene:
    def __init__(self, h, counts, vcount):
        self.counts = counts
        self.vcount = vcount
        # indices of the subsets that carry data, in stream order
        self.nz = [i for i, n in enumerate(counts) if n]
        self.nsub = len(self.nz)
        self.nbuf = self.nsub + (1 if vcount else 0)

        self.seq = h.alloc(0x200, bytes(0x200))
        self.read_log = h.alloc(0x100, bytes(0x100))
        self.read_cnt = h.alloc(0x10, bytes(0x10))
        self.create_log = h.alloc(0x100, bytes(0x100))
        self.create_cnt = h.alloc(0x10, bytes(0x10))
        self.check_log = h.alloc(0x100, bytes(0x100))
        self.check_cnt = h.alloc(0x10, bytes(0x10))
        self.lock_log = h.alloc(0x100, bytes(0x100))
        self.lock_cnt = h.alloc(0x10, bytes(0x10))
        self.unlock_log = h.alloc(0x40, bytes(0x40))
        self.unlock_cnt = h.alloc(0x10, bytes(0x10))

        self.sub_data = {}
        self.sub_offsets = {}
        parts = [_dword(len(counts))]
        pos = 4
        for i, n in enumerate(counts):
            parts.append(_dword(n))
            if n:
                self.sub_data[i] = bytes((i * 13 + j * 5 + 1) & 0xFF for j in range(n * 6))
                self.sub_offsets[i] = pos + 4
                parts.append(self.sub_data[i])
            pos += 4 + n * 6
        parts.append(_dword(vcount))
        self.vtx_data = b''
        self.vtx_offset = 0
        if vcount:
            self.vtx_data = bytes((0x40 + j * 3) & 0xFF for j in range(vcount * 0x20))
            self.vtx_offset = pos + 4
            parts.append(self.vtx_data)
        script_bytes = b''.join(parts)

        self.this = h.alloc(0x80, bytes(0x80))
        self.script = h.alloc(len(script_bytes), script_bytes)
        self.cursor = h.alloc(4, bytes(4))
        self.stream = h.alloc(0x40, bytes(0x40))
        reader = h.alloc(0x10, bytes(0x10))
        reader_vt = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(reader, _dword(reader_vt))
        h.uc.mem_write(reader_vt + 0x10, _dword(_tell_stub(h, self.cursor)))
        h.uc.mem_write(self.stream + 0x24, _dword(reader))

        self.buffer_data = [h.alloc(0x100, b'\xCC' * 0x100) for _ in range(self.nbuf)]
        dataobjs = h.alloc(0x40, bytes(0x40))
        for i in range(self.nbuf):
            h.uc.mem_write(dataobjs + i * 4, _dword(self.buffer_data[i]))
        self.buffers = []
        for i in range(self.nbuf):
            vt = h.alloc(0x40, bytes(0x40))
            obj = h.alloc(0x10, bytes(0x10))
            h.uc.mem_write(obj, _dword(vt))
            h.uc.mem_write(vt + 0x2C, _dword(_lock_stub(h, self.seq, self.lock_log, self.lock_cnt, dataobjs)))
            h.uc.mem_write(vt + 0x30, _dword(_unlock_stub(h, self.seq, self.unlock_log, self.unlock_cnt)))
            self.buffers.append(obj)
        objs = h.alloc(0x40, bytes(0x40))
        for i in range(self.nbuf):
            h.uc.mem_write(objs + i * 4, _dword(self.buffers[i]))

        device = h.alloc(0x10, bytes(0x10))
        dev_vt = h.alloc(0x80, bytes(0x80))
        h.uc.mem_write(device, _dword(dev_vt))
        create = _create_stub(h, self.seq, self.create_log, self.create_cnt, objs)
        h.uc.mem_write(dev_vt + 0x6C, _dword(create))
        h.uc.mem_write(dev_vt + 0x68, _dword(create))
        self.device = device
        _patch(h, DEV_GLOBAL, _dword(device))
        _thunk_to(h, CHECK, _check_stub(h, self.seq, self.check_log, self.check_cnt))
        _thunk_to(h, READ, _read_stub(h, self.seq, self.read_cnt, self.read_log, self.script, self.cursor))
        self.heap_after = h.heap_ptr

    def expect(self, flags):
        """the tag sequence and read sizes of one call, in order"""
        tags, sizes = [TAG_READ], [4]
        for n in self.counts:
            tags.append(TAG_READ)
            sizes.append(4)
            if not n:
                continue
            if flags & 2:
                tags.append(TAG_READ)
                sizes.append(n * 6)
            if flags & 1:
                tags += [TAG_CREATE, TAG_CHECK, TAG_LOCK]
                if not flags & 2:
                    tags.append(TAG_READ)
                    sizes.append(n * 6)
                tags.append(TAG_UNLOCK)
        tags.append(TAG_READ)
        sizes.append(4)
        if self.vcount:
            if flags & 2:
                tags.append(TAG_READ)
                sizes.append(self.vcount * 0x20)
            if flags & 1:
                tags += [TAG_CREATE, TAG_CHECK, TAG_LOCK]
                if not flags & 2:
                    tags.append(TAG_READ)
                    sizes.append(self.vcount * 0x20)
                tags.append(TAG_UNLOCK)
        return tags, sizes


def _run(h, scene, flags):
    tags, sizes = scene.expect(flags)
    diffs = h.compare(FN, args=[scene.stream, UNUSED, flags],
                      regs={UC_X86_REG_ECX: scene.this, UC_X86_REG_EAX: IN_EAX}, ret=None)
    if diffs:
        return diffs
    h.heap_ptr = scene.heap_after
    result = h.call(FN, args=[scene.stream, UNUSED, flags],
                    regs={UC_X86_REG_ECX: scene.this, UC_X86_REG_EAX: IN_EAX})
    if result['fault']:
        return [result['fault']]

    problems = []
    got = [_u32(h, scene.seq + 4 + i * 4) for i in range(_u32(h, scene.seq))]
    if got != tags:
        return ['calls %r' % got]
    if result['esp'] != 0x10:
        problems.append('esp delta %#x' % result['esp'])
    got_sizes = [_u32(h, scene.read_log + i * 8 + 4) for i in range(_u32(h, scene.read_cnt))]
    if got_sizes != sizes:
        problems.append('read sizes %r' % got_sizes)
    if any(_u32(h, scene.read_log + i * 8) != scene.stream for i in range(_u32(h, scene.read_cnt))):
        problems.append('read streams differ')

    subs = _u32(h, scene.this + 8)
    if _u32(h, scene.this + 0xC) != len(scene.counts):
        problems.append('subset count %d' % _u32(h, scene.this + 0xC))
    buf_of_sub = {}
    for i, n in enumerate(scene.counts):
        e = subs + i * 0x10
        if _u32(h, e) != n:
            problems.append('subset %d count %d' % (i, _u32(h, e)))
        if not n:
            continue
        if _u32(h, e + 0xC) != scene.sub_offsets[i]:
            problems.append('subset %d offset %#x' % (i, _u32(h, e + 0xC)))
        data = _u32(h, e + 4)
        if flags & 2:
            if not data or bytes(h.uc.mem_read(data, n * 6)) != scene.sub_data[i]:
                problems.append('subset %d data' % i)
        elif data:
            problems.append('subset %d keeps data %#x' % (i, data))
        buf = _u32(h, e + 8)
        buf_of_sub[i] = buf
        if flags & 1:
            if buf != scene.buffers[scene.nz.index(i)]:
                problems.append('subset %d buffer %#x' % (i, buf))
        elif buf:
            problems.append('subset %d keeps buffer %#x' % (i, buf))

    if scene.counts:
        first = [_u32(h, scene.this + 0x10), _u32(h, scene.this + 0x14), _u32(h, scene.this + 0x18),
                 _u32(h, scene.this + 0x1C), _u32(h, scene.this + 0x20)]
        want = [_u32(h, subs), _u32(h, subs), _u32(h, subs + 4), _u32(h, subs + 8), _u32(h, subs + 0xC)]
        if first != want:
            problems.append('first copy %r' % first)

    if _u32(h, scene.this + 0x24) != scene.vcount:
        problems.append('vertex count %d' % _u32(h, scene.this + 0x24))
    if scene.vcount:
        if _u32(h, scene.this + 0x30) != scene.vtx_offset:
            problems.append('vertex offset %#x' % _u32(h, scene.this + 0x30))
        data = _u32(h, scene.this + 0x28)
        if flags & 2:
            if not data or bytes(h.uc.mem_read(data, scene.vcount * 0x20)) != scene.vtx_data:
                problems.append('vertex data')
        elif data:
            problems.append('vertex keeps data %#x' % data)
        buf = _u32(h, scene.this + 0x2C)
        if flags & 1:
            if buf != scene.buffers[scene.nsub]:
                problems.append('vertex buffer %#x' % buf)
        elif buf:
            problems.append('vertex keeps buffer %#x' % buf)

    # each locked buffer received its data (copy from the CPU array or straight from the stream)
    for i in range(scene.nbuf):
        if i < scene.nsub:
            sub = scene.nz[i]
            want, size = scene.sub_data[sub], scene.counts[sub] * 6
        else:
            want, size = scene.vtx_data, scene.vcount * 0x20
        if flags & 1:
            if bytes(h.uc.mem_read(scene.buffer_data[i], size)) != want:
                problems.append('buffer %d not filled' % i)
        elif bytes(h.uc.mem_read(scene.buffer_data[i], size)) != b'\xCC' * size:
            problems.append('buffer %d written' % i)

    for i in range(_u32(h, scene.create_cnt)):
        e = scene.create_log + i * 0x20
        if i < scene.nsub:
            sub = scene.nz[i]
            want = (scene.device, scene.counts[sub] * 6, USAGE, FMT_INDEX, 0, subs + sub * 0x10 + 8, 0)
        else:
            want = (scene.device, scene.vcount * 0x20, USAGE, FMT_VERTEX, 0, scene.this + 0x2C, 0)
        got_args = tuple(_u32(h, e + 4 * q) for q in range(7))
        if got_args != want:
            problems.append('create %d %r' % (i, got_args))
    for i in range(_u32(h, scene.check_cnt)):
        e = scene.check_log + i * 0xC
        line = 0x61 if i < scene.nsub else 0x89
        if (_u32(h, e), _u32(h, e + 4), _u32(h, e + 8)) != (0, MESH_CPP, line):
            problems.append('check %d %r' % (i, [_u32(h, e + 4 * q) for q in range(3)]))
    if _u32(h, scene.lock_cnt) != (scene.nbuf if flags & 1 else 0):
        problems.append('lock count %d' % _u32(h, scene.lock_cnt))
    for i in range(_u32(h, scene.lock_cnt)):
        e = scene.lock_log + i * 0x10
        size = (scene.vtx_data and scene.vcount * 0x20) if i >= scene.nsub else \
            scene.counts[scene.nz[i]] * 6
        if (_u32(h, e), _u32(h, e + 4), _u32(h, e + 8), _u32(h, e + 0xC)) != (scene.buffers[i], 0, size, 0):
            problems.append('lock %d %r' % (i, [_u32(h, e + 4 * q) for q in range(4)]))
    for i in range(_u32(h, scene.unlock_cnt)):
        if _u32(h, scene.unlock_log + i * 4) != scene.buffers[i]:
            problems.append('unlock %d %#x' % (i, _u32(h, scene.unlock_log + i * 4)))
    return problems


def _case(h, counts, vcount, flags):
    heap0 = h.heap_ptr
    try:
        scene = Scene(h, counts, vcount)
        return _run(h, scene, flags) or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_cpu_and_gpu(h):
    """flags 3: both index subsets and the vertices get CPU copies and device buffers"""
    return _case(h, [3, 5], 2, 3)


def test_gpu_only(h):
    """flags 1: no CPU arrays, the buffers are filled straight from the stream"""
    return _case(h, [4], 3, 1)


def test_cpu_only(h):
    """flags 2: only the arrays are read, the device is never touched"""
    return _case(h, [2, 0], 1, 2)


def test_no_vertices(h):
    """a zero vertex count ends the load after the subsets"""
    return _case(h, [6], 0, 3)
