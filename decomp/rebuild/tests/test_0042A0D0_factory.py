"""The mesh object factories 0x42A0D0 and 0x42A330: the name suffix picks the class (".lgdl" -> CLGDLObject
0x25C, ".ska" -> skin mesh 0x248, anything else -> base mesh 0x1DC).  0x42A0D0 hands the mesh constructors a
lowercased copy of the whole name (CharLowerA on c_str), 0x42A330 hands them the name itself.

Operator new and the five class constructors are stubs that log their arguments; operator new returns the block
address the test puts into its log, which is 0 in the allocation-failure runs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FACTORY = 0x0042A0D0
FACTORY_KEEP = 0x0042A330
NEW = 0x005E3EAE
LGDL_CTOR = 0x00471FB0
SKA_CTOR = 0x004C0FE0
MESH_CTOR = 0x004308F0
SKA_CTOR_KEEP = 0x004C1100
MESH_CTOR_KEEP = 0x00430A10

L_SIZE = 0
L_RESULT = 4
L_LGDL = 0x10
L_SKA = 0x20
L_MESH = 0x30
L_SKA_KEEP = 0x40
L_MESH_KEEP = 0x50
LOG_SIZE = 0x80

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


def _put_string(h, p, text):
    """a MSVC 2005 std::string at p (28 bytes)"""
    data = text.encode()
    if len(data) < 16:
        h.uc.mem_write(p + 4, data + b'\0' * (16 - len(data)))
        capacity = 15
    else:
        q = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(p + 4, _dword(q))
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


def _ctor_stub(h, target, log, pop):
    """ECX this, `pop` bytes of stack arguments: logs (this, name, arg[, kind]) and returns this"""
    code = (b'\x89\x0D' + _dword(log)                                # mov [log], ecx
            + b'\x8B\x4C\x24\x04' + b'\x89\x0D' + _dword(log + 4)    # name = [esp+4]
            + b'\x8B\x4C\x24\x08' + b'\x89\x0D' + _dword(log + 8))   # arg = [esp+8]
    if pop == 12:
        code += b'\x8B\x4C\x24\x0C' + b'\x89\x0D' + _dword(log + 12)  # kind = [esp+0xc]
    code += b'\xA1' + _dword(log) + b'\xC2' + struct.pack('<H', pop)  # mov eax, [log] (this); ret pop
    _hook(h, target, code)


def _install(h, result):
    """stubs the factory's callees; operator new answers `result`, every call target has its own log"""
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    _hook(h, NEW,
          b'\x8B\x4C\x24\x04'                                        # mov ecx, [esp+4] size
          + b'\x89\x0D' + _dword(log + L_SIZE)                       # mov [log], ecx
          + b'\xA1' + _dword(log + L_RESULT)                         # mov eax, [log+4]
          + b'\xC3')
    _ctor_stub(h, LGDL_CTOR, log + L_LGDL, 8)
    _ctor_stub(h, SKA_CTOR, log + L_SKA, 8)
    _ctor_stub(h, MESH_CTOR, log + L_MESH, 12)
    _ctor_stub(h, SKA_CTOR_KEEP, log + L_SKA_KEEP, 8)
    _ctor_stub(h, MESH_CTOR_KEEP, log + L_MESH_KEEP, 12)
    h.uc.mem_write(log + L_RESULT, _dword(result))
    return log


def _entry(h, log, offset, words):
    vals = [_u32(h, log + offset + 4 * i) for i in range(words)]
    return vals[0], vals[1:]


def _call(h, entry, name, arg, kind):
    res = h.call(entry, args=[name, arg, kind])
    if res['fault']:
        raise AssertionError('%08X faulted: %s' % (entry, res['fault']))
    return res['eax']


def test_lgdl(h):
    """".lgdl" builds a 0x25C CLGDLObject from the stem"""
    heap0 = h.heap_ptr
    restore = _install_char_lower(h)
    try:
        log = _install(h, 0x0BEE0000)
        name = _string(h, 'foo.lgdl')
        arg = h.alloc(4, bytes(4))
        diffs = h.compare(FACTORY, args=[name, arg, 0x2A], mem=False)
        if diffs:
            return diffs
        got = _call(h, FACTORY, name, arg, 0x2A)
        problems = []
        if _u32(h, log + L_SIZE) != 0x25c:
            problems.append('operator new got %#x bytes' % _u32(h, log + L_SIZE))
        if got != 0x0BEE0000:
            problems.append('the factory returned %#x' % got)
        this, args = _entry(h, log, L_LGDL, 3)
        if this != 0x0BEE0000:
            problems.append('the CLGDL constructor got this %#x' % this)
        if args[0] and _string_text(h, args[0]) != 'foo':
            problems.append('the CLGDL constructor got the name %r' % _string_text(h, args[0]))
        if args[1] != 0x2A:
            problems.append('the CLGDL constructor got the kind %#x' % args[1])
        if _u32(h, log + L_SKA) or _u32(h, log + L_MESH):
            problems.append('a mesh constructor was called as well')
        return problems or None
    finally:
        _restore(h)
        restore()
        h.heap_ptr = heap0


def test_skin(h):
    """".ska" builds a 0x248 skin mesh from a lowercased copy of the whole name"""
    heap0 = h.heap_ptr
    restore = _install_char_lower(h)
    try:
        log = _install(h, 0x0BEE0100)
        name = _string(h, 'Foo.ska')
        arg = h.alloc(4, bytes(4))
        diffs = h.compare(FACTORY, args=[name, arg, 0x2B], mem=False)
        if diffs:
            return diffs
        got = _call(h, FACTORY, name, arg, 0x2B)
        problems = []
        if _u32(h, log + L_SIZE) != 0x248:
            problems.append('operator new got %#x bytes' % _u32(h, log + L_SIZE))
        if got != 0x0BEE0100:
            problems.append('the factory returned %#x' % got)
        this, args = _entry(h, log, L_SKA, 3)
        if this != 0x0BEE0100:
            problems.append('the skin constructor got this %#x' % this)
        if args[0] and _string_text(h, args[0]) != 'foo.ska':
            problems.append('the skin constructor got the name %r' % _string_text(h, args[0]))
        if args[1] != arg:
            problems.append('the skin constructor got the argument %#x' % args[1])
        if _string_text(h, name) != 'foo.ska':
            problems.append('the name was not lowercased: %r' % _string_text(h, name))
        if _u32(h, log + L_LGDL) or _u32(h, log + L_MESH):
            problems.append('another constructor was called as well')
        return problems or None
    finally:
        _restore(h)
        restore()
        h.heap_ptr = heap0


def test_mesh(h):
    """any other name builds a 0x1DC base mesh from a lowercased copy of the name"""
    heap0 = h.heap_ptr
    restore = _install_char_lower(h)
    try:
        log = _install(h, 0x0BEE0200)
        name = _string(h, 'Wall.Bmp')
        arg = h.alloc(4, bytes(4))
        diffs = h.compare(FACTORY, args=[name, arg, 0x2C], mem=False)
        if diffs:
            return diffs
        got = _call(h, FACTORY, name, arg, 0x2C)
        problems = []
        if _u32(h, log + L_SIZE) != 0x1dc:
            problems.append('operator new got %#x bytes' % _u32(h, log + L_SIZE))
        if got != 0x0BEE0200:
            problems.append('the factory returned %#x' % got)
        this, args = _entry(h, log, L_MESH, 4)
        if this != 0x0BEE0200:
            problems.append('the mesh constructor got this %#x' % this)
        if args[0] and _string_text(h, args[0]) != 'wall.bmp':
            problems.append('the mesh constructor got the name %r' % _string_text(h, args[0]))
        if args[1] != arg:
            problems.append('the mesh constructor got the argument %#x' % args[1])
        if args[2] != 0x2C:
            problems.append('the mesh constructor got the kind %#x' % args[2])
        if _string_text(h, name) != 'wall.bmp':
            problems.append('the name was not lowercased: %r' % _string_text(h, name))
        if _u32(h, log + L_LGDL) or _u32(h, log + L_SKA):
            problems.append('another constructor was called as well')
        return problems or None
    finally:
        _restore(h)
        restore()
        h.heap_ptr = heap0


def test_five_char_name(h):
    """five characters are too short for ".lgdl" but ".ska" fits"""
    heap0 = h.heap_ptr
    restore = _install_char_lower(h)
    try:
        log = _install(h, 0x0BEE0300)
        name = _string(h, 'a.ska')
        arg = h.alloc(4, bytes(4))
        diffs = h.compare(FACTORY, args=[name, arg, 0x2D], mem=False)
        if diffs:
            return diffs
        got = _call(h, FACTORY, name, arg, 0x2D)
        problems = []
        if _u32(h, log + L_SIZE) != 0x248:
            problems.append('operator new got %#x bytes' % _u32(h, log + L_SIZE))
        this, args = _entry(h, log, L_SKA, 3)
        if got != 0x0BEE0300 or this != 0x0BEE0300:
            problems.append('the skin constructor was not used: %#x / %#x' % (got, this))
        if args[0] and _string_text(h, args[0]) != 'a.ska':
            problems.append('the skin constructor got the name %r' % _string_text(h, args[0]))
        return problems or None
    finally:
        _restore(h)
        restore()
        h.heap_ptr = heap0


def test_short_name(h):
    """four characters cannot hold a suffix, so the base mesh is built"""
    heap0 = h.heap_ptr
    restore = _install_char_lower(h)
    try:
        log = _install(h, 0x0BEE0400)
        name = _string(h, 'abcd')
        arg = h.alloc(4, bytes(4))
        diffs = h.compare(FACTORY, args=[name, arg, 0x2E], mem=False)
        if diffs:
            return diffs
        got = _call(h, FACTORY, name, arg, 0x2E)
        problems = []
        if _u32(h, log + L_SIZE) != 0x1dc:
            problems.append('operator new got %#x bytes' % _u32(h, log + L_SIZE))
        this, args = _entry(h, log, L_MESH, 4)
        if got != 0x0BEE0400 or this != 0x0BEE0400:
            problems.append('the mesh constructor was not used: %#x / %#x' % (got, this))
        if args[0] and _string_text(h, args[0]) != 'abcd':
            problems.append('the mesh constructor got the name %r' % _string_text(h, args[0]))
        return problems or None
    finally:
        _restore(h)
        restore()
        h.heap_ptr = heap0


def test_allocation_failure(h):
    """when operator new fails the factory returns 0 and builds nothing"""
    heap0 = h.heap_ptr
    restore = _install_char_lower(h)
    try:
        log = _install(h, 0)
        problems = []
        for text in ('foo.lgdl', 'Foo.ska', 'Wall.Bmp'):
            name = _string(h, text)
            arg = h.alloc(4, bytes(4))
            diffs = h.compare(FACTORY, args=[name, arg, 1], mem=False)
            if diffs:
                problems.extend('%r: %s' % (text, d) for d in diffs)
                continue
            if _call(h, FACTORY, name, arg, 1) != 0:
                problems.append('%r: the factory did not return 0' % text)
            if any(_u32(h, log + off) for off in (L_LGDL, L_SKA, L_MESH)):
                problems.append('%r: a constructor ran without an object' % text)
        return problems or None
    finally:
        _restore(h)
        restore()
        h.heap_ptr = heap0


def test_keep_forms(h):
    """0x42A330 hands the class constructor the name itself, not a lowercased copy"""
    heap0 = h.heap_ptr
    try:
        log = _install(h, 0x0BEE0500)
        problems = []
        for text, size, target, offset, expected, words in (
                ('Foo.ska', 0x248, SKA_CTOR_KEEP, L_SKA_KEEP, 'Foo.ska', 3),
                ('Wall.Bmp', 0x1dc, MESH_CTOR_KEEP, L_MESH_KEEP, 'Wall.Bmp', 4),
                ('foo.lgdl', 0x25c, LGDL_CTOR, L_LGDL, 'foo', 3)):
            name = _string(h, text)
            arg = h.alloc(4, bytes(4))
            diffs = h.compare(FACTORY_KEEP, args=[name, arg, 0x31], mem=False)
            if diffs:
                problems.extend('%r: %s' % (text, d) for d in diffs)
                continue
            got = _call(h, FACTORY_KEEP, name, arg, 0x31)
            if _u32(h, log + L_SIZE) != size:
                problems.append('%r: operator new got %#x bytes' % (text, _u32(h, log + L_SIZE)))
            this, args = _entry(h, log, offset, words)
            if got != 0x0BEE0500 or this != 0x0BEE0500:
                problems.append('%r: the constructor was not used: %#x / %#x' % (text, got, this))
            if args[0] and _string_text(h, args[0]) != expected:
                problems.append('%r: the constructor got the name %r' % (text, _string_text(h, args[0])))
            if _string_text(h, name) != text:
                problems.append('%r: the name string was changed to %r' % (text, _string_text(h, name)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
