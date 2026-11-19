"""0x4CF960 (CSurfacePlane buffer setup): the previous vertex and index buffers are released, then a
vertex buffer (20 bytes per vertex, FVF 0x102) and a 16-bit index buffer (6 * (vertices / 3) bytes)
are created on the global D3D device and filled through lock/unlock.  The device and the buffer
vtables are stubbed; the global d_006C8C10 is patched."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

SETUP = 0x004CF960
DEV_GLOBAL = 0x006C8C10

saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _tag(seq, tag):
    """appends tag to the sequence at seq (count at +0, entries from +4)"""
    return (b'\xA1' + _dword(seq) +                                   # mov eax,[seq]
            b'\xFF\x05' + _dword(seq) +                               # inc dword [seq]
            b'\xC7\x04\x85' + _dword(seq + 4) + _dword(tag))          # mov dword [seq+4+eax*4],tag


def _create_stub(h, seq, tag, log, obj):
    """vf0x68/vf0x6C(dev, len, usage, fmt, pool, &out, h): logs the arguments, hands out obj, returns 0"""
    code = _tag(seq, tag)
    code += b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)               # mov eax,[esp+4]; mov [log],eax
    code += b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4)           # mov eax,[esp+8]; mov [log+4],eax
    code += b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + 8)           # mov eax,[esp+0xC]; mov [log+8],eax
    code += b'\x8B\x44\x24\x10' + b'\xA3' + _dword(log + 0xC)         # mov eax,[esp+0x10]; mov [log+0xC],eax
    code += b'\x8B\x44\x24\x14' + b'\xA3' + _dword(log + 0x10)        # mov eax,[esp+0x14]; mov [log+0x10],eax
    code += b'\x8B\x44\x24\x1C' + b'\xA3' + _dword(log + 0x14)        # mov eax,[esp+0x1C]; mov [log+0x14],eax
    code += b'\x8B\x44\x24\x18' + b'\xC7\x00' + _dword(obj)           # mov eax,[esp+0x18]; mov dword [eax],obj
    code += b'\x33\xC0' + b'\xC2\x1C\x00'                             # xor eax,eax; ret 0x1C
    return _stub(h, code)


def _lock_stub(h, seq, tag, log, data):
    """vf0x2C(self, off, size, &data, flags): logs the arguments and hands out data"""
    code = _tag(seq, tag)
    code += b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)               # self
    code += b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + 4)           # off
    code += b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + 8)           # size
    code += b'\x8B\x44\x24\x14' + b'\xA3' + _dword(log + 0xC)         # flags
    code += b'\x8B\x44\x24\x10' + b'\xC7\x00' + _dword(data)          # mov eax,[esp+0x10]; mov dword [eax],data
    code += b'\x33\xC0' + b'\xC2\x14\x00'                             # xor eax,eax; ret 0x14
    return _stub(h, code)


def _com_stub(h, seq, tag, log):
    """vf0x30/vf0x8(self): logs self, returns 0"""
    code = _tag(seq, tag)
    code += b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log)               # mov eax,[esp+4]; mov [log],eax
    code += b'\x33\xC0' + b'\xC2\x04\x00'                             # xor eax,eax; ret 4
    return _stub(h, code)


def _release_stub(h, seq, log):
    """vf0x8(self): appends self to the release list (count at +0)"""
    code = _tag(seq, 1)
    code += (b'\x8B\x15' + _dword(log) +                              # mov edx,[log]
             b'\xFF\x05' + _dword(log) +                              # inc dword [log]
             b'\x8B\x4C\x24\x04' + b'\x89\x0C\x95' + _dword(log + 4) +  # mov ecx,[esp+4]; mov [edx*4+log+4],ecx
             b'\x33\xC0' + b'\xC2\x04\x00')                           # xor eax,eax; ret 4
    return _stub(h, code)


def _check(h, count, with_old):
    heap0 = h.heap_ptr
    seq = h.alloc(0x40, bytes(0x40))
    logs = h.alloc(0x100, bytes(0x100))
    rel = h.alloc(0x10, bytes(0x10))
    # logs: vb create 0x00, ib create 0x20, lock vb 0x40, unlock vb 0x60, lock ib 0x70, unlock ib 0x80
    buf_vb = h.alloc(0x200, b'\xCC' * 0x200)
    buf_ib = h.alloc(0x100, b'\xCC' * 0x100)
    try:
        device = h.alloc(0x10, bytes(0x10))
        devvt = h.alloc(0x80, bytes(0x80))
        h.uc.mem_write(device, _dword(devvt))
        vb = h.alloc(0x10, bytes(0x10))
        ib = h.alloc(0x10, bytes(0x10))
        vt_vb = h.alloc(0x40, bytes(0x40))
        vt_ib = h.alloc(0x40, bytes(0x40))
        vt_old = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(devvt + 0x68, _dword(_create_stub(h, seq, 3, logs, vb)))
        h.uc.mem_write(devvt + 0x6C, _dword(_create_stub(h, seq, 6, logs + 0x20, ib)))
        h.uc.mem_write(vt_vb + 0x2c, _dword(_lock_stub(h, seq, 4, logs + 0x40, buf_vb)))
        h.uc.mem_write(vt_vb + 0x30, _dword(_com_stub(h, seq, 5, logs + 0x60)))
        h.uc.mem_write(vt_ib + 0x2c, _dword(_lock_stub(h, seq, 7, logs + 0x70, buf_ib)))
        h.uc.mem_write(vt_ib + 0x30, _dword(_com_stub(h, seq, 8, logs + 0x80)))
        h.uc.mem_write(vt_old + 0x8, _dword(_release_stub(h, seq, rel)))
        h.uc.mem_write(vb, _dword(vt_vb))
        h.uc.mem_write(ib, _dword(vt_ib))
        old_vb = h.alloc(0x10, bytes(0x10))
        old_ib = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(old_vb, _dword(vt_old))
        h.uc.mem_write(old_ib, _dword(vt_old))

        vdata = h.alloc(0x200, bytes(range(0x100)) * 2)
        idata = h.alloc(0x40, bytes(range(0x40)))
        obj = h.alloc(0x90, bytes(0x90))
        h.uc.mem_write(obj + 0x70, _dword(old_vb if with_old else 0))
        h.uc.mem_write(obj + 0x74, _dword(old_ib if with_old else 0))
        h.uc.mem_write(obj + 0x78, _dword(vdata))
        h.uc.mem_write(obj + 0x7c, _dword(idata))
        h.uc.mem_write(obj + 0x80, _dword(count))
        _patch(h, DEV_GLOBAL, _dword(device))

        diffs = h.compare(SETUP, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return ['count %d old %d: %s' % (count, with_old, d) for d in diffs]

        h.uc.mem_write(seq, bytes(0x40))
        h.uc.mem_write(logs, bytes(0x100))
        h.uc.mem_write(rel, bytes(0x10))
        h.uc.mem_write(buf_vb, b'\xCC' * 0x200)
        h.uc.mem_write(buf_ib, b'\xCC' * 0x100)
        result = h.call(SETUP, regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return ['count %d old %d: %s' % (count, with_old, result['fault'])]

        problems = []
        tags = [_u32(h, seq + 4 + i * 4) for i in range(_u32(h, seq))]
        want = ([1, 1] if with_old else []) + [3, 4, 5, 6, 7, 8]
        if tags != want:
            problems.append('count %d old %d: calls %r' % (count, with_old, tags))
        if with_old:
            if _u32(h, rel) != 2 or (_u32(h, rel + 4), _u32(h, rel + 8)) != (old_vb, old_ib):
                problems.append('count %d old %d: released %r'
                                % (count, with_old, [_u32(h, rel + 4 * i) for i in range(3)]))
        if _u32(h, logs) != device or _u32(h, logs + 4) != count * 20 or _u32(h, logs + 8) != 8 or \
                _u32(h, logs + 0xC) != 0x102 or _u32(h, logs + 0x10) != 1 or _u32(h, logs + 0x14) != 0:
            problems.append('count %d old %d: vertex create %r' % (count, with_old,
                            [_u32(h, logs + 4 * i) for i in range(6)]))
        if _u32(h, logs + 0x20) != device or _u32(h, logs + 0x24) != (count // 3) * 6 or \
                _u32(h, logs + 0x28) != 8 or _u32(h, logs + 0x2C) != 0x65 or _u32(h, logs + 0x30) != 1 or \
                _u32(h, logs + 0x34) != 0:
            problems.append('count %d old %d: index create %r' % (count, with_old,
                            [_u32(h, logs + 0x20 + 4 * i) for i in range(6)]))
        if (_u32(h, logs + 0x40), _u32(h, logs + 0x44), _u32(h, logs + 0x48), _u32(h, logs + 0x4C)) != (vb, 0, 0, 0):
            problems.append('count %d old %d: vertex lock %r' % (count, with_old,
                            [_u32(h, logs + 0x40 + 4 * i) for i in range(4)]))
        if _u32(h, logs + 0x60) != vb:
            problems.append('count %d old %d: vertex unlock %#x' % (count, with_old, _u32(h, logs + 0x60)))
        if (_u32(h, logs + 0x70), _u32(h, logs + 0x74), _u32(h, logs + 0x78), _u32(h, logs + 0x7C)) != (ib, 0, 0, 0):
            problems.append('count %d old %d: index lock %r' % (count, with_old,
                            [_u32(h, logs + 0x70 + 4 * i) for i in range(4)]))
        if _u32(h, logs + 0x80) != ib:
            problems.append('count %d old %d: index unlock %#x' % (count, with_old, _u32(h, logs + 0x80)))
        want_v = bytes(h.uc.mem_read(vdata, count * 20))
        if bytes(h.uc.mem_read(buf_vb, count * 20)) != want_v:
            problems.append('count %d old %d: the vertices were not copied' % (count, with_old))
        if bytes(h.uc.mem_read(buf_vb + count * 20, 1)) != b'\xCC':
            problems.append('count %d old %d: the vertex buffer was overrun' % (count, with_old))
        want_i = bytes(h.uc.mem_read(idata, count * 2))
        if bytes(h.uc.mem_read(buf_ib, count * 2)) != want_i:
            problems.append('count %d old %d: the indices were not copied' % (count, with_old))
        if bytes(h.uc.mem_read(buf_ib + count * 2, 1)) != b'\xCC':
            problems.append('count %d old %d: the index buffer was overrun' % (count, with_old))
        if _u32(h, obj + 0x70) != vb or _u32(h, obj + 0x74) != ib:
            problems.append('count %d old %d: the buffers are %#x, %#x'
                            % (count, with_old, _u32(h, obj + 0x70), _u32(h, obj + 0x74)))
        return problems
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_buffers_created_and_filled(h):
    return _check(h, 12, False) or None


def test_buffers_replaced(h):
    return _check(h, 9, True) or None


def test_vertex_count_not_multiple_of_three(h):
    """the index buffer keeps the original's 6 * (count / 3) size and 2 * count copy length"""
    return _check(h, 1, False) or None
