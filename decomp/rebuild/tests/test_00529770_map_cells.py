"""Differential test for 0x00529770 (world map cell geometry and hover update).

Every callee and both vtable groups (the map's double-buffered vertex copy and the mesh vertex buffer) are
replaced by stubs that log their arguments, so the refresh block, the three cell passes, the copied item order
and the accumulator fields are all checked."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00529770
ACTIVE_TEST = 0x004D9A40
ROW_COPY = 0x00529520
CELL_TEST = 0x00528A40
CAMERA = 0x00424E70

TAG_ACTIVE = 1
TAG_LOCK1 = 2
TAG_UNLOCK1 = 3
TAG_COPY = 4
TAG_CELL = 5
TAG_LOCK2 = 6
TAG_UNLOCK2 = 7

COUNT = {(0, 0): 2, (0, 1): 1, (0, 2): 0,
         (1, 0): 3, (1, 1): 3, (1, 2): 1,
         (2, 0): 2, (2, 1): 0, (2, 2): 1}
VISIBLE = [1, 1, 1, 0, 1, 1, 1, 1, 1]          # (1, 0) is hidden
CAM_X = 25.0
CAM_Y = 65.0
ORIGIN_X = 5.0
ORIGIN_Y = 85.0
CELL_W = 10.0
CELL_H = 20.0

saved = {}


def _u(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _f(value):
    return struct.pack('<f', value)


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


def _arg(dst_reg, disp):
    """mov dst_reg, [esp+disp] (dst_reg: 1=ecx, 2=edx)"""
    return bytes([0x8B, 0x44 | (dst_reg << 3), 0x24, disp])


def _entries(h, log, cnt, width):
    n = _u32(h, cnt)
    data = h.uc.mem_read(log, width * 4 * n)
    return [struct.unpack('<%dI' % width, data[i * width * 4:(i + 1) * width * 4]) for i in range(n)]


class Scene:
    def __init__(self, h):
        self.h = h
        self.seq = h.alloc(4 + 4 * 200, bytes(4 + 4 * 200))
        self.cnt = {name: h.alloc(4, bytes(4)) for name in
                    ('active', 'lock1', 'unlock1', 'copy', 'cell', 'lock2', 'unlock2')}
        self.l_active = h.alloc(64 * 8, bytes(64 * 8))
        self.l_lock1 = h.alloc(8 * 16, bytes(8 * 16))
        self.l_unlock1 = h.alloc(8 * 4, bytes(8 * 4))
        self.l_copy = h.alloc(8 * 8, bytes(8 * 8))
        self.l_cell = h.alloc(64 * 12, bytes(64 * 12))
        self.l_lock2 = h.alloc(8 * 16, bytes(8 * 16))
        self.l_unlock2 = h.alloc(8 * 4, bytes(8 * 4))
        self.flag = h.alloc(4, bytes(4))
        self.this = h.alloc(0x400, bytes(0x400))
        self.active = h.alloc(0x100, bytes(0x100))
        self.cam = h.alloc(0x80, bytes(0x80))
        self.map = h.alloc(0x20, bytes(0x20))
        self.obj = h.alloc(0x80, bytes(0x80))
        self.buf1 = h.alloc(0x20, bytes(0x20))
        self.buf2 = h.alloc(0x20, bytes(0x20))
        self.vb = h.alloc(0x20, bytes(0x20))
        self.vtbuf = h.alloc(0x40, bytes(0x40))
        self.vtvb = h.alloc(0x40, bytes(0x40))
        self.records = h.alloc(0x60, bytes(0x60))
        self.rows = h.alloc(0x30, bytes(0x30))
        self.cells = h.alloc(0x90, bytes(0x90))
        self.items = h.alloc(0x200, bytes(0x200))
        self.visible = h.alloc(9, bytes(9))
        self.data1 = h.alloc(0x100, bytes(0x100))
        self.data2 = h.alloc(0x400, bytes(0x400))
        self._install()

    def item_off(self, row, col):
        off = 0
        for r in range(3):
            for c in range(3):
                if (r, c) == (row, col):
                    return off
                off += 6 * COUNT[(r, c)]
        raise KeyError(row)

    def item_bytes(self, row, col):
        idx = row * 3 + col
        return bytes((idx * 0x10 + k) & 0xFF for k in range(6 * COUNT[(row, col)]))

    def reset(self, active, current, camx=CAM_X, camy=CAM_Y):
        h = self.h
        h.uc.mem_write(self.seq, bytes(4 + 4 * 200))
        for c in self.cnt.values():
            h.uc.mem_write(c, b'\0' * 4)
        for block, size in ((self.this, 0x400), (self.active, 0x100), (self.cam, 0x80), (self.map, 0x20),
                            (self.obj, 0x80), (self.records, 0x60), (self.rows, 0x30), (self.cells, 0x90),
                            (self.items, 0x200), (self.data1, 0x100), (self.data2, 0x400)):
            h.uc.mem_write(block, bytes(size))
        h.uc.mem_write(self.flag, _u(active))
        h.uc.mem_write(self.this + 0x1e4, _u(self.active))
        h.uc.mem_write(self.this + 0x208, _u(self.buf1))
        h.uc.mem_write(self.this + 0x20c, _u(self.buf2))
        h.uc.mem_write(self.this + 0x210, _u(0 if current == 2 else (self.buf1 if current == 0 else self.buf2)))
        h.uc.mem_write(self.this + 0x214, _u(self.vb))
        h.uc.mem_write(self.this + 0x218, _u(self.map))
        h.uc.mem_write(self.map + 8, _u(self.obj))
        h.uc.mem_write(self.this + 0x1ec, _u(self.records))
        h.uc.mem_write(self.this + 0x1f0, _u(self.records + 0x60))
        h.uc.mem_write(self.this + 0x1c8, _u(0xDEAD))
        h.uc.mem_write(self.this + 0x1cc, _u(0xDEAD))
        h.uc.mem_write(self.this + 0x1d0, _u(0xDEAD))
        h.uc.mem_write(self.this + 0x2c8, _u(self.rows))
        h.uc.mem_write(self.this + 0x2cc, _u(self.rows + 0x30))
        h.uc.mem_write(self.cam + 0x44, _f(camx))
        h.uc.mem_write(self.cam + 0x4c, _f(camy))
        h.uc.mem_write(self.obj + 0x5c, _f(CELL_W))
        h.uc.mem_write(self.obj + 0x60, _f(CELL_H))
        h.uc.mem_write(self.obj + 0x70, _f(ORIGIN_X))
        h.uc.mem_write(self.obj + 0x78, _f(ORIGIN_Y))
        h.uc.mem_write(self.records, bytes((0xA0 + k) & 0xFF for k in range(0x60)))
        h.uc.mem_write(self.visible, bytes(VISIBLE))
        for r in range(3):
            h.uc.mem_write(self.rows + r * 0x10,
                           _u(0) + _u(self.cells + r * 0x30) + _u(self.cells + r * 0x30 + 0x30) + _u(0))
        for r in range(3):
            for c in range(3):
                idx, n = r * 3 + c, COUNT[(r, c)]
                base = self.items + self.item_off(r, c)
                h.uc.mem_write(self.cells + idx * 0x10, _u(0) + _u(base) + _u(base + 6 * n) + _u(0))
                h.uc.mem_write(base, self.item_bytes(r, c))
        h.uc.mem_write(self.buf1, _u(self.vtbuf))
        h.uc.mem_write(self.buf2, _u(self.vtbuf))
        h.uc.mem_write(self.vb, _u(self.vtvb))

    def x(self, camx=CAM_X):
        return int((camx - ORIGIN_X) / CELL_W)

    def y(self, camy=CAM_Y):
        return int((ORIGIN_Y - camy) / CELL_H)

    def expected(self, camx=CAM_X, camy=CAM_Y):
        """(band cells, outer cells) in walk order"""
        x, y = self.x(camx), self.y(camy)
        band, outer = [], []
        for r in range(3):
            for c in range(3):
                if not VISIBLE[r * 3 + c]:
                    continue
                adx = abs(r - x)
                ady = abs(c - y)
                if adx <= 1 and ady <= 1:
                    band.append((r, c))
                if adx > 1 or ady > 1:
                    outer.append((r, c))
        return band, outer

    def _install(self):
        h = self.h
        self.stub_cam = _stub(h, b'\xB8' + _u(self.cam) + b'\xC3')
        _hook(h, CAMERA, self.stub_cam)

        # 0x004D9A40 (ECX = active object, ret 0): logs the object and returns the flag
        code = _tag(self.seq, TAG_ACTIVE) + _next(self.cnt['active']) + _base(self.l_active, 0x08)
        code += _store(0, 1) + b'\x8B\x0D' + _u(self.flag) + _store(4, 1) + b'\xA1' + _u(self.flag) + b'\xC3'
        _hook(h, ACTIVE_TEST, _stub(h, code))

        # 0x00529520 (ECX = this+0x2C4, [esp+4] = source vector, ret 4)
        code = _tag(self.seq, TAG_COPY) + _next(self.cnt['copy']) + _base(self.l_copy, 0x08)
        code += _store(0, 1) + _arg(1, 0x04) + _store(4, 1) + b'\xC2\x04\x00'
        _hook(h, ROW_COPY, _stub(h, code))

        # 0x00528A40 (ECX = map object, [esp+4] = row, [esp+8] = col, ret 8): logs and returns VISIBLE
        code = _tag(self.seq, TAG_CELL) + _next(self.cnt['cell']) + _base(self.l_cell, 0x0C)
        code += _store(0, 1) + _arg(1, 0x04) + _store(4, 1) + _arg(1, 0x08) + _store(8, 1)
        code += b'\x33\xC0' + _arg(1, 0x04) + b'\x8D\x0C\x49' + b'\x03\x4C\x24\x08'
        code += b'\xBA' + _u(self.visible) + b'\x8A\x04\x0A' + b'\xC2\x08\x00'
        _hook(h, CELL_TEST, _stub(h, code))

        # vtable +0x2C / +0x30 (stdcall): lock(buf, off, len, &data, flags) / unlock(buf)
        def lock_code(tag, counter, log, data):
            c = _tag(self.seq, tag) + _next(counter) + _base(log, 0x10)
            c += _arg(1, 0x04) + _store(0, 1) + _arg(1, 0x08) + _store(4, 1)
            c += _arg(1, 0x0C) + _store(8, 1) + _arg(1, 0x10) + b'\xBA' + _u(data) + b'\x89\x11'
            c += _arg(1, 0x14) + _store(0x0C, 1) + b'\x33\xC0' + b'\xC2\x14\x00'
            return c

        def unlock_code(tag, counter, log):
            c = _tag(self.seq, tag) + _next(counter) + _base(log, 0x04)
            c += _arg(1, 0x04) + _store(0, 1) + b'\xC2\x04\x00'
            return c

        lock1 = _stub(h, lock_code(TAG_LOCK1, self.cnt['lock1'], self.l_lock1, self.data1))
        unlock1 = _stub(h, unlock_code(TAG_UNLOCK1, self.cnt['unlock1'], self.l_unlock1))
        lock2 = _stub(h, lock_code(TAG_LOCK2, self.cnt['lock2'], self.l_lock2, self.data2))
        unlock2 = _stub(h, unlock_code(TAG_UNLOCK2, self.cnt['unlock2'], self.l_unlock2))
        h.uc.mem_write(self.vtbuf + 0x2c, _u(lock1) + _u(unlock1))
        h.uc.mem_write(self.vtvb + 0x2c, _u(lock2) + _u(unlock2))

    def tags(self):
        n = _u32(self.h, self.seq)
        return list(struct.unpack('<%dI' % n, self.h.uc.mem_read(self.seq + 4, 4 * n)))


def _run(h, scene):
    diffs = h.compare(FN, regs={UC_X86_REG_ECX: scene.this}, ret=None)
    if diffs:
        return diffs
    res = h.call(FN, regs={UC_X86_REG_ECX: scene.this})
    if res['fault']:
        return ['the replacement faulted: %s' % res['fault']]
    return None


def _check(h, scene, active, current, camx=CAM_X, camy=CAM_Y):
    scene.reset(active, current, camx, camy)
    diffs = _run(h, scene)
    if diffs:
        return diffs
    band, outer = scene.expected(camx, camy)
    tags = [TAG_ACTIVE]
    if active:
        tags += [TAG_LOCK1, TAG_UNLOCK1, TAG_COPY]
    tags += [TAG_CELL] * 9 + [TAG_LOCK2] + [TAG_CELL] * 18 + [TAG_UNLOCK2]
    if scene.tags() != tags:
        return ['active %d: the call order is %s, expected %s' % (active, scene.tags(), tags)]
    act = _entries(h, scene.l_active, scene.cnt['active'], 2)
    if act != [(scene.active, 1 if active else 0)]:
        return ['active %d: the activity test is %s' % (active, act)]
    if active:
        chosen = scene.buf2 if current == 0 else scene.buf1
        lock = _entries(h, scene.l_lock1, scene.cnt['lock1'], 4)
        if lock != [(chosen, 0, 0, 0x2000)]:
            return ['active: the refresh lock is %s' % (lock,)]
        if _entries(h, scene.l_unlock1, scene.cnt['unlock1'], 1) != [(chosen,)]:
            return ['active: the refresh buffer was not unlocked']
        copy = _entries(h, scene.l_copy, scene.cnt['copy'], 2)
        if copy != [(scene.this + 0x2C4, scene.active + 0x50)]:
            return ['active: the row copy is %s' % (copy,)]
        if _u32(h, scene.this + 0x1C8) != 3:
            return ['active: the record count is %08X' % _u32(h, scene.this + 0x1C8)]
        if h.uc.mem_read(scene.data1, 0x60) != h.uc.mem_read(scene.records, 0x60):
            return ['active: the records were not copied']
        if _u32(h, scene.this + 0x210) != chosen:
            return ['active: the current buffer is %08X' % _u32(h, scene.this + 0x210)]
    else:
        if _u32(h, scene.this + 0x1C8) != 0xDEAD:
            return ['inactive: the record count changed']
    lock = _entries(h, scene.l_lock2, scene.cnt['lock2'], 4)
    if lock != [(scene.vb, 0, 6 * sum(COUNT[c] for c in [(r, b) for r in range(3) for b in range(3)
                                                        if VISIBLE[r * 3 + b]]), 0x2000)]:
        return ['the mesh lock is %s' % (lock,)]
    cells = _entries(h, scene.l_cell, scene.cnt['cell'], 3)
    want = [(scene.obj, r, c) for _ in range(3) for r in range(3) for c in range(3)]
    if cells != want:
        return ['the cell tests are %s' % (cells,)]
    expected = b''.join(scene.item_bytes(r, c) for r, c in band + outer)
    if h.uc.mem_read(scene.data2, len(expected)) != expected:
        return ['the copied items differ: %s' % h.uc.mem_read(scene.data2, len(expected)).hex()]
    if h.uc.mem_read(scene.data2 + len(expected), 0x20) != bytes(0x20):
        return ['the copy overran: %s' % h.uc.mem_read(scene.data2 + len(expected), 0x20).hex()]
    if _u32(h, scene.this + 0x1D0) != sum(COUNT[c] for c in band):
        return ['the hover total is %d' % _u32(h, scene.this + 0x1D0)]
    if _u32(h, scene.this + 0x1CC) != sum(COUNT[c] for c in band + outer):
        return ['the copied total is %d' % _u32(h, scene.this + 0x1CC)]
    if _entries(h, scene.l_unlock2, scene.cnt['unlock2'], 1) != [(scene.vb,)]:
        return ['the mesh buffer was not unlocked']
    return None


def test_00529770(h):
    heap0 = h.heap_ptr
    try:
        scene = Scene(h)
        result = _check(h, scene, 1, 0)
        if result:
            return ['active/copy buffer: %s' % d for d in result]
        result = _check(h, scene, 0, 2)
        if result:
            return ['inactive: %s' % d for d in result]
        result = _check(h, scene, 1, 2, CAM_X, 105.0)
        if result:
            return ['negative column: %s' % d for d in result]
        return None
    finally:
        _restore(h)
