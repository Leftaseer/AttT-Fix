"""CMapHeight::Load (0x00473370): reads "<path>.nmph" through a CGameFile: the grid size and origin, one row of
depth unsigned shorts per x, then the scale and offset; the bounds follow from the cell size 5.0 and a missing
file leaves the object untouched.  CFileSystem::OpenFile (0x004514B0) and the file's vtable are stubs."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

OPEN_FILE = 0x004514B0
LIVE_READERS = 0x006C8DE0
FILE_SYSTEM = 0x006C8DE4

WIDTH, DEPTH, ORIGIN_X, ORIGIN_Z = 3, 2, -10, 20
SAMPLES = (1, 2, 3, 4, 5, 6)
SCALE, OFFSET = 2.5, -100.0
BLOB = (struct.pack('<iiii', WIDTH, DEPTH, ORIGIN_X, ORIGIN_Z)
        + struct.pack('<%dH' % len(SAMPLES), *SAMPLES)
        + struct.pack('<ff', SCALE, OFFSET))


def _redirect(h, entry, body):
    saved = bytes(h.uc.mem_read(entry, 6))
    h.uc.mem_write(entry, b'\xe9' + struct.pack('<i', body - (entry + 5)))
    h.uc.ctl_remove_cache(entry, entry + 8)
    return saved


def _entry_impl(h, entry):
    """the rebuilt entry is a jump to the compiled function, which new code calls directly"""
    code = bytes(h.uc.mem_read(entry, 5))
    if code[0] != 0xE9:
        raise AssertionError('%08X is not a jump' % entry)
    return entry + 5 + struct.unpack('<i', code[1:5])[0]


def _body(h, code):
    area = h.alloc(len(code) + 4, bytes(len(code) + 4))
    h.uc.mem_write(area, code)
    return area


def _sso(h, text):
    data = text.encode()
    buf = data + b'\0' + bytes(16 - len(data) - 1)
    return h.alloc(28, bytes(4) + buf + struct.pack('<II', len(data), 15))


def _sequential_reader(h):
    """FsFile::Read: copies the requested count from the file image at a running offset"""
    blob = h.alloc(len(BLOB), BLOB)
    pos = h.alloc(4, bytes(4))
    code = (b'\x56\x57'                                    # push esi, edi
            + b'\x8b\x7c\x24\x0c'                          # mov edi, [esp+0xC]   buffer
            + b'\x8b\x4c\x24\x10'                          # mov ecx, [esp+0x10]  count
            + b'\xa1' + struct.pack('<I', pos)             # mov eax, [pos]
            + b'\x8d\x15' + struct.pack('<I', blob)        # lea edx, [blob]
            + b'\x01\xc2'                                  # add edx, eax
            + b'\x01\xc8'                                  # add eax, ecx
            + b'\xa3' + struct.pack('<I', pos)             # mov [pos], eax
            + b'\x89\xd6'                                  # mov esi, edx
            + b'\xf3\xa4'                                  # rep movsb
            + b'\x5f\x5e\xc2\x08\x00')                     # pop edi, pop esi, ret 8
    return _body(h, code)


def _fake_file(h, read):
    dtor = _body(h, b'\x8b\x44\x24\x04\xc2\x04\x00')       # mov eax, [esp+4]; ret 4
    vtable = h.alloc(8, struct.pack('<II', dtor, read))
    return h.alloc(0xC, struct.pack('<III', vtable, 0, len(BLOB)))


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _float(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def test_map_height_load(h):
    read = _sequential_reader(h)
    file_ = _fake_file(h, read)
    opener = _body(h, b'\xb8' + struct.pack('<I', file_) + b'\xc2\x04\x00')  # mov eax, file; ret 4
    impl = _entry_impl(h, OPEN_FILE)
    saved = _redirect(h, impl, opener)
    saved_state = (bytes(h.uc.mem_read(LIVE_READERS, 8)))
    h.uc.mem_write(LIVE_READERS, struct.pack('<II', 1, 0x12345678))
    path = _sso(h, 'maps/test')
    try:
        obj = h.alloc(0x30, bytes(0x30))
        diffs = h.compare(0x00473370, args=[path, 0x1111], regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        res = h.call(0x00473370, args=[path, 0x1111], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        fields = struct.unpack('<6i', h.uc.mem_read(obj + 4, 24))
        rows, width, depth, origin_x, origin_z = fields[:5]
        if (width, depth, origin_x, origin_z) != (WIDTH, DEPTH, ORIGIN_X, ORIGIN_Z):
            return ['grid %r, want %r' % ((width, depth, origin_x, origin_z),
                                          (WIDTH, DEPTH, ORIGIN_X, ORIGIN_Z))]
        bounds = struct.unpack('<4f', h.uc.mem_read(obj + 0x18, 16))
        if bounds != (-10.0, 0.0, 20.0, 25.0):
            return ['bounds %r' % (bounds,)]
        if (_float(h, obj + 0x28), _float(h, obj + 0x2C)) != (SCALE, OFFSET):
            return ['scale/offset %r' % ((_float(h, obj + 0x28), _float(h, obj + 0x2C)),)]
        if not rows:
            return ['no rows']
        pointers = struct.unpack('<III', h.uc.mem_read(rows, 12))
        for i, pointer in enumerate(pointers):
            got = struct.unpack('<%dH' % DEPTH, h.uc.mem_read(pointer, DEPTH * 2))
            want = SAMPLES[i * DEPTH:(i + 1) * DEPTH]
            if got != want:
                return ['row %d is %r, want %r' % (i, got, want)]

        # a missing file makes CGameFile::Open raise 0xE0000002 before anything is read; the emulator stops at the
        # import, so the original cannot be compared here - only that the object is still untouched at that point
        h.uc.mem_write(impl, b'\x33\xc0\xc2\x04\x00')       # xor eax, eax; ret 4
        h.uc.ctl_remove_cache(impl, impl + 8)
        obj = h.alloc(0x30, b'\xa5' * 0x30)
        res = h.call(0x00473370, args=[path, 0], regs={UC_X86_REG_ECX: obj})
        if 'RaiseException' not in (res['fault'] or ''):
            return ['missing: %s' % (res['fault'] or 'returned without raising')]
        if h.uc.mem_read(obj, 0x30) != b'\xa5' * 0x30:
            return ['missing: the object was changed']
        return []
    finally:
        h.uc.mem_write(impl, saved)
        h.uc.ctl_remove_cache(impl, impl + 8)
        h.uc.mem_write(LIVE_READERS, saved_state)
