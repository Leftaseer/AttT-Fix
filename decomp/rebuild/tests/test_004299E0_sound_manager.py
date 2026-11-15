"""The ambient sound manager (0x4299E0..0x42A010): Load (0x4299E0), the map holder's erase (0x429B10), the destructor
(0x429B40), the adjusted-this deleting destructor (0x429D70), the Lua push (0x429D80), the map-init duplicate of
0x427EC0 (0x429DC0), the constructors (0x429DF0 with the registration, 0x429F10 without it), the scalar deleting
destructor (0x429EF0), the +0x1D8 setter (0x429FF0) and the string-headed constructor (0x42A010).

Operator new (0x5E3EAE) hands out 0x34-byte blocks from one pool and operator delete (0x5E3E9C) only records its
argument, so both runs of a comparison build the same objects.  The virtual destructors of the record objects are
pointed at one stub (a counter and the this/flag of each call)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EDX

LOAD = 0x004299E0
MAP_ERASE = 0x00429B10
DTOR = 0x00429B40
ADJ_DTOR = 0x00429D70
PUSH_UD = 0x00429D80
MAP_INIT = 0x00429DC0
CTOR = 0x00429DF0
DEL_DTOR = 0x00429EF0
CTOR_FAST = 0x00429F10
SET_1D8 = 0x00429FF0
STR_CTOR = 0x0042A010

NEW = 0x005E3EAE
FREE = 0x005E3E9C
RESET = 0x00427EC0
INSERT = 0x00429330
CONTAINERS = 0x00427FF0
CGOBJECT_CTOR = 0x00424D00
REGISTER = 0x004287C0
LOADER = 0x00429440
NEW_USERDATA = 0x00403BF0
RAWGETI = 0x00403390
SET_META = 0x004036B0

D_008D122C = 0x008D122C
D_006BF4E4 = 0x006BF4E4
D_0068AE40 = 0x0068AE40
VT_READER = 0x0060B6A4
VT_CGAMEOBJECT = 0x00607D14
VT_MANAGER = 0x006083E0
VT_MANAGER_38 = 0x006083D8
VT_MANAGER_3C = 0x006083D0
VT_MANAGER_38_BASE = 0x00608250
VT_MANAGER_3C_BASE = 0x00608214
VT_CUPDATE = 0x00607D5C

L_NEW = 0x00
L_FREE = 0x04
L_TABLE = 0x08
LOG_SIZE = 0x200

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def _call(h, entry, args=(), regs=None):
    res = h.call(entry, args=args, regs=regs)
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res


def _record(h, key):
    rec = h.alloc(0x20, bytes(0x20))
    h.uc.mem_write(rec, struct.pack('<IIfI', key, 0x100 + key, 1.5, 0x200 + key))
    return rec


def _allocator(h, blocks=48):
    """operator new returns the pool's 0x34-byte blocks in order; operator delete logs its argument"""
    pool = h.alloc(0x34 * (blocks + 1), bytes(0x34 * (blocks + 1)))
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    _hook(h, NEW,
           b'\xFF\x05' + _dword(log + L_NEW)                       # inc [allocations]
           + b'\xA1' + _dword(log + L_NEW)                         # mov eax, [allocations]
           + b'\x6B\xC0\x34'                                       # imul eax, eax, 0x34
           + b'\x05' + _dword(pool)                                # add eax, pool
           + b'\xC3')
    _hook(h, FREE,
           b'\xFF\x05' + _dword(log + L_FREE)                      # inc [frees]
           + b'\x8B\x44\x24\x04'                                   # mov eax, [esp+4]
           + b'\x8B\x15' + _dword(log + L_FREE)                    # mov edx, [frees]
           + b'\x89\x04\x95' + _dword(log + L_TABLE)               # mov [edx*4+table], eax
           + b'\xC3')
    return log


def _freed(h, log):
    count = _u32(h, log + L_FREE)
    return [struct.unpack('<I', h.uc.mem_read(log + L_TABLE + 4 * i, 4))[0] for i in range(1, count + 1)]


def _new_map(h):
    container = h.alloc(0xc, bytes(0xc))
    _call(h, RESET, regs={UC_X86_REG_ECX: container})
    if _u32(h, container + 8) != 0:
        raise AssertionError('the fresh map is not empty')
    return container


def _build(h, container, keys):
    for key in keys:
        rec = _record(h, key)
        out = h.alloc(8, bytes(8))
        _call(h, INSERT, args=(out, rec), regs={UC_X86_REG_ECX: container})
        if h.uc.mem_read(out + 4, 1)[0] != 1:
            raise AssertionError('the insertion of key %d was refused' % key)


def _find(h, container, key):
    head = _u32(h, container + 4)
    n = _u32(h, head + 4)
    while h.uc.mem_read(n + 0x31, 1)[0] == 0:
        k = _u32(h, n + 0xc)
        if k == key:
            return n
        n = _u32(h, n if key < k else n + 8)
    return None


def _obj(h, vtable):
    o = h.alloc(8, bytes(8))
    h.uc.mem_write(o, _dword(vtable))
    return o


def _dtor_logger(h, count=16):
    """a vtable whose slot 0 logs (this, flag) and pops the flag; returns (vtable address, log)"""
    log = h.alloc(0x10 + 8 * count, bytes(0x10 + 8 * count))
    stub = _stub(h,
                 b'\xFF\x05' + _dword(log + 0)                       # inc [calls]
                 + b'\xA1' + _dword(log + 0)                         # mov eax, [calls]
                 + b'\x8B\x15' + _dword(log + 0)                     # mov edx, [calls]
                 + b'\x89\x0C\x95' + _dword(log + 8)                 # mov [edx*4+this], ecx
                 + b'\x8B\x4C\x24\x04'                               # mov ecx, [esp+4]
                 + b'\x89\x0C\x95' + _dword(log + 0x48)              # mov [edx*4+flag], ecx
                 + b'\xC2\x04\x00')                                  # ret 4
    vt = h.alloc(4, _dword(stub))
    return vt, log


def _dtor_calls(h, log):
    n = _u32(h, log)
    this = [struct.unpack('<I', h.uc.mem_read(log + 8 + 4 * i, 4))[0] for i in range(1, n + 1)]
    flag = [struct.unpack('<I', h.uc.mem_read(log + 0x48 + 4 * i, 4))[0] for i in range(1, n + 1)]
    return n, this, flag


def _manager(h, nodes=0):
    """a 0xc0-byte manager with a map at +0x88, container heads at +0x9C/+0xA8 and no child at +0x2C"""
    s = h.alloc(0xc0, bytes(0xc0))
    _call(h, CONTAINERS, regs={UC_X86_REG_ECX: s + 0x98})
    m = _new_map(h)
    h.uc.mem_write(s + 0x88, bytes(h.uc.mem_read(m, 0xc)))
    for key in range(nodes):
        rec = _record(h, key + 1)
        out = h.alloc(8, bytes(8))
        _call(h, INSERT, args=(out, rec), regs={UC_X86_REG_ECX: s + 0x88})
    return s


def _attach_record_objects(h, node, vt, elems=2):
    """gives the record node a virtual object at +0x18 and a vector of `elems` such objects at +0x20"""
    h.uc.mem_write(node + 0x18, _dword(_obj(h, vt)))
    vec = h.alloc(0xc * elems, bytes(0xc * elems))
    for i in range(elems):
        h.uc.mem_write(vec + 0xc * i, _dword(_obj(h, vt)))
    h.uc.mem_write(node + 0x24, _dword(vec) + _dword(vec + 0xc * elems) + _dword(vec + 0xc * elems))
    return vec


def test_map_init(h):
    heap0 = h.heap_ptr
    try:
        _allocator(h)
        container = h.alloc(0xc, bytes(0xc))
        diffs = h.compare(MAP_INIT, regs={UC_X86_REG_ECX: container}, ret=None)
        if diffs:
            return diffs
        _call(h, MAP_INIT, regs={UC_X86_REG_ECX: container})
        head = _u32(h, container + 4)
        problems = []
        if h.uc.mem_read(head + 0x31, 1)[0] != 1:
            problems.append('the head is not the nil node')
        if [_u32(h, head), _u32(h, head + 4), _u32(h, head + 8)] != [head, head, head]:
            problems.append('the head is not a self circle: %r' % [_u32(h, head + 4 * i) for i in range(3)])
        if _u32(h, container + 8) != 0:
            problems.append('the count is %d' % _u32(h, container + 8))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_set_1d8(h):
    heap0 = h.heap_ptr
    try:
        this = h.alloc(0x200, bytes(0x200))
        diffs = h.compare(SET_1D8, args=(0x12345678,), regs={UC_X86_REG_ECX: this}, ret=None)
        if diffs:
            return diffs
        _call(h, SET_1D8, args=(0xCAFEBABE,), regs={UC_X86_REG_ECX: this})
        return None if _u32(h, this + 0x1d8) == 0xCAFEBABE else ['+0x1D8 is %08X' % _u32(h, this + 0x1d8)]
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_map_erase(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        m = _new_map(h)
        _build(h, m, [5, 2, 8, 1])
        head = _u32(h, m + 4)
        diffs = h.compare(MAP_ERASE, regs={UC_X86_REG_ECX: m}, ret=None)
        if diffs:
            return diffs
        _call(h, MAP_ERASE, regs={UC_X86_REG_ECX: m})
        problems = []
        if _u32(h, m + 4) != 0 or _u32(h, m + 8) != 0:
            problems.append('the map holder was not cleared: %08X/%08X' % (_u32(h, m + 4), _u32(h, m + 8)))
        freed = _freed(h, log)
        if len(freed) != 5 or freed[0] == head or freed[-1] != head:
            problems.append('operator delete got %r (head %08X)' % (freed, head))
        if head in freed[:-1]:
            problems.append('the head was freed twice')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_load(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        vt, dlog = _dtor_logger(h)
        s = _manager(h, nodes=2)
        nodes = [_find(h, s + 0x88, 1), _find(h, s + 0x88, 2)]
        vectors = [_attach_record_objects(h, n, vt) for n in nodes]
        h.uc.mem_write(s + 0x40, _dword(_obj(h, vt)))
        released = [_u32(h, s + 0x40)]
        released += [_u32(h, n + 0x18) for n in nodes]
        released += [_u32(h, v + 0xc * i) for v in vectors for i in range(2)]
        h.uc.mem_write(s + 0x74, _dword(0xAAAAAAAA))
        loader = h.alloc(0x20, bytes(0x20))
        _hook(h, LOADER,
               b'\xFF\x05' + _dword(loader + 0)                     # inc [calls]
               + b'\x8B\x15' + _dword(loader + 0)                   # mov edx, [calls]
               + b'\x89\x0C\x95' + _dword(loader + 8)               # mov [edx*4+this], ecx
               + b'\x8B\x4C\x24\x04'                                # mov ecx, [esp+4]
               + b'\x89\x0C\x95' + _dword(loader + 0x10)            # mov [edx*4+name], ecx
               + b'\xC2\x04\x00')                                   # ret 4
        pos = h.alloc(8, struct.pack('<ff', 1.5, -2.5))
        name = h.alloc(0x20, b'\0' * 0x20)
        head = _u32(h, s + 0x8c)
        diffs = h.compare(LOAD, args=(pos, name), regs={UC_X86_REG_ECX: s}, ret=None)
        if diffs:
            return diffs
        _call(h, LOAD, args=(pos, name), regs={UC_X86_REG_ECX: s})
        problems = []
        if _u32(h, s + 0x40) != 0:
            problems.append('the sound object was not cleared')
        if [_u32(h, head), _u32(h, head + 4), _u32(h, head + 8)] != [head, head, head]:
            problems.append('the head is not a self circle')
        if _u32(h, s + 0x90) != 0:
            problems.append('the count is %d' % _u32(h, s + 0x90))
        if _u32(h, s + 0x74) != 0:
            problems.append('+0x74 is %08X' % _u32(h, s + 0x74))
        x, y = struct.unpack('<ff', h.uc.mem_read(s + 0x78, 8))
        if (x, y) != (1.5, -2.5):
            problems.append('the position is %r' % ((x, y),))
        if _u32(h, loader) != 1 or _u32(h, loader + 0xc) != s or _u32(h, loader + 0x14) != name:
            problems.append('the loader ran %d times with %08X/%08X' %
                            (_u32(h, loader), _u32(h, loader + 0xc), _u32(h, loader + 0x14)))
        calls, this, flag = _dtor_calls(h, dlog)
        if calls != 7 or any(f != 1 for f in flag) or sorted(this) != sorted(released):
            problems.append('the virtual destructors ran %d times on %r' % (calls, this))
        freed = _freed(h, log)
        if sorted(freed) != sorted(nodes + vectors):
            problems.append('operator delete got %r' % (freed,))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_destructor(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        vt, dlog = _dtor_logger(h)
        s = _manager(h, nodes=1)
        node = _find(h, s + 0x88, 1)
        vec = _attach_record_objects(h, node, vt)
        head = _u32(h, s + 0x8c)
        # one node threaded off the +0xA8 container head (its +0 link), like the map records
        extra = h.alloc(8, bytes(8))
        link = _u32(h, s + 0xa8)
        h.uc.mem_write(extra, _dword(link) + _dword(0))
        h.uc.mem_write(link, _dword(extra) + _dword(link))
        h.uc.mem_write(s + 0xac, _dword(1))
        head2 = _u32(h, s + 0x9c)
        diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: s}, ret=None)
        if diffs:
            return diffs
        _call(h, DTOR, regs={UC_X86_REG_ECX: s})
        problems = []
        if [_u32(h, s), _u32(h, s + 0x38), _u32(h, s + 0x3c)] != [VT_CGAMEOBJECT, VT_MANAGER_38_BASE, VT_MANAGER_3C]:
            problems.append('the vtables are %08X/%08X/%08X' % (_u32(h, s), _u32(h, s + 0x38), _u32(h, s + 0x3c)))
        if _u32(h, s + 0x44) != VT_CGAMEOBJECT:
            problems.append('the reader base is %08X' % _u32(h, s + 0x44))
        if _u32(h, s + 0x8c) != 0 or _u32(h, s + 0x90) != 0:
            problems.append('the map is %08X/%08X' % (_u32(h, s + 0x8c), _u32(h, s + 0x90)))
        if _u32(h, s + 0xa8) != 0 or _u32(h, s + 0xac) != 0:
            problems.append('the second container is %08X/%08X' % (_u32(h, s + 0xa8), _u32(h, s + 0xac)))
        if _u32(h, s + 0x9c) != 0 or _u32(h, s + 0xa0) != 0:
            problems.append('the first container is %08X/%08X' % (_u32(h, s + 0x9c), _u32(h, s + 0xa0)))
        calls, this, flag = _dtor_calls(h, dlog)
        if calls != 3 or any(f != 1 for f in flag) or sorted(this) != sorted(
                [_u32(h, node + 0x18), _u32(h, vec), _u32(h, vec + 0xc)]):
            problems.append('the virtual destructors ran %d times on %r' % (calls, this))
        freed = _freed(h, log)
        want = [extra, link, head2, vec, node, head]
        if freed != want:
            problems.append('operator delete got %r, want %r' % (freed, want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _dtor_common(h, entry, flag, adjusted):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        s = _manager(h)
        this = s + 0x38 if adjusted else s
        diffs = h.compare(entry, args=(flag,), regs={UC_X86_REG_ECX: this}, ret='eax')
        if diffs:
            return diffs
        res = _call(h, entry, args=(flag,), regs={UC_X86_REG_ECX: this})
        problems = []
        if res['eax'] != s:
            problems.append('the result is %08X, not %08X' % (res['eax'], s))
        if _u32(h, s) != VT_CGAMEOBJECT:
            problems.append('the vtable is %08X' % _u32(h, s))
        freed = _freed(h, log)
        want_nodes = [] if flag == 0 else [s]
        lists = [n for n in freed if n not in want_nodes]
        if len(lists) != 3:
            problems.append('operator delete got %r (want the object %s and the three heads)' %
                            (freed, 'plus ' if flag else 'without '))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_deleting_dtor_keep(h):
    return _dtor_common(h, DEL_DTOR, 0, False)


def test_deleting_dtor_free(h):
    return _dtor_common(h, DEL_DTOR, 1, False)


def test_adjusted_dtor(h):
    return _dtor_common(h, ADJ_DTOR, 1, True)


def test_push_ud(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        block = h.alloc(0x10, bytes(0x10))
        _patch(h, D_008D122C, _dword(0x0DD00000))
        _patch(h, D_006BF4E4, _dword(0x77))
        _hook(h, NEW_USERDATA,
               b'\xFF\x05' + _dword(log + 0)                        # inc [calls]
               + b'\x8B\x15' + _dword(log + 0)                      # mov edx, [calls]
               + b'\x8B\x4C\x24\x04'                                # mov ecx, [esp+4]
               + b'\x89\x0C\x95' + _dword(log + 8)                  # mov [edx*4+L], ecx
               + b'\x8B\x4C\x24\x08'                                # mov ecx, [esp+8]
               + b'\x89\x0C\x95' + _dword(log + 0x18)               # mov [edx*4+size], ecx
               + b'\xB8' + _dword(block) + b'\xC3')
        _hook(h, RAWGETI,
               b'\xFF\x05' + _dword(log + 0x20)                     # inc [rawgeti]
               + b'\x8B\x15' + _dword(log + 0x20)                   # mov edx, [rawgeti]
               + b'\x8B\x4C\x24\x04'                                # mov ecx, [L]
               + b'\x89\x0C\x95' + _dword(log + 0x28)               # mov [edx*4+L], ecx
               + b'\x8B\x4C\x24\x08'                                # mov ecx, [idx]
               + b'\x89\x0C\x95' + _dword(log + 0x30)               # mov [edx*4+idx], ecx
               + b'\x8B\x4C\x24\x0C'                                # mov ecx, [n]
               + b'\x89\x0C\x95' + _dword(log + 0x38)               # mov [edx*4+n], ecx
               + b'\xC3')
        _hook(h, SET_META,
               b'\xFF\x05' + _dword(log + 0x24)                     # inc [setmeta]
               + b'\xB8\x07\x00\x00\x00\xC3')                       # mov eax, 7; ret
        this = h.alloc(0x40, bytes(0x40))
        diffs = h.compare(PUSH_UD, regs={UC_X86_REG_ECX: this}, ret='eax')
        if diffs:
            return diffs
        res = _call(h, PUSH_UD, regs={UC_X86_REG_ECX: this})
        problems = []
        if res['eax'] != 7:
            problems.append('the result is %d' % res['eax'])
        if _u32(h, log) != 1 or _u32(h, log + 0xc) != 0x0DD00000 or _u32(h, log + 0x1c) != 4:
            problems.append('lua_newuserdata got %08X/%d' % (_u32(h, log + 0xc), _u32(h, log + 0x1c)))
        if _u32(h, block) != this - 0x3c:
            problems.append('the userdata holds %08X, not %08X' % (_u32(h, block), this - 0x3c))
        if _u32(h, log + 0x20) != 1 or _u32(h, log + 0x34) != 0xFFFFD8F0 or _u32(h, log + 0x3c) != 0x77:
            problems.append('lua_rawgeti got %d/%d' % (_u32(h, log + 0x34), _u32(h, log + 0x3c)))
        if _u32(h, log + 0x24) != 1:
            problems.append('lua_setmetatable ran %d times' % _u32(h, log + 0x24))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _ctor_common(h, entry, fast):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        calls = h.alloc(0x40, bytes(0x40))
        _hook(h, CGOBJECT_CTOR,
               b'\xFF\x05' + _dword(calls + 0)                      # inc [base ctor]
               + b'\x8B\x15' + _dword(calls + 0)                    # mov edx, [base ctor]
               + b'\x89\x0C\x95' + _dword(calls + 8)                # mov [edx*4+this], ecx
               + b'\x8B\x4C\x24\x04'                                # mov ecx, [name]
               + b'\x8B\x49\x14'                                    # mov ecx, [ecx+0x14] (size)
               + b'\x89\x0C\x95' + _dword(calls + 0x18)             # mov [edx*4+size], ecx
               + b'\xC2\x08\x00')                                   # ret 8
        if fast:
            _hook(h, REGISTER, b'\xC3')
        else:
            _hook(h, REGISTER,
                   b'\xFF\x05' + _dword(calls + 0x20)               # inc [registration]
                   + b'\x8B\x44\x24\x04\xA3' + _dword(calls + 0x28) # [name] -> log
                   + b'\x8B\x44\x24\x08\xA3' + _dword(calls + 0x2c) # [value] -> log
                   + b'\xC3')
        this = h.alloc(0xc0, bytes(0xc0))
        if fast:
            diffs = h.compare(entry, args=(0x55,), regs={UC_X86_REG_ECX: this, UC_X86_REG_EDX: 0x1234}, ret='eax')
        else:
            diffs = h.compare(entry, regs={UC_X86_REG_ECX: this}, ret='eax')
        if diffs:
            return diffs
        if fast:
            res = _call(h, entry, args=(0x55,), regs={UC_X86_REG_ECX: this, UC_X86_REG_EDX: 0x1234})
        else:
            res = _call(h, entry, regs={UC_X86_REG_ECX: this})
        problems = []
        if res['eax'] != this:
            problems.append('the result is %08X' % res['eax'])
        if [_u32(h, this), _u32(h, this + 0x38), _u32(h, this + 0x3c)] != [VT_MANAGER, VT_MANAGER_38, VT_MANAGER_3C]:
            problems.append('the vtables are %08X/%08X/%08X' %
                            (_u32(h, this), _u32(h, this + 0x38), _u32(h, this + 0x3c)))
        if _u32(h, this + 0x44) != VT_READER:
            problems.append('the reader is %08X' % _u32(h, this + 0x44))
        head = _u32(h, this + 0x8c)
        if [_u32(h, head), _u32(h, head + 4), _u32(h, head + 8)] != [head, head, head]:
            problems.append('the head is not a self circle')
        if h.uc.mem_read(head + 0x31, 1)[0] != 1 or _u32(h, this + 0x90) != 0:
            problems.append('the head flag/count are %d/%d' % (h.uc.mem_read(head + 0x31, 1)[0], _u32(h, this + 0x90)))
        if _u32(h, this + 0x9c) == 0 or _u32(h, this + 0xa8) == 0:
            problems.append('the containers are %08X/%08X' % (_u32(h, this + 0x9c), _u32(h, this + 0xa8)))
        if _u32(h, calls) != 1 or _u32(h, calls + 0xc) != this:
            problems.append('the base constructor ran %d times on %08X' % (_u32(h, calls), _u32(h, calls + 0xc)))
        if fast:
            if _u32(h, this + 0x94) != 0 or _u32(h, this + 0x74) != 0:
                problems.append('+0x94/+0x74 are %08X/%08X' % (_u32(h, this + 0x94), _u32(h, this + 0x74)))
        else:
            if _u32(h, this + 0x94) != _u32(h, D_0068AE40):
                problems.append('+0x94 is %08X' % _u32(h, this + 0x94))
            if _u32(h, calls + 0x20) != 1 or _u32(h, calls + 0x28) != 0x006082D4 \
                    or _u32(h, calls + 0x2c) != this:
                problems.append('the registration got %d/%08X/%08X' % (_u32(h, calls + 0x20), _u32(h, calls + 0x28),
                                                                       _u32(h, calls + 0x2c)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_ctor(h):
    return _ctor_common(h, CTOR, False)


def test_ctor_fast(h):
    return _ctor_common(h, CTOR_FAST, True)


def test_str_ctor(h):
    heap0 = h.heap_ptr
    try:
        this = h.alloc(0x40, bytes(0x40))
        # the by-value std::string (28 bytes: allocator, 16-byte buffer, size, capacity) then the two dwords
        args = (0, 0x64636261, 0x00000000, 0, 0, 4, 15, 0x11111111, 0x22222222)
        diffs = h.compare(STR_CTOR, args=args, regs={UC_X86_REG_ECX: this}, ret='eax')
        if diffs:
            return diffs
        res = _call(h, STR_CTOR, args=args, regs={UC_X86_REG_ECX: this})
        problems = []
        if res['eax'] != this:
            problems.append('the result is %08X' % res['eax'])
        size, cap = struct.unpack('<II', h.uc.mem_read(this + 20, 8))
        if size != 4:
            problems.append('the string size is %d' % size)
        text = h.uc.mem_read(this + 4, 4)
        if text != b'abcd':
            problems.append('the string buffer holds %r' % text)
        if _u32(h, this + 0x1c) != 0x11111111 or _u32(h, this + 0x20) != 0x22222222:
            problems.append('the following dwords are %08X/%08X' % (_u32(h, this + 0x1c), _u32(h, this + 0x20)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
