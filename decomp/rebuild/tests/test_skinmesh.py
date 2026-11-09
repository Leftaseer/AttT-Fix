"""CSkinMesh: the destructor (0x4C06D0), the deleting destructor (0x4C07A0) and the loader (0x4C07C0), plus the
constructor that drives it (0x4C0A10).

Load reads through a CGameFile, so CFileSystem::OpenFile (0x4514B0) is redirected to a fake file whose read stub
serves a blob sequentially.  The blob holds empty sub-object lists (a non-empty one would run the original
0x4BD0F0 / 0x475720, which is not what these tests cover) and the 0x60-byte block.  The destructor's sub objects
are fake vtables pointing at a counting stub.
"""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

OPEN_FILE = 0x004514B0
LIVE_READERS = 0x006C8DE0
FILE_SYSTEM = 0x006C8DE4

SKINMESH_CTOR = 0x004C0A10
SKINMESH_DTOR = 0x004C06D0
DELETE_SKINMESH = 0x004C07A0
SKINMESH_LOAD = 0x004C07C0

SKINMESH_VFT = 0x00611290
NAME = b'alpha'
BLOCK = bytes((i * 7 + 3) & 0xFF for i in range(0x60))
BLOB = struct.pack('<ii', 0, 0) + BLOCK
BLOB_SIZE = 0x68


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


def _name_words(text):
    """the seven words of an MSVC 2005 std::string with the text inline (short-string form)"""
    inline = text + b'\0' + bytes(16 - len(text) - 1)
    return [0] + list(struct.unpack('<4I', inline)) + [len(text), 15]


def _sequential_reader(h):
    """FsFile::Read: copies the requested count from the blob at a running offset"""
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
    return _body(h, code), pos


def _fake_file(h, read):
    dtor = _body(h, b'\x8b\x44\x24\x04\xc2\x04\x00')       # mov eax, [esp+4]; ret 4
    vtable = h.alloc(8, struct.pack('<II', dtor, read))
    return h.alloc(0xC, struct.pack('<III', vtable, 0, len(BLOB)))


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _with_fake_file(h):
    """redirect OpenFile (restored by the caller) and mark the reader alive so the ctor keeps the file system"""
    read, pos = _sequential_reader(h)
    file_ = _fake_file(h, read)
    opener = _body(h, b'\xb8' + struct.pack('<I', file_) + b'\xc2\x04\x00')  # mov eax, file; ret 4
    impl = _entry_impl(h, OPEN_FILE)
    saved = _redirect(h, impl, opener)
    saved_state = bytes(h.uc.mem_read(LIVE_READERS, 8))
    h.uc.mem_write(LIVE_READERS, struct.pack('<II', 1, 0x12345678))
    return impl, saved, saved_state, pos


def _restore(h, impl, saved, saved_state):
    h.uc.mem_write(impl, saved)
    h.uc.ctl_remove_cache(impl, impl + 8)
    h.uc.mem_write(LIVE_READERS, saved_state)


def test_skin_mesh_load(h):
    """0x4C07C0 reads both empty lists, then the 0x60-byte block; the vector and the vtable stay as they were."""
    impl, saved, saved_state, pos = _with_fake_file(h)
    words = _name_words(NAME)
    try:
        obj = h.alloc(0x74, bytes(0x74))
        h.uc.mem_write(obj, struct.pack('<I', 0xA5A5A5A5) + struct.pack('<I', 0x5A) + bytes(12) + b'\xEE' * 0x60)
        diffs = h.compare(SKINMESH_LOAD, args=words, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        res = h.call(SKINMESH_LOAD, args=words, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, obj) != 0xA5A5A5A5:
            return ['the vtable was written']
        if _u32(h, obj + 4) != 0x5A:
            return ['the allocator slot changed']
        if struct.unpack('<III', h.uc.mem_read(obj + 8, 12)) != (0, 0, 0):
            return ['the vector is %r' % (h.uc.mem_read(obj + 8, 12),)]
        if bytes(h.uc.mem_read(obj + 0x14, 0x60)) != BLOCK:
            return ['the file block was not copied']
        if _u32(h, pos) != BLOB_SIZE:
            return ['the file offset is %#x, not %#x' % (_u32(h, pos), BLOB_SIZE)]
        return []
    finally:
        _restore(h, impl, saved, saved_state)


def test_skin_mesh_ctor(h):
    """0x4C0A10 tags the mesh, clears the vector and loads the name."""
    impl, saved, saved_state, pos = _with_fake_file(h)
    words = _name_words(NAME)
    try:
        obj = h.alloc(0x74, b'\x5A' * 0x74)
        diffs = h.compare(SKINMESH_CTOR, args=words, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        res = h.call(SKINMESH_CTOR, args=words, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, obj) != SKINMESH_VFT:
            return ['the vtable is %#x' % _u32(h, obj)]
        if _u32(h, obj + 4) != 0x5A5A5A5A:
            return ['the allocator slot was written']
        if struct.unpack('<III', h.uc.mem_read(obj + 8, 12)) != (0, 0, 0):
            return ['the vector is %r' % (h.uc.mem_read(obj + 8, 12),)]
        if bytes(h.uc.mem_read(obj + 0x14, 0x60)) != BLOCK:
            return ['the file block was not copied']
        if _u32(h, pos) != BLOB_SIZE:
            return ['the file offset is %#x, not %#x' % (_u32(h, pos), BLOB_SIZE)]
        return []
    finally:
        _restore(h, impl, saved, saved_state)


def test_destroy_skin_mesh(h):
    """0x4C06D0 deletes the non-null elements through vtable slot 0 and frees the buffer."""
    obj = h.alloc(0x74, b'\x5A' * 0x74)
    marker = h.alloc(4, bytes(4))
    stub = _body(h, b'\xc7\x05' + struct.pack('<I', marker) + b'\x01\x00\x00\x00'  # mov [marker], 1
                 + b'\x8b\xc1\xc2\x04\x00')                                          # mov eax, ecx; ret 4
    vtable = h.alloc(4, struct.pack('<I', stub))
    element = h.alloc(4, struct.pack('<I', vtable))
    buffer = h.alloc(12, struct.pack('<III', element, 0, 0xDEADBEEF))
    h.uc.mem_write(obj, struct.pack('<I', 0x5A) + struct.pack('<I', 0x5A)  # allocator slot
                   + struct.pack('<III', buffer, buffer + 4, buffer + 12))

    diffs = h.compare(SKINMESH_DTOR, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(SKINMESH_DTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, obj) != SKINMESH_VFT:
        return ['the vtable is %#x' % _u32(h, obj)]
    if _u32(h, obj + 4) != 0x5A:
        return ['the allocator slot changed']
    if struct.unpack('<III', h.uc.mem_read(obj + 8, 12)) != (0, 0, 0):
        return ['the vector is %r' % (h.uc.mem_read(obj + 8, 12),)]
    if _u32(h, marker) != 1:
        return ['the element destructor ran %d times' % _u32(h, marker)]
    return []


def test_delete_skin_mesh(h):
    """0x4C07A0 destroys the mesh and deletes it only when flag 1 is set; it returns this."""
    diffs = []
    for flags in (0, 1):
        obj = h.alloc(0x74, b'\x5A' * 0x74)
        h.uc.mem_write(obj + 4, struct.pack('<I', 0x5A) + struct.pack('<III', 0, 0, 0))
        diffs += h.compare(DELETE_SKINMESH, args=[flags], regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        res = h.call(DELETE_SKINMESH, args=[flags], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted for flag %d: %s' % (flags, res['fault'])]
        if res['eax'] != obj:
            diffs.append('flag %d returned %#x, not this %#x' % (flags, res['eax'], obj))
        if _u32(h, obj) != SKINMESH_VFT:
            diffs.append('flag %d did not run the destructor' % flags)
    return diffs
