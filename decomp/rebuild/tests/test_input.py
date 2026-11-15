# Differential tests for rebuild/src/engine/input.cpp: CInput state resets on random objects.

def make_input(h):
    obj = h.alloc(0x7CC, bytes(random.getrandbits(8) for _ in range(0x7CC)))
    nkeys, nbtn = random.randint(0, 40), random.randint(0, 8)
    keys = h.alloc(2 * nkeys + 2, bytes(random.getrandbits(8) for _ in range(2 * nkeys + 2)))
    btns = h.alloc(4 * nbtn + 4, bytes(random.getrandbits(8) for _ in range(4 * nbtn + 4)))
    h.uc.mem_write(obj + 0x660, struct.pack('<II', keys, nkeys))
    h.uc.mem_write(obj + 0x66C, struct.pack('<II', btns, nbtn))
    return obj

def run(h, addr):
    from unicorn.x86_const import UC_X86_REG_ECX
    diffs = []
    for _ in range(30):
        obj = make_input(h)
        diffs += h.compare(addr, args=[], regs={UC_X86_REG_ECX: obj}, ret=None)
    return diffs

def test_reset_mouse(h): return run(h, 0x0046CEB0)
def test_reset_keys(h): return run(h, 0x0046CEF0)
def test_reset(h): return run(h, 0x0046CF30)


# ---- the input.dat loader (0x46B4F0) --------------------------------------------------------------
# Only the CGameFile opening (0x459290) is stubbed: it zeroes the reader, records (this, name, noLoad) and fills
# in the opened flag and a fake FsFile - its read method copies from a byte stream [size][payload] and records
# (buffer, count), its destructor records (self, flags).  The reader's Read (0x458F80), Close (0x459010) and
# destructor (0x459170) run for real in both frames.  The two runs are called directly and their recordings
# compared; the pointers to the loader's stack locals differ between the frames, so only their relations and the
# side effects are compared.

LOADER = 0x0046B4F0
FILE_OPEN = 0x00459290


def _loader_body(h, code):
    area = h.alloc(len(code) + 4, bytes(len(code) + 4))
    h.uc.mem_write(area, code)
    return area


def _loader_redirect(h, entry, body):
    saved = bytes(h.uc.mem_read(entry, 6))
    h.uc.mem_write(entry, b'\xe9' + struct.pack('<i', body - (entry + 5)))
    h.uc.ctl_remove_cache(entry, entry + 8)
    return saved


def _loader_open_stub(h, log, file, opened):
    """logs this/name/noLoad, then zeroes the 0x30-byte reader and fills the FsFile and the opened flag in"""
    code = (b'\x53\x55\x56\x57'               # the callee-saved registers the loader relies on
            + b'\x8b\x54\x24\x14'               # mov edx, [esp+0x14]   name
            + b'\x8b\x5c\x24\x18'               # mov ebx, [esp+0x18]   noLoad
            + b'\xb8' + struct.pack('<I', log)
            + b'\x83\x00\x01'                   # add dword [eax], 1
            + b'\x8b\x28'                       # mov ebp, [eax]
            + b'\x6b\xed\x0c'                   # imul ebp, ebp, 12
            + b'\x8d\x6c\x28\xf8'               # lea ebp, [eax+ebp-8]
            + b'\x89\x4d\x00'                   # mov [ebp], ecx
            + b'\x89\x55\x04'                   # mov [ebp+4], edx
            + b'\x89\x5d\x08'                   # mov [ebp+8], ebx
            + b'\x89\xcf'                       # mov edi, ecx
            + b'\x31\xc0'                       # xor eax, eax
            + b'\xb9\x0c\x00\x00\x00'           # mov ecx, 12
            + b'\xf3\xab'                       # rep stosd
            + b'\x8d\x4f\xd0'                   # lea ecx, [edi-0x30]
            + b'\xc7\x41\x24' + struct.pack('<I', file)     # mov dword [ecx+0x24], file
            + b'\xc6\x41\x2c' + bytes([opened])             # mov byte [ecx+0x2C], opened
            + b'\x5f\x5e\x5d\x5b'               # pop edi/esi/ebp/ebx
            + b'\x89\xc8'                       # mov eax, ecx
            + b'\xc2\x08\x00')                  # ret 8
    return _loader_body(h, code)


def _loader_read_stub(h, log, cursor, source):
    """the FsFile read: logs (buffer, count) and copies from the stream at source + cursor"""
    code = (b'\x8b\x54\x24\x04'                 # mov edx, [esp+4]   buffer
            + b'\x8b\x4c\x24\x08'               # mov ecx, [esp+8]   count
            + b'\x53\x55\x56\x57'               # the callee-saved registers the loader relies on
            + b'\xb8' + struct.pack('<I', log)
            + b'\xff\x00'                       # inc dword [eax]
            + b'\x8b\x18'                       # mov ebx, [eax]
            + b'\x8d\x1c\xdd\xfc\xff\xff\xff'   # lea ebx, [ebx*8-4]
            + b'\x01\xc3'                       # add ebx, eax
            + b'\x89\x13'                       # mov [ebx], edx
            + b'\x89\x4b\x04'                   # mov [ebx+4], ecx
            + b'\x8b\x2d' + struct.pack('<I', cursor)
            + b'\x8d\xb5' + struct.pack('<I', source)   # lea esi, [ebp+source]
            + b'\x89\xd7'                       # mov edi, edx
            + b'\x89\xc8'                       # mov eax, ecx
            + b'\xf3\xa4'                       # rep movsb
            + b'\x01\x05' + struct.pack('<I', cursor)   # add [cursor], eax
            + b'\x5f\x5e\x5d\x5b'               # pop edi/esi/ebp/ebx
            + b'\x89\xd0'                       # mov eax, edx
            + b'\xc2\x08\x00')                  # ret 8
    return _loader_body(h, code)


def _loader_ffile_dtor_stub(h, log):
    """the FsFile destructor: logs (self, flags)"""
    code = (b'\x8b\x54\x24\x04'                 # mov edx, [esp+4]   flags
            + b'\x53\x55\x56\x57'               # the callee-saved registers the loader relies on
            + b'\xb8' + struct.pack('<I', log)
            + b'\xff\x00'                       # inc dword [eax]
            + b'\x8b\x18'                       # mov ebx, [eax]
            + b'\x8d\x1c\xdd\xfc\xff\xff\xff'   # lea ebx, [ebx*8-4]
            + b'\x01\xc3'                       # add ebx, eax
            + b'\x89\x0b'                       # mov [ebx], ecx
            + b'\x89\x53\x04'                   # mov [ebx+4], edx
            + b'\x5f\x5e\x5d\x5b'               # pop edi/esi/ebp/ebx
            + b'\x89\xc8'                       # mov eax, ecx
            + b'\xc2\x04\x00')                  # ret 4
    return _loader_body(h, code)


def _loader_u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _loader_string(h, p):
    size, capacity = struct.unpack('<II', h.uc.mem_read(p + 0x14, 8))
    ptr = p + 4 if capacity < 16 else _loader_u32(h, p + 4)
    return bytes(h.uc.mem_read(ptr, size)).decode()


def _loader_entries(h, log, width, count=None):
    n = _loader_u32(h, log) if count is None else count
    return [struct.unpack('<%dI' % width, h.uc.mem_read(log + 4 + 4 * width * i, 4 * width))
            for i in range(n)]


def _loader_run(h, use_original, opened, payload):
    from unicorn.x86_const import UC_X86_REG_ECX

    logs = {name: h.alloc(0x100, bytes(0x100)) for name in ('open', 'read', 'dtor')}
    cursor = h.alloc(4, bytes(4))
    source = h.alloc(len(payload) + 8, struct.pack('<I', len(payload)) + payload)
    read_stub = _loader_read_stub(h, logs['read'], cursor, source)
    dtor_stub = _loader_ffile_dtor_stub(h, logs['dtor'])
    vtable = h.alloc(8, struct.pack('<II', dtor_stub, read_stub))
    ffile = h.alloc(0xC, struct.pack('<III', vtable, 0, len(payload) + 4))
    saved = _loader_redirect(h, FILE_OPEN,
                             _loader_open_stub(h, logs['open'], ffile if opened else 0, opened))

    obj = h.alloc(0x7CC, bytes(0x7CC))
    h.uc.mem_write(obj + 0x674, struct.pack('<I', 0x11223344))
    original = bytes(h.orig.read(LOADER, 5))
    rebuilt = bytes(h.uc.mem_read(LOADER, 5))
    h.uc.mem_write(LOADER, original if use_original else rebuilt)
    h.uc.ctl_remove_cache(LOADER, LOADER + 8)
    try:
        res = h.call(LOADER, regs={UC_X86_REG_ECX: obj})
    finally:
        h.uc.mem_write(LOADER, rebuilt)
        h.uc.ctl_remove_cache(LOADER, LOADER + 8)
        h.uc.mem_write(FILE_OPEN, saved)
        h.uc.ctl_remove_cache(FILE_OPEN, FILE_OPEN + 8)

    data = _loader_u32(h, obj + 0x678)
    size = _loader_u32(h, obj + 0x67C)
    return {
        'fault': res['fault'],
        'self': obj,
        'open': [(record[0], _loader_string(h, record[1]), record[2])
                 for record in _loader_entries(h, logs['open'], 3)],
        'read': _loader_entries(h, logs['read'], 2),
        'dtor': _loader_entries(h, logs['dtor'], 2),
        'ffile': ffile,
        'mode': _loader_u32(h, obj + 0x674),
        'size': size,
        'data': data,
        'bytes': bytes(h.uc.mem_read(data, len(payload))) if data and size == len(payload) else b'',
        'cursor': _loader_u32(h, obj + 0x680),
    }


def _check_loader(h, opened, payload):
    want_mode = 0x11223344 if opened else 0
    for use_original in (True, False):
        which = 'original' if use_original else 'replacement'
        snap = _loader_run(h, use_original, opened, payload)
        if snap['fault']:
            return ['%s faulted: %s' % (which, snap['fault'])]
        if len(snap['open']) != 1:
            return ['%s opened the file %d times' % (which, len(snap['open']))]
        self_ptr, name, no_load = snap['open'][0]
        if name != 'input.dat' or no_load != 1:
            return ['%s opened %r' % (which, snap['open'][0])]
        if snap['mode'] != want_mode:
            return ['%s mode %08X, want %08X' % (which, snap['mode'], want_mode)]
        if opened:
            if snap['size'] != len(payload):
                return ['%s size %d, want %d' % (which, snap['size'], len(payload))]
            if not snap['data']:
                return ['%s did not allocate the buffer' % which]
            if snap['bytes'] != payload:
                return ['%s read %r' % (which, snap['bytes'])]
            if snap['read'] != [(snap['self'] + 0x67C, 4), (snap['data'], len(payload))]:
                return ['%s reads %r' % (which, snap['read'])]
            if snap['cursor'] != 0:
                return ['%s cursor %d' % (which, snap['cursor'])]
            if snap['dtor'] != [(snap['ffile'], 1)]:
                return ['%s released the stream %r' % (which, snap['dtor'])]
        else:
            if snap['size'] or snap['data']:
                return ['%s left size %d / data %08X' % (which, snap['size'], snap['data'])]
            if snap['read'] or snap['dtor']:
                return ['%s touched the stream (reads %r, released %r)'
                        % (which, snap['read'], snap['dtor'])]
    return []


def test_input_load_playback(h):
    return _check_loader(h, True, bytes(range(1, 0x41)))


def test_input_load_playback_missing_file(h):
    return _check_loader(h, False, b'')
