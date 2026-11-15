"""The model name helpers and the loader: SplitStringVector (0x4F7290), DestroyStringVector (0x434A60) and
LoadSkinModel (0x4C0240).

The splitter and the vector destructor run for real (their std::string calls are the MSVCP80 imports the harness
emulates).  The loader's callees - the map find (0x422D80), the mesh file load (0x4BEE20), the two copies
(0x4EE310 / 0x4BEA10), the model record (0x4BE940 / 0x4BE990), the model map slot (0x4C00E0), the clip
(0x4BD930) and the clip map slot (0x5542E0) - are replaced by stubs that record their arguments; the map find
answers the model node to the first lookup and the clip node to the second, the order the loader uses.  The
successful runs compare registers only: the stubs log the addresses of the loader's stack locals, and those
differ between the original's frame and the replacement's.  CharLowerA is installed on the harness the way the
file archive tests do it."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

SPLIT = 0x004F7290
DESTROY = 0x00434A60
LOAD_MODEL = 0x004C0240

FIND = 0x00422D80
LOAD_FILE = 0x004BEE20
COPY_MESHES = 0x004EE310
COPY_TABLE = 0x004BEA10
MAKE_RECORD = 0x004BE940
FREE_RECORD = 0x004BE990
MODEL_SLOT = 0x004C00E0
MAKE_CLIP = 0x004BD930
CLIP_SLOT = 0x005542E0

MODELS_SENTINEL = 0x0EAD0001
ANIMATIONS_SENTINEL = 0x0EAD0002


def _body(h, code):
    area = h.alloc(len(code) + 4, bytes(len(code) + 4))
    h.uc.mem_write(area, code)
    return area


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _redirect(h, entry, body):
    saved = bytes(h.uc.mem_read(entry, 6))
    h.uc.mem_write(entry, b'\xe9' + struct.pack('<i', body - (entry + 5)))
    h.uc.ctl_remove_cache(entry, entry + 8)
    return saved


def _restore_code(h, entry, saved):
    h.uc.mem_write(entry, saved)
    h.uc.ctl_remove_cache(entry, entry + 8)


def _put_string(h, p, text):
    """a MSVC 2005 std::string at p (28 bytes)"""
    data = text.encode()
    if len(data) < 16:
        h.uc.mem_write(p + 4, data + b'\0' * (16 - len(data)))
        capacity = 15
    else:
        q = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(p + 4, struct.pack('<I', q))
        capacity = len(data)
    h.uc.mem_write(p + 0x14, struct.pack('<II', len(data), capacity))


def _string(h, text):
    p = h.alloc(28, bytes(28))
    _put_string(h, p, text)
    return p


def _string_text(h, p):
    size, capacity = struct.unpack('<II', h.uc.mem_read(p + 0x14, 8))
    ptr = p + 4 if capacity < 16 else _u32(h, p + 4)
    return bytes(h.uc.mem_read(ptr, size)).decode()


def _install_char_lower(h):
    old = getattr(h, 'crt_CharLowerA', None)

    def char_lower():
        p = h._arg(0)
        h.uc.mem_write(p, h._cstr(p).lower() + b'\0')
        h._ret(p, 4)

    h.crt_CharLowerA = char_lower

    def restore():
        if old is None:
            if hasattr(h, 'crt_CharLowerA'):
                del h.crt_CharLowerA
        else:
            h.crt_CharLowerA = old
    return restore


def _manager(h):
    manager = h.alloc(0x54, bytes(0x54))
    h.uc.mem_write(manager + 0x0C, struct.pack('<I', MODELS_SENTINEL))
    h.uc.mem_write(manager + 0x34, struct.pack('<I', ANIMATIONS_SENTINEL))
    return manager


def _find_stub(h, log, models_node, animations_node):
    """0x422D80 (ECX map, out, key; ret 8): entries of (map, out, key) at log + 4 + 12*n, count at log.

    The loader looks the model up first and the clip second, and the component stubs hand back the node the map
    they were given belongs to."""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x8b\x10'                                 # mov edx, [eax] count
            + b'\x6b\xd2\x0c'                             # imul edx, edx, 12
            + b'\x03\xd0'                                 # add edx, eax
            + b'\x89\x4a\x04'                             # [entry+0] = map
            + b'\x8b\x4c\x24\x04' + b'\x89\x4a\x08'       # [entry+4] = out
            + b'\x8b\x4c\x24\x08' + b'\x89\x4a\x0c'       # [entry+8] = key
            + b'\x83\x00\x01'                             # add DWORD [eax], 1
            + b'\x81\xfa' + struct.pack('<I', log)        # cmp edx, log
            + b'\x75\x0e'                                 # jne animations
            + b'\x8b\x54\x24\x04'                         # mov edx, [esp+4] (out)
            + b'\xb8' + struct.pack('<I', models_node) + b'\x89\x02' + b'\xc2\x08\x00'
            + b'\x8b\x54\x24\x04'                         # mov edx, [esp+4] (out)
            + b'\xb8' + struct.pack('<I', animations_node) + b'\x89\x02' + b'\xc2\x08\x00')
    return _body(h, code)


def _load_stub(h, log):
    """0x4BEE20 (ECX manager, out, name, frames, drawTable; ret 0x10): records and marks the vector"""
    marker = 0x0BEE0024
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x8b\x4c\x24\x04' + b'\x89\x08'           # out
            + b'\x8b\x4c\x24\x08' + b'\x89\x48\x04'       # name
            + b'\x8b\x4c\x24\x0c' + b'\x89\x48\x08'       # frames
            + b'\x8b\x4c\x24\x10' + b'\x89\x48\x0c'       # drawTable
            + b'\x8b\x54\x24\x04'                         # mov edx, out
            + b'\xc7\x42\x04' + struct.pack('<I', marker)     # begin
            + b'\xc7\x42\x08' + struct.pack('<I', marker + 4) # end
            + b'\xc7\x42\x0c' + struct.pack('<I', marker + 4) # limit
            + b'\x8b\x44\x24\x04'                         # mov eax, out
            + b'\xc2\x10\x00')                            # ret 0x10
    return _body(h, code)


def _copy_stub(h, log):
    """0x4EE310 / 0x4BEA10 (ECX dest, source; ret 4): appends (dest, source) at log + 8*n, count at log+0x10"""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x8b\x50\x10'                             # mov edx, [eax+0x10] count
            + b'\x89\x0c\xd0'                             # mov [eax+edx*8], ecx
            + b'\x8b\x4c\x24\x04'                         # mov ecx, [esp+4]
            + b'\x89\x4c\xd0\x04'                         # mov [eax+edx*8+4], ecx
            + b'\x83\x40\x10\x01'                         # add DWORD [eax+0x10], 1
            + b'\xc2\x04\x00')                            # ret 4
    return _body(h, code)


def _record_stub(h, log):
    """0x4BE940 (ECX record, meshes, drawTable; ret 8): records the arguments and returns the record"""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x89\x08'                                 # [log] = record
            + b'\x8b\x54\x24\x04' + b'\x89\x50\x04'       # [log+4] = meshes
            + b'\x8b\x54\x24\x08' + b'\x89\x50\x08'       # [log+8] = drawTable
            + b'\x8b\xc1'                                 # mov eax, ecx
            + b'\xc2\x08\x00')                            # ret 8
    return _body(h, code)


def _record_free_stub(h, log):
    """0x4BE990 (ECX record; ret): records the record"""
    code = (b'\xb8' + struct.pack('<I', log) + b'\x89\x08' + b'\xc3')
    return _body(h, code)


def _slot_stub(h, log, slot):
    """0x4C00E0 / 0x5542E0 (ECX map, key; ret 4): records and hands out the slot"""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x89\x08'                                 # [log] = map
            + b'\x8b\x4c\x24\x04' + b'\x89\x48\x04'       # key
            + b'\xb8' + struct.pack('<I', slot)           # mov eax, slot
            + b'\xc2\x04\x00')                            # ret 4
    return _body(h, code)


def _clip_stub(h, log):
    """0x4BD930 (ECX memory, name; ret 4): records the arguments and returns the memory"""
    code = (b'\xb8' + struct.pack('<I', log)              # mov eax, log
            + b'\x89\x08'                                 # [log] = memory
            + b'\x8b\xd1'                                 # mov edx, ecx (memory)
            + b'\x8b\x4c\x24\x04' + b'\x89\x48\x04'       # [log+4] = name
            + b'\x8b\xc2'                                 # mov eax, edx
            + b'\xc2\x04\x00')                            # ret 4
    return _body(h, code)


def test_split_string_vector(h):
    """0x4F7290 splits at every ';'; the tail after the last one is a part even when empty."""
    cases = [('alpha;12;beta;', [b'alpha', b'12', b'beta', b'']),
             ('plain', [b'plain']),
             (';a;;b', [b'', b'a', b'', b'b'])]
    for text, want in cases:
        source = _string(h, text)
        parts = h.alloc(0x10, bytes(0x10))
        diffs = h.compare(SPLIT, args=[parts, source, ord(';')])
        if diffs:
            return ['%r: %s' % (text, d) for d in diffs]
        res = h.call(SPLIT, args=[parts, source, ord(';')])
        if res['fault']:
            return ['%r: replacement faulted: %s' % (text, res['fault'])]
        if res['eax'] != parts:
            return ['%r: the splitter returned %#x' % (text, res['eax'])]
        begin, end, limit = struct.unpack('<III', h.uc.mem_read(parts + 4, 12))
        if end - begin != 28 * len(want):
            return ['%r: %d parts' % (text, (end - begin) // 28)]
        for i, expected in enumerate(want):
            if _string_text(h, begin + 28 * i).encode() != expected:
                return ['%r: part %d is %r' % (text, i, _string_text(h, begin + 28 * i))]
    return []


def test_destroy_string_vector(h):
    """0x434A60 destroys every element and frees the buffer; the pointers are cleared."""
    elements = h.alloc(28 * 3, bytes(28 * 3))
    for i, text in enumerate(('one', 'two', 'three')):
        _put_string(h, elements + 28 * i, text)
    parts = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(parts, struct.pack('<I', 0x5A))
    h.uc.mem_write(parts + 4, struct.pack('<III', elements, elements + 56, elements + 84))
    diffs = h.compare(DESTROY, regs={UC_X86_REG_ECX: parts}, ret=None)
    if diffs:
        return diffs
    res = h.call(DESTROY, regs={UC_X86_REG_ECX: parts})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if h.uc.mem_read(parts + 4, 12) != bytes(12):
        return ['the pointers were not cleared']
    if _u32(h, parts) != 0x5A:
        return ['the allocator slot is %#x' % _u32(h, parts)]
    if _string_text(h, elements) != 'one' or _string_text(h, elements + 56) != 'three':
        return ['the elements were not left readable']
    return []


def _entries(h, log):
    return [struct.unpack('<3I', h.uc.mem_read(log + 4 + 12 * i, 12)) for i in range(_u32(h, log))]


def _load_common(h):
    logs = {name: h.alloc(size, bytes(size)) for name, size in
            (('find', 0x1C), ('load', 20), ('mesh_copy', 0x18), ('table_copy', 0x18), ('record', 12),
             ('record_free', 4), ('model_slot', 8), ('clip', 8), ('clip_slot', 8))}
    manager = _manager(h)
    names = _string(h, 'M1;12;clip')
    meshes = h.alloc(0x10, bytes(0x10))
    animation = h.alloc(4, bytes(4))
    draw_table = h.alloc(0x10, bytes(0x10))
    return logs, manager, names, meshes, animation, draw_table


def _redirect_all(h, logs, manager, model_node, animation_node):
    model_slot = h.alloc(0x20, bytes(0x20))
    clip_slot = h.alloc(4, bytes(4))
    stubs = {
        FIND: _find_stub(h, logs['find'], model_node, animation_node),
        LOAD_FILE: _load_stub(h, logs['load']),
        COPY_MESHES: _copy_stub(h, logs['mesh_copy']),
        COPY_TABLE: _copy_stub(h, logs['table_copy']),
        MAKE_RECORD: _record_stub(h, logs['record']),
        FREE_RECORD: _record_free_stub(h, logs['record_free']),
        MODEL_SLOT: _slot_stub(h, logs['model_slot'], model_slot),
        MAKE_CLIP: _clip_stub(h, logs['clip']),
        CLIP_SLOT: _slot_stub(h, logs['clip_slot'], clip_slot),
    }
    saved = {entry: _redirect(h, entry, body) for entry, body in stubs.items()}
    return saved, model_slot, clip_slot


def _unstub(h, saved):
    for entry, code in saved.items():
        _restore_code(h, entry, code)


def _copies(h, log):
    count = _u32(h, log + 0x10)
    return [struct.unpack('<II', h.uc.mem_read(log + 8 * i, 8)) for i in range(count)]


def test_load_skin_model_loads_a_new_model(h):
    """0x4C0240 loads a model the cache does not know, caches a copy of it and builds the missing clip."""
    restore = _install_char_lower(h)
    logs, manager, names, meshes, animation, draw_table = _load_common(h)
    saved, model_slot, clip_slot = _redirect_all(h, logs, manager, MODELS_SENTINEL, ANIMATIONS_SENTINEL)
    try:
        args = [names, meshes, animation, draw_table]
        diffs = h.compare(LOAD_MODEL, args=args, regs={UC_X86_REG_ECX: manager}, ret=None, mem=False)
        if diffs:
            return diffs
        res = h.call(LOAD_MODEL, args=args, regs={UC_X86_REG_ECX: manager})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]

        find, clip_find = _entries(h, logs['find'])
        if find[0] != manager + 4:
            return ['the model lookup got map %#x' % find[0]]
        if _string_text(h, find[2]) != 'm1':
            return ['the model key is %r' % _string_text(h, find[2])]
        if clip_find[0] != manager + 0x2C:
            return ['the clip lookup got map %#x' % clip_find[0]]
        if _string_text(h, clip_find[2]) != 'clip':
            return ['the clip key is %r' % _string_text(h, clip_find[2])]

        load = struct.unpack('<5I', h.uc.mem_read(logs['load'], 20))
        if _string_text(h, load[1]) != 'm1' or load[2] != 12 or load[3] != draw_table:
            return ['the file load got (name %r, frames %d, table %#x)'
                    % (_string_text(h, load[1]), load[2], load[3])]
        if _u32(h, load[0] + 4) != 0x0BEE0024:
            return ['the file load was handed %#x' % load[0]]

        mesh_copies = _copies(h, logs['mesh_copy'])
        record = struct.unpack('<3I', h.uc.mem_read(logs['record'], 12))
        if mesh_copies != [(meshes, load[0]), (model_slot, record[0])]:
            return ['the mesh copies are %r' % (mesh_copies,)]
        table_copies = _copies(h, logs['table_copy'])
        if table_copies != [(model_slot + 0x10, record[0] + 0x10)]:
            return ['the draw table copy is %r' % (table_copies,)]
        if record[1:] != (meshes, draw_table):
            return ['the record got %r' % (record,)]
        if _u32(h, logs['record_free']) != record[0]:
            return ['the record destructor got %#x' % _u32(h, logs['record_free'])]

        slot = struct.unpack('<2I', h.uc.mem_read(logs['model_slot'], 8))
        if slot[0] != manager + 4 or _string_text(h, slot[1]) != 'm1':
            return ['the model slot got map %#x key %r' % (slot[0], _string_text(h, slot[1]))]

        clip = struct.unpack('<2I', h.uc.mem_read(logs['clip'], 8))
        if _string_text(h, clip[1]) != 'clip':
            return ['the clip got the name %r' % _string_text(h, clip[1])]
        if _u32(h, animation) != clip[0]:
            return ['the animation is %#x, not the clip %#x' % (_u32(h, animation), clip[0])]
        clip_slot_log = struct.unpack('<2I', h.uc.mem_read(logs['clip_slot'], 8))
        if clip_slot_log[0] != manager + 0x2C or _string_text(h, clip_slot_log[1]) != 'clip':
            return ['the clip slot got map %#x key %r'
                    % (clip_slot_log[0], _string_text(h, clip_slot_log[1]))]
        if _u32(h, clip_slot) != clip[0]:
            return ['the clip slot holds %#x' % _u32(h, clip_slot)]
        return []
    finally:
        _unstub(h, saved)
        restore()


def test_load_skin_model_from_cache(h):
    """0x4C0240 copies the cached model and takes the cached clip."""
    restore = _install_char_lower(h)
    logs, manager, names, meshes, animation, draw_table = _load_common(h)
    model_node = h.alloc(0x40, bytes(0x40))
    h.uc.mem_write(model_node + 0x24, struct.pack('<III', 0xC0FFEE04, 0xC0FFEE08, 0xC0FFEE0C))
    h.uc.mem_write(model_node + 0x34, struct.pack('<III', 0xC0FFEE34, 0xC0FFEE38, 0xC0FFEE3C))
    animation_node = h.alloc(0x40, bytes(0x40))
    h.uc.mem_write(animation_node + 0x24, struct.pack('<I', 0xCAFEBABE))
    saved, model_slot, clip_slot = _redirect_all(h, logs, manager, model_node, animation_node)
    try:
        args = [names, meshes, animation, draw_table]
        diffs = h.compare(LOAD_MODEL, args=args, regs={UC_X86_REG_ECX: manager}, ret=None, mem=False)
        if diffs:
            return diffs
        res = h.call(LOAD_MODEL, args=args, regs={UC_X86_REG_ECX: manager})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _copies(h, logs['mesh_copy']) != [(meshes, model_node + 0x24)]:
            return ['the mesh copies are %r' % (_copies(h, logs['mesh_copy']),)]
        if _copies(h, logs['table_copy']) != [(draw_table, model_node + 0x34)]:
            return ['the table copies are %r' % (_copies(h, logs['table_copy']),)]
        if _u32(h, animation) != 0xCAFEBABE:
            return ['the animation is %#x' % _u32(h, animation)]
        for name in ('load', 'record', 'record_free', 'model_slot', 'clip', 'clip_slot'):
            if _u32(h, logs[name]) != 0:
                return ['the cache hit still called the %s helper' % name]
        return []
    finally:
        _unstub(h, saved)
        restore()


def _run_original(h, entry, args=(), regs=None):
    """call the original body the rebuilt entry jumps over (the jump is five bytes)"""
    original = bytes(h.orig.read(entry, 5))
    rebuilt = bytes(h.uc.mem_read(entry, 5))
    h.uc.mem_write(entry, original)
    try:
        return h.call(entry, args=args, regs=regs)
    finally:
        h.uc.mem_write(entry, rebuilt)


def test_load_skin_model_bad_name(h):
    """0x4C0240 throws when the name has fewer than three ';' tokens.

    The frame each side unwinds from differs (the original inlines the exception constructor), so the contract is
    only that both sides throw."""
    manager = _manager(h)
    names = _string(h, 'onlyname')
    meshes = h.alloc(0x10, bytes(0x10))
    animation = h.alloc(4, bytes(4))
    draw_table = h.alloc(0x10, bytes(0x10))
    args = [names, meshes, animation, draw_table]
    original = _run_original(h, LOAD_MODEL, args=args, regs={UC_X86_REG_ECX: manager})
    if original['fault'] != 'threw':
        return ['the original did not throw: %r' % original['fault']]
    res = h.call(LOAD_MODEL, args=args, regs={UC_X86_REG_ECX: manager})
    if res['fault'] != 'threw':
        return ['the replacement did not throw: %r' % res['fault']]
    return []
