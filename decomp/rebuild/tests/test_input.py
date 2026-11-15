# Differential tests for rebuild/src/engine/input.cpp: CInput state resets on random objects.

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

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


# ---- the recorded-frame player (0x46C6E0) and recorder (0x46D0E0) ---------------------------------
# A frame is the key-state overrides (count, then dik and state per pressed key), the key events (count, then dik
# and the press flag), the mouse buttons (count, then a byte each) and the twelve bytes of the three motion floats.
# The device polls the recorder runs first are no-ops while the object is not acquired (0x7C7 / 0x7C8 clear).

PLAYER = 0x0046C6E0
RECORDER = 0x0046D0E0


def _frame_object(h, playback, size, cursor, keys, buttons):
    obj = h.alloc(0x7CC, b'\xff' * 0x7CC)
    for offset in range(0x008, 0x7CC, 4):
        h.uc.mem_write(obj + offset, bytes(4))
    h.uc.mem_write(obj + 0x660, struct.pack('<II', keys, 0))
    h.uc.mem_write(obj + 0x66C, struct.pack('<II', buttons, 0))
    h.uc.mem_write(obj + 0x650, b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c')
    h.uc.mem_write(obj + 0x678, struct.pack('<III', playback, size, cursor))
    return obj


def _playback_case(h):
    stream = (bytes([2, 0x10, 0x80, 0x20, 0x00])          # two key-state overrides
              + bytes([2, 0x41, 1, 0x42, 2])              # two key events; any nonzero press is a press
              + bytes([1, 3])                             # one mouse button
              + struct.pack('<fff', 1.5, -2.25, 3.75))    # the motion
    buffer = h.alloc(len(stream) + 8, stream + bytes(8))
    keys = h.alloc(8, b'\x11' * 8)
    buttons = h.alloc(8, b'\x22' * 8)
    obj = _frame_object(h, buffer, 0, 0, keys, buttons)
    return obj, buffer, keys, buttons, stream


def test_input_playback_frame(h):
    obj, buffer, keys, buttons, stream = _playback_case(h)
    diffs = h.compare(PLAYER, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(PLAYER, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    key_state = h.uc.mem_read(obj + 0x48, 0x100)
    problems = []
    if key_state[0x10] != 0x80 or key_state[0x20] != 0 or key_state[0] != 0 or key_state[0xFF] != 0:
        problems.append('key state is not the cleared one with the overrides')
    if struct.unpack('<I', h.uc.mem_read(obj + 0x664, 4))[0] != 2:
        problems.append('key count %d' % _loader_u32(h, obj + 0x664))
    if bytes(h.uc.mem_read(keys, 4)) != b'\x41\x01\x42\x01':
        problems.append('key events %r' % bytes(h.uc.mem_read(keys, 4)))
    if _loader_u32(h, obj + 0x670) != 1:
        problems.append('button count %d' % _loader_u32(h, obj + 0x670))
    if struct.unpack('<I', h.uc.mem_read(buttons, 4))[0] != 3:
        problems.append('button %d' % struct.unpack('<I', h.uc.mem_read(buttons, 4))[0])
    if struct.unpack('<fff', h.uc.mem_read(obj + 0x650, 12)) != (1.5, -2.25, 3.75):
        problems.append('motion %r' % (h.uc.mem_read(obj + 0x650, 12),))
    if _loader_u32(h, obj + 0x680) != len(stream):
        problems.append('cursor %d, want %d' % (_loader_u32(h, obj + 0x680), len(stream)))
    return problems


def _record_case(h):
    obj, _, keys, buttons, _ = _playback_case(h)
    buffer = h.alloc(64, bytes(64))
    key_state = bytearray(0x100)
    key_state[0x07] = 0x80
    key_state[0x10] = 0x90
    key_state[0xFF] = 0x85
    key_state[0x20] = 0x7F                                # not held: not recorded
    h.uc.mem_write(obj + 0x48, bytes(key_state))
    h.uc.mem_write(keys, bytes([0x41, 1, 0x42, 0]))
    h.uc.mem_write(obj + 0x664, struct.pack('<I', 2))
    h.uc.mem_write(buttons, struct.pack('<II', 5, 0x107))
    h.uc.mem_write(obj + 0x670, struct.pack('<I', 2))
    h.uc.mem_write(obj + 0x650, struct.pack('<fff', 1.5, -2.25, 3.75))
    h.uc.mem_write(obj + 0x678, struct.pack('<III', buffer, 0, 0))
    return obj, buffer


def test_input_record_frame(h):
    obj, buffer = _record_case(h)
    diffs = h.compare(RECORDER, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(RECORDER, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    want = (bytes([3, 0x07, 0x80, 0x10, 0x90, 0xFF, 0x85])
            + bytes([2, 0x41, 1, 0x42, 0])
            + bytes([2, 5, 7])
            + struct.pack('<fff', 1.5, -2.25, 3.75))
    size = _loader_u32(h, obj + 0x67C)
    if size != len(want):
        return ['size %d, want %d' % (size, len(want))]
    got = bytes(h.uc.mem_read(buffer, len(want)))
    if got != want:
        return ['recording %r, want %r' % (got, want)]
    return []


def test_input_playback_frame_sparse(h):
    stream = bytes(3) + struct.pack('<fff', -0.5, 0.25, 7.0)
    buffer = h.alloc(len(stream) + 8, stream + bytes(8))
    keys = h.alloc(8, b'\x11' * 8)
    buttons = h.alloc(8, b'\x22' * 8)
    obj = _frame_object(h, buffer, 0, 0, keys, buttons)
    diffs = h.compare(PLAYER, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(PLAYER, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    problems = []
    if bytes(h.uc.mem_read(obj + 0x48, 0x100)) != bytes(0x100):
        problems.append('key state not cleared')
    if _loader_u32(h, obj + 0x664) or _loader_u32(h, obj + 0x670):
        problems.append('counts %d / %d' % (_loader_u32(h, obj + 0x664), _loader_u32(h, obj + 0x670)))
    if struct.unpack('<fff', h.uc.mem_read(obj + 0x650, 12)) != (-0.5, 0.25, 7.0):
        problems.append('motion %r' % (h.uc.mem_read(obj + 0x650, 12),))
    if _loader_u32(h, obj + 0x680) != len(stream):
        problems.append('cursor %d, want %d' % (_loader_u32(h, obj + 0x680), len(stream)))
    return problems


def test_input_record_frame_empty(h):
    obj, _, keys, buttons, _ = _playback_case(h)
    buffer = h.alloc(64, bytes(64))
    h.uc.mem_write(obj + 0x48, bytes(0x100))
    h.uc.mem_write(obj + 0x664, struct.pack('<I', 0))
    h.uc.mem_write(obj + 0x670, struct.pack('<I', 0))
    h.uc.mem_write(obj + 0x650, struct.pack('<fff', 0.0, 0.0, 0.0))
    h.uc.mem_write(obj + 0x678, struct.pack('<III', buffer, 0, 0))
    diffs = h.compare(RECORDER, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(RECORDER, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    want = bytes(3) + bytes(12)
    size = _loader_u32(h, obj + 0x67C)
    if size != len(want):
        return ['size %d, want %d' % (size, len(want))]
    got = bytes(h.uc.mem_read(buffer, len(want)))
    if got != want:
        return ['recording %r, want %r' % (got, want)]
    return []


# ---- the device polls (0x46C980 keyboard, 0x46CB50 mouse) -----------------------------------------
# The DirectInput devices are faked: the GetDeviceData slot (10) copies scripted DIDEVICEOBJECTDATA events
# (offset, data) from a cursor and returns the scripted HRESULT, logging every call; the Acquire slot (7) returns
# DIERR_OTHERAPPHASPRIO a scripted number of times before the scripted result.  The editor flag (EditorUtils +0x40)
# and the input's listener lists are set for the duration of the test and restored afterwards.

KEYBOARD = 0x0046C980
MOUSE = 0x0046CB50
EDITOR = 0x006C88D8
MOVE_LISTENERS = 0x006C9054
KEY_DOWN_LISTENERS = 0x006C9044


def _poll_getdata(h, script, cursor, log):
    """stdcall (dev, size, data, count*, flags) -> hr: logs the call, fills count and copies the events"""
    code = (b'\x53\x56\x57\x55'                       # push ebx/esi/edi/ebp
            + b'\x8b\x1d' + struct.pack('<I', log)
            + b'\xff\x05' + struct.pack('<I', log)    # inc dword [log]
            + b'\x6b\xdb\x14'                          # imul ebx, ebx, 20
            + b'\x81\xc3' + struct.pack('<I', log + 4)   # add ebx, log+4
            + b'\x8b\x44\x24\x14\x89\x03'              # [ebx] = dev
            + b'\x8b\x44\x24\x18\x89\x43\x04'          # [ebx+4] = size
            + b'\x8b\x44\x24\x1c\x89\x43\x08'          # [ebx+8] = data
            + b'\x8b\x44\x24\x20\x8b\x00\x89\x43\x0c'  # [ebx+0C] = *count
            + b'\x8b\x44\x24\x24\x89\x43\x10'          # [ebx+10] = flags
            + b'\x8b\x6c\x24\x20'                      # mov ebp, count*
            + b'\x8b\x7c\x24\x1c'                      # mov edi, data
            + b'\x8b\x1d' + struct.pack('<I', cursor)  # mov ebx, [cursor]
            + b'\xbe' + struct.pack('<I', script)      # mov esi, script
            + b'\x03\xf3'                              # add esi, ebx
            + b'\x8b\x06'                              # mov eax, [esi]      n
            + b'\x8b\x56\x04'                          # mov edx, [esi+4]    hr
            + b'\x89\x45\x00'                          # mov [ebp], eax
            + b'\x6b\xc8\x14'                          # imul ecx, eax, 0x14
            + b'\x03\xd9'                              # add ebx, ecx
            + b'\x83\xc3\x08'                          # add ebx, 8
            + b'\x89\x1d' + struct.pack('<I', cursor)  # mov [cursor], ebx
            + b'\x8d\x76\x08'                          # lea esi, [esi+8]
            + b'\xf3\xa4'                              # rep movsb (ecx = n * 0x14 bytes)
            + b'\x89\xd0'                              # mov eax, edx
            + b'\x5d\x5f\x5e\x5b'                      # pop ebp/edi/esi/ebx
            + b'\xc2\x14\x00')                         # ret 0x14
    area = h.alloc(len(code), code)
    return area


def _poll_acquire(h, cell):
    """stdcall (dev) -> hr: [cell] errors of 0x8007001E, then [cell+4]; [cell+8] counts the calls"""
    code = (b'\xb8' + struct.pack('<I', cell)
            + b'\x83\x38\x00'                          # cmp dword [eax], 0
            + b'\x74\x0e'                              # je done
            + b'\x83\x28\x01'                          # sub dword [eax], 1
            + b'\xff\x40\x08'                          # inc dword [eax+8]
            + b'\xb8\x1e\x00\x07\x80'                  # mov eax, 0x8007001E
            + b'\xc2\x04\x00'                          # ret 4
            + b'\xff\x40\x08'                          # done: inc dword [eax+8]
            + b'\x8b\x40\x04'                          # mov eax, [eax+4]
            + b'\xc2\x04\x00')                         # ret 4
    area = h.alloc(len(code), code)
    return area


def _poll_device(h, events, hr=0, acquire_pending=0, acquire_result=0):
    """a device (vtable slot 7 Acquire, 10 GetDeviceData) and the cells its stubs work from"""
    script = struct.pack('<II', len(events), hr & 0xFFFFFFFF)
    for offset, data in events:
        script += struct.pack('<5I', offset, data & 0xFFFFFFFF, 0, 0, 0)
    script += bytes(8)
    cells = {
        'script': h.alloc(len(script), script),
        'cursor': h.alloc(4, bytes(4)),
        'log': h.alloc(4 + 32 * 20, bytes(4 + 32 * 20)),
        'acquire': h.alloc(12, struct.pack('<III', acquire_pending, acquire_result & 0xFFFFFFFF, 0)),
    }
    getdata = _poll_getdata(h, cells['script'], cells['cursor'], cells['log'])
    acquire = _poll_acquire(h, cells['acquire'])
    vtable = h.alloc(0x2C, bytes(0x2C))
    h.uc.mem_write(vtable + 0x1C, struct.pack('<I', acquire))
    h.uc.mem_write(vtable + 0x28, struct.pack('<I', getdata))
    device = h.alloc(4, struct.pack('<I', vtable))
    cells['device'] = device
    cells['vtable'] = vtable
    return cells


def _poll_input(h, device, acquired_offset):
    obj = h.alloc(0x7CC, bytes(0x7CC))
    h.uc.mem_write(obj + 0x44, struct.pack('<I', device))     # also +0x148: both devices point here
    h.uc.mem_write(obj + 0x148, struct.pack('<I', device))
    h.uc.mem_write(obj + acquired_offset, b'\x01')
    keys = h.alloc(0x100, bytes(0x100))
    buttons = h.alloc(0x100, bytes(0x100))
    h.uc.mem_write(obj + 0x660, struct.pack('<II', keys, 0))
    h.uc.mem_write(obj + 0x66C, struct.pack('<II', buttons, 0))
    return obj, keys, buttons


def _poll_getdata_calls(h, cells):
    n = _loader_u32(h, cells['log'])
    return [struct.unpack('<5I', h.uc.mem_read(cells['log'] + 4 + 20 * i, 20)) for i in range(n)]


def _with_editor(h, flag):
    """points the editor singleton at a fake object with the given mode flag; returns the saved pointer"""
    saved = bytes(h.uc.mem_read(EDITOR, 4))
    editor = h.alloc(0x48, bytes(0x48))
    h.uc.mem_write(editor + 0x40, bytes([1 if flag else 0]))
    h.uc.mem_write(EDITOR, struct.pack('<I', editor))
    return saved


def test_input_poll_keyboard(h):
    cells = _poll_device(h, [(0x10, 0x80), (0x20, 0x00), (0x30, 0x81)])
    obj, keys, _ = _poll_input(h, cells['device'], 0x7C7)
    edge = bytes([0x02, 0x08, 0x0A, 0x00, 0x01, 0x04, 0xFF]) + bytes(0x100 - 7)
    h.uc.mem_write(obj + 0x6C4, edge)
    h.uc.mem_write(obj + 0x14C, struct.pack('<I', 0x40))
    h.uc.mem_write(obj + 0x40, struct.pack('<I', 0))
    diffs = h.compare(KEYBOARD, regs={UC_X86_REG_ECX: obj})
    if diffs:
        return diffs
    res = h.call(KEYBOARD, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    problems = []
    calls = _poll_getdata_calls(h, cells)
    if calls != [(cells['device'], 0x14, obj + 0x150, 0x40, 0)]:
        problems.append('device calls %r' % (calls,))
    if res['eax'] != 3:
        problems.append('eax %r, want 3' % res['eax'])
    if _loader_u32(h, obj + 0x14C) != 3:
        problems.append('event count %d' % _loader_u32(h, obj + 0x14C))
    if _loader_u32(h, obj + 0x664) != 3:
        problems.append('key count %d' % _loader_u32(h, obj + 0x664))
    if bytes(h.uc.mem_read(keys, 6)) != bytes([0x10, 1, 0x20, 0, 0x30, 1]):
        problems.append('key events %r' % bytes(h.uc.mem_read(keys, 6)))
    state = h.uc.mem_read(obj + 0x48, 0x100)
    if state[0x10] != 0x90 or state[0x20] != 0x20 or state[0x30] != 0xB0 or state[0] != 0:
        problems.append('key state %02X %02X %02X' % (state[0x10], state[0x20], state[0x30]))
    gotten = h.uc.mem_read(obj + 0x6C4, 0x100)
    want_edge = bytearray(edge)
    want_edge[0], want_edge[1], want_edge[2], want_edge[5], want_edge[6] = 1, 4, 1, 4, 1
    want_edge[0x10] = (want_edge[0x10] & 0xFB) | 2
    want_edge[0x20] = (want_edge[0x20] & 0xFE) | 8
    want_edge[0x30] = (want_edge[0x30] & 0xFB) | 2
    if bytes(gotten) != bytes(want_edge):
        i = next(j for j in range(0x100) if gotten[j] != want_edge[j])
        problems.append('edge flags differ at %02X: %02X want %02X' % (i, gotten[i], want_edge[i]))
    if _loader_u32(h, obj + 0x40) != 0:
        problems.append('result %08X' % _loader_u32(h, obj + 0x40))
    return problems


def test_input_poll_keyboard_retry(h):
    cells = _poll_device(h, [], hr=0x80070001, acquire_pending=2, acquire_result=0)
    obj, _, _ = _poll_input(h, cells['device'], 0x7C7)
    h.uc.mem_write(obj + 0x48, b'\xff' * 0x100)
    h.uc.mem_write(obj + 0x664, struct.pack('<I', 7))
    diffs = h.compare(KEYBOARD, regs={UC_X86_REG_ECX: obj})
    if diffs:
        return diffs
    res = h.call(KEYBOARD, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    problems = []
    if bytes(h.uc.mem_read(obj + 0x48, 0x100)) != bytes(0x100):
        problems.append('key state not cleared')
    if _loader_u32(h, obj + 0x664):
        problems.append('key count %d' % _loader_u32(h, obj + 0x664))
    if res['eax'] != obj + 0x48:                      # the original returns the memset's destination
        problems.append('eax %08X, want the cleared key state' % res['eax'])
    if _loader_u32(h, cells['acquire'] + 8) != 3:
        problems.append('acquire calls %d, want 3' % _loader_u32(h, cells['acquire'] + 8))
    return problems


def test_input_poll_keyboard_not_acquired(h):
    cells = _poll_device(h, [(0x10, 0x80)])
    obj, _, _ = _poll_input(h, cells['device'], 0x7C7)
    h.uc.mem_write(obj + 0x7C7, b'\x00')
    h.uc.mem_write(obj + 0x48, b'\xaa' * 0x100)
    eax = 0x12345678
    diffs = h.compare(KEYBOARD, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: eax}, ret=None)
    if diffs:
        return diffs
    res = h.call(KEYBOARD, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: eax})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    problems = []
    if _poll_getdata_calls(h, cells):
        problems.append('the device was read')
    if bytes(h.uc.mem_read(obj + 0x48, 0x100)) != b'\xaa' * 0x100:
        problems.append('key state changed')
    return problems


def test_input_poll_mouse(h):
    cells = _poll_device(h, [(0, 5), (4, 0xFFFFFFFD), (8, 1), (0xC, 0x80), (0xC, 0x00), (0xE, 0x80)])
    obj, _, buttons = _poll_input(h, cells['device'], 0x7C8)
    h.uc.mem_write(obj + 0x660, struct.pack('<II', h.alloc(0x20, bytes(0x20)), 0))
    h.uc.mem_write(obj + 0x40, struct.pack('<I', 0x55))
    saved = _with_editor(h, False)
    try:
        diffs = h.compare(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x12345678})
        if diffs:
            return diffs
        res = h.call(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x12345678})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        problems = []
        if _poll_getdata_calls(h, cells) != [(cells['device'], 0x14, obj + 0x150, 0x40, 0)]:
            problems.append('device calls %r' % (_poll_getdata_calls(h, cells),))
        if struct.unpack('<fff', h.uc.mem_read(obj + 0x650, 12)) != (5.0, -3.0, 1.0):
            problems.append('motion %r' % (h.uc.mem_read(obj + 0x650, 12),))
        if _loader_u32(h, obj + 0x670) != 3 or struct.unpack('<III', h.uc.mem_read(buttons, 12)) != (0, 1, 4):
            problems.append('button log %d %r' % (_loader_u32(h, obj + 0x670), h.uc.mem_read(buttons, 12)))
        if h.uc.mem_read(obj + 0x7C5, 1) != b'\x00' or h.uc.mem_read(obj + 0x7C6, 1) != b'\x01':
            problems.append('held flags left %02X middle %02X'
                            % (h.uc.mem_read(obj + 0x7C5, 1)[0], h.uc.mem_read(obj + 0x7C6, 1)[0]))
        if h.uc.mem_read(obj + 0x7C9, 1) != b'\x01':
            problems.append('motion not marked')
        if res['eax'] != 0x40A00000:                  # the motion floats, no listeners
            problems.append('eax %08X, want the mouseX bits' % res['eax'])
        if _loader_u32(h, obj + 0x40) != 0:
            problems.append('result %08X' % _loader_u32(h, obj + 0x40))
        return problems
    finally:
        h.uc.mem_write(EDITOR, saved)


def test_input_poll_mouse_button_guard(h):
    """without the editor, the left press while the right button is down is dropped; in the editor it counts"""
    problems = []
    for editor, want_count, want_log in ((False, 1, (2,)), (True, 2, (2, 0))):
        cells = _poll_device(h, [(0xD, 0x80), (0xC, 0x80)])
        obj, _, buttons = _poll_input(h, cells['device'], 0x7C8)
        h.uc.mem_write(obj + 0x7C4, b'\x01')          # the right button is held
        saved = _with_editor(h, editor)
        try:
            diffs = h.compare(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0})
            if diffs:
                return diffs
            res = h.call(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0})
            if res['fault']:
                return ['replacement faulted: %s' % res['fault']]
            count = _loader_u32(h, obj + 0x670)
            if count != want_count:
                problems.append('editor %d: button count %d, want %d' % (editor, count, want_count))
            if h.uc.mem_read(obj + 0x7C5, 1) != bytes([1 if editor else 0]):
                problems.append('editor %d: left held flag %02X' % (editor, h.uc.mem_read(obj + 0x7C5, 1)[0]))
            if struct.unpack('<%dI' % count, h.uc.mem_read(buttons, 4 * count)) != want_log:
                problems.append('editor %d: button log %r, want %r'
                                % (editor, h.uc.mem_read(buttons, 4 * count), want_log))
        finally:
            h.uc.mem_write(EDITOR, saved)
    return problems


def test_input_poll_mouse_retry(h):
    cells = _poll_device(h, [], hr=0x80070001, acquire_pending=1, acquire_result=0x80004005)
    obj, _, buttons = _poll_input(h, cells['device'], 0x7C8)
    h.uc.mem_write(obj + 0x650, b'\x11' * 12)
    h.uc.mem_write(obj + 0x670, struct.pack('<I', 5))
    h.uc.mem_write(buttons, b'\x03' * 4)
    diffs = h.compare(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0})
    if diffs:
        return diffs
    res = h.call(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    problems = []
    if bytes(h.uc.mem_read(obj + 0x650, 12)) != bytes(12):
        problems.append('motion %r, want cleared' % (h.uc.mem_read(obj + 0x650, 12),))
    if _loader_u32(h, obj + 0x670):
        problems.append('button count %d' % _loader_u32(h, obj + 0x670))
    if _loader_u32(h, obj + 0x40) != 0x80004005:
        problems.append('result %08X' % _loader_u32(h, obj + 0x40))
    if _loader_u32(h, cells['acquire'] + 8) != 2:
        problems.append('acquire calls %d, want 2' % _loader_u32(h, cells['acquire'] + 8))
    if res['eax'] != 0x80004005:
        problems.append('eax %08X, want the last result' % res['eax'])
    return problems


def test_input_poll_mouse_not_acquired(h):
    cells = _poll_device(h, [(0, 7)])
    obj, _, _ = _poll_input(h, cells['device'], 0x7C8)
    h.uc.mem_write(obj + 0x7C8, b'\x00')
    h.uc.mem_write(obj + 0x650, b'\x2a' * 12)
    eax = 0xDEADBEEF
    diffs = h.compare(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: eax}, ret=None)
    if diffs:
        return diffs
    res = h.call(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: eax})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    problems = []
    if res['eax'] != eax:
        problems.append('eax %08X, want the previous EAX' % res['eax'])
    if _poll_getdata_calls(h, cells):
        problems.append('the device was read')
    if bytes(h.uc.mem_read(obj + 0x650, 12)) != b'\x2a' * 12:
        problems.append('the motion was cleared')
    return problems


def _move_listener_stub(h, log):
    code = (b'\x53\x56\x57'                           # push ebx/esi/edi
            + b'\xbb' + struct.pack('<I', log)        # mov ebx, log
            + b'\x8b\x03'                              # mov eax, [ebx]   the count
            + b'\xff\x03'                              # inc dword [ebx]
            + b'\x6b\xc0\x10'                          # imul eax, eax, 16
            + b'\x8d\x7c\x03\x04'                      # lea edi, [ebx+eax+4]
            + b'\x8b\x74\x24\x10'                      # mov esi, [esp+0x10]   the event
            + b'\xb9\x04\x00\x00\x00'                  # mov ecx, 4
            + b'\xf3\xa5'                              # rep movsd
            + b'\xb8\xcd\xab\x00\x00'                  # mov eax, 0xABCD
            + b'\x5f\x5e\x5b'                          # pop edi/esi/ebx
            + b'\xc2\x04\x00')                         # ret 4
    return h.alloc(len(code), code)


def test_input_poll_mouse_motion_listener(h):
    cells = _poll_device(h, [(0, 2), (4, 4)])
    obj, _, _ = _poll_input(h, cells['device'], 0x7C8)
    log = h.alloc(4 + 16 * 4, bytes(4 + 16 * 4))
    stub = _move_listener_stub(h, log)
    vt = h.alloc(8, struct.pack('<II', 0, stub))
    listener = h.alloc(8, struct.pack('<II', vt, 0))
    saved = bytes(h.uc.mem_read(MOVE_LISTENERS, 4))
    h.uc.mem_write(MOVE_LISTENERS, struct.pack('<I', listener))
    try:
        diffs = h.compare(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0})
        if diffs:
            return diffs
        res = h.call(MOUSE, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        problems = []
        if _loader_u32(h, log) != 1:
            problems.append('listener calls %d, want 1' % _loader_u32(h, log))
        else:
            got = struct.unpack('<Ifff', h.uc.mem_read(log + 4, 16))
            if got[0] != 0x0060C798 or got[1:] != (2.0, 4.0, 0.0):
                problems.append('move event %r' % (got,))
        if res['eax'] != 0xABCD:
            problems.append('eax %08X, want the listener result' % res['eax'])
        if bytes(h.uc.mem_read(MOVE_LISTENERS, 4)) != struct.pack('<I', listener):
            problems.append('the listener list head was not kept')
        return problems
    finally:
        h.uc.mem_write(MOVE_LISTENERS, saved)

# ---- the input's update part (0x46D030): the mode switch and the fixed-step timer --------------------------------
# The part (CInput + 4) has its own vtable; slot 5 (Tick) is a stub here that logs its calls and returns 0x1000 + 4n.
UPDATE = 0x0046D030


def _tick_stub(h, log):
    """thiscall (part): the n-th call returns 0x1000 + 4n"""
    code = (b'\x56'                                   # push esi
            + b'\xbe' + struct.pack('<I', log)        # mov esi, log
            + b'\x8b\x06'                              # mov eax, [esi]
            + b'\xff\x06'                              # inc dword [esi]
            + b'\x6b\xc0\x04'                          # imul eax, eax, 4
            + b'\x05\x00\x10\x00\x00'                  # add eax, 0x1000
            + b'\x5e'                                  # pop esi
            + b'\xc3')                                 # ret
    return h.alloc(len(code), code)


def _update_case(h, mode, accumulator, interval, dt):
    """an input whose update part has a logging Tick; returns the object and the call log"""
    obj = h.alloc(0x7CC, bytes(0x7CC))
    log = h.alloc(4, bytes(4))
    vtable = h.alloc(0x18, bytes(0x18))
    h.uc.mem_write(vtable + 0x14, struct.pack('<I', _tick_stub(h, log)))
    h.uc.mem_write(obj + 4, struct.pack('<I', vtable))
    h.uc.mem_write(obj + 4 + 0x24, struct.pack('<f', interval))
    h.uc.mem_write(obj + 4 + 0x28, struct.pack('<f', accumulator))
    h.uc.mem_write(obj + 0x674, struct.pack('<I', mode))
    return obj, log


def _update_call(h, obj, dt):
    from unicorn.x86_const import UC_X86_REG_ECX
    return [struct.unpack('<I', struct.pack('<f', dt))[0]], {UC_X86_REG_ECX: obj + 4}


def _part_floats(h, obj):
    return struct.unpack('<ff', h.uc.mem_read(obj + 4 + 0x24, 8))


def test_input_update_frame_polls(h):
    """mode 0 reads the devices and never runs the timer"""
    obj, log = _update_case(h, 0, 25.0, 10.0, 1.0)
    args, regs = _update_call(h, obj, 1.0)
    diffs = h.compare(UPDATE, args=args, regs=regs)
    if diffs:
        return diffs
    res = h.call(UPDATE, args=args, regs=regs)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    problems = []
    if _loader_u32(h, log):
        problems.append('the timer ran %d times' % _loader_u32(h, log))
    if _part_floats(h, obj) != (10.0, 25.0):
        problems.append('the timer moved: %r' % (_part_floats(h, obj),))
    if res['eax'] != 0:                               # neither device acquired: the mouse poll returns its EAX
        problems.append('eax %08X' % res['eax'])
    return problems


def test_input_update_frame_timer(h):
    """in the recording / playback modes a frame short of an interval only drops this frame's input"""
    problems = []
    for mode, want in ((1, 0), (2, 1)):
        obj, log = _update_case(h, mode, 10.0, 33.0, 5.0)
        h.uc.mem_write(obj + 0x650, struct.pack('<fff', 1.5, -2.5, 3.5))
        h.uc.mem_write(obj + 0x664, struct.pack('<I', 7))
        h.uc.mem_write(obj + 0x670, struct.pack('<I', 5))
        keys, buttons = h.alloc(4, b'\x11' * 4), h.alloc(4, b'\x22' * 4)
        h.uc.mem_write(obj + 0x660, struct.pack('<I', keys))
        h.uc.mem_write(obj + 0x66C, struct.pack('<I', buttons))
        args, regs = _update_call(h, obj, 5.0)
        diffs = h.compare(UPDATE, args=args, regs=regs)
        if diffs:
            return diffs
        res = h.call(UPDATE, args=args, regs=regs)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != want:
            problems.append('mode %d: eax %08X, want %d' % (mode, res['eax'], want))
        if _loader_u32(h, log):
            problems.append('mode %d: the timer ran %d times' % (mode, _loader_u32(h, log)))
        if _part_floats(h, obj) != (33.0, 15.0):
            problems.append('mode %d: the timer %r' % (mode, _part_floats(h, obj)))
        if bytes(h.uc.mem_read(obj + 0x650, 12)) != bytes(12):
            problems.append('mode %d: motion %r' % (mode, h.uc.mem_read(obj + 0x650, 12)))
        if _loader_u32(h, obj + 0x664) or _loader_u32(h, obj + 0x670):
            problems.append('mode %d: counts %d %d' % (mode, _loader_u32(h, obj + 0x664),
                                                       _loader_u32(h, obj + 0x670)))
        if _loader_u32(h, obj + 0x660) != keys or _loader_u32(h, obj + 0x66C) != buttons:
            problems.append('mode %d: the buffers were dropped' % mode)
    return problems


def test_input_update_frame_tick(h):
    """a frame that fills the interval runs one Tick and drains the interval; the frame's input stays"""
    problems = []
    for mode in (1, 2):
        obj, log = _update_case(h, mode, 25.0, 10.0, 1.0)
        h.uc.mem_write(obj + 0x650, struct.pack('<fff', 1.5, -2.5, 3.5))
        h.uc.mem_write(obj + 0x664, struct.pack('<I', 7))
        h.uc.mem_write(obj + 0x670, struct.pack('<I', 5))
        args, regs = _update_call(h, obj, 1.0)
        diffs = h.compare(UPDATE, args=args, regs=regs)
        if diffs:
            return diffs
        res = h.call(UPDATE, args=args, regs=regs)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _loader_u32(h, log) != 1:
            problems.append('mode %d: the timer ran %d times, want 1' % (mode, _loader_u32(h, log)))
        if res['eax'] != 0x1000:
            problems.append('mode %d: eax %08X, want the Tick value' % (mode, res['eax']))
        if _part_floats(h, obj) != (10.0, 6.0):
            problems.append('mode %d: the timer %r' % (mode, _part_floats(h, obj)))
        if struct.unpack('<fff', h.uc.mem_read(obj + 0x650, 12)) != (1.5, -2.5, 3.5):
            problems.append('mode %d: the motion was dropped' % mode)
        if _loader_u32(h, obj + 0x664) != 7 or _loader_u32(h, obj + 0x670) != 5:
            problems.append('mode %d: the counts were dropped' % mode)
    return problems


def test_input_update_frame_other_mode(h):
    """any other mode does nothing but return mode - 1"""
    problems = []
    for mode in (3, 5):
        obj, log = _update_case(h, mode, 25.0, 10.0, 1.0)
        h.uc.mem_write(obj + 0x650, struct.pack('<fff', 1.5, -2.5, 3.5))
        args, regs = _update_call(h, obj, 1.0)
        diffs = h.compare(UPDATE, args=args, regs=regs)
        if diffs:
            return diffs
        res = h.call(UPDATE, args=args, regs=regs)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != mode - 1:
            problems.append('mode %d: eax %08X' % (mode, res['eax']))
        if _loader_u32(h, log) or _part_floats(h, obj) != (10.0, 25.0):
            problems.append('mode %d: the timer moved' % mode)
        if struct.unpack('<fff', h.uc.mem_read(obj + 0x650, 12)) != (1.5, -2.5, 3.5):
            problems.append('mode %d: the motion was dropped' % mode)
    return problems
