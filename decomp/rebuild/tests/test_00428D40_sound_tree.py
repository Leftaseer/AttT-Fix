"""The ambient sound map at 0x428D40..0x429920: the node maker (0x428D40), the node's vector release (0x428DD0),
the tree insert (0x428E00), erase (0x429030), the std::out_of_range copy (0x429310), insert by key (0x429330), the
subtree release (0x4293F0), clear (0x4298F0) and range erase (0x429920).

Operator new (0x5E3EAE) hands out 0x34-byte nodes from one pool and operator delete (0x5E3E9C) only records its
argument, so both runs of a comparison build the same tree.  The map head is the +4 field (its +0x31 nil flag set,
+0/+4/+8 a self circle when empty), node links at +0/+4/+8, the key at +0xC, the colour byte +0x30."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

NODE_NEW = 0x00428D40
NODE_FREE = 0x00428DD0
INSERT_AT = 0x00428E00
ERASE = 0x00429030
ERROR_COPY = 0x00429310
INSERT = 0x00429330
ERASE_TREE = 0x004293F0
CLEAR = 0x004298F0
ERASE_RANGE = 0x00429920

NEW = 0x005E3EAE
FREE = 0x005E3E9C
RESET = 0x00427EC0

BASE_COPY = 0x00420C80
IAT_BASE = 0x006073BC
IAT_STR = 0x00607334
BASE_SYM = '__imp_??0exception@std@@QAE@ABV01@@Z'
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z'
VT_OUT_OF_RANGE = 0x00608208

L_NEW = 0x00
L_FREE = 0x04
L_TABLE = 0x08
LOG_SIZE = 0x200

NIL = 0x31
COLOR = 0x30

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


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


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


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


def _allocator(h, nodes=48):
    """operator new returns the pool's 0x34-byte nodes in order; operator delete logs its argument"""
    pool = h.alloc(0x34 * (nodes + 1), bytes(0x34 * (nodes + 1)))
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


def _nodes_allocated(h, log):
    return _u32(h, log + L_NEW)


def _freed(h, log):
    count = _u32(h, log + L_FREE)
    return [struct.unpack('<I', h.uc.mem_read(log + L_TABLE + 4 * i, 4))[0] for i in range(1, count + 1)]


def _record(h, key, byte=0, flag=0):
    rec = h.alloc(0x20, bytes(0x20))
    h.uc.mem_write(rec, struct.pack('<IIfI', key, 0x100 + key, 1.5, 0x200 + key))
    h.uc.mem_write(rec + 0x10, struct.pack('<B', byte))
    return rec


def _head(h, container):
    return _u32(h, container + 4)


def _root(h, container):
    return _u32(h, _head(h, container) + 4)


def _nil(h, node):
    return h.uc.mem_read(node + NIL, 1)[0] != 0


def _find(h, container, key):
    n = _root(h, container)
    while not _nil(h, n):
        k = _u32(h, n + 0xc)
        if k == key:
            return n
        n = _u32(h, n if key < k else n + 8)
    return None


def _inorder(h, container):
    out = []
    head = _head(h, container)
    n = _u32(h, head)
    while n != head:
        if not _nil(h, n):
            out.append(_u32(h, n + 0xc))
            r = _u32(h, n + 8)
            if not _nil(h, r):
                while not _nil(h, _u32(h, r)):
                    r = _u32(h, r)
                n = r
            else:
                p = _u32(h, n + 4)
                while not _nil(h, p) and n == _u32(h, p + 8):
                    n = p
                    p = _u32(h, p + 4)
                n = p
    return out


def _build(h, container, keys):
    for key in keys:
        rec = _record(h, key)
        out = h.alloc(8, bytes(8))
        _call(h, INSERT, args=(out, rec), regs={UC_X86_REG_ECX: container})
        if h.uc.mem_read(out + 4, 1)[0] != 1:
            raise AssertionError('the insertion of key %d was refused' % key)


def _new_map(h):
    container = h.alloc(0xc, bytes(0xc))
    _call(h, RESET, regs={UC_X86_REG_ECX: container})
    if _u32(h, container + 8) != 0:
        raise AssertionError('the fresh map is not empty')
    return container


KEYS = [5, 2, 8, 1, 9, 3, 7, 4, 6, 10]


def test_node_maker(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        rec = _record(h, 0x11223344, byte=0x5a)
        diffs = h.compare(NODE_NEW, args=(0x11111111, 0x22222222, 0x33333333, rec, 0), ret=None)
        if diffs:
            return diffs
        node = _call(h, NODE_NEW, args=(0x11111111, 0x22222222, 0x33333333, rec, 0))['eax']
        problems = []
        fields = struct.unpack('<IIIIIfI', h.uc.mem_read(node, 0x1c))
        if fields[:4] != (0x11111111, 0x22222222, 0x33333333, 0x11223344):
            problems.append('the node fields are %r' % (fields,))
        if fields[4] != 0x100 + 0x11223344 or fields[5] != 1.5 or fields[6] != 0x200 + 0x11223344:
            problems.append('the record dword/float/dword are %r/%r/%r' % fields[4:7])
        if h.uc.mem_read(node + 0x1c, 1)[0] != 0x5a:
            problems.append('the record byte is %02x' % h.uc.mem_read(node + 0x1c, 1)[0])
        if any(h.uc.mem_read(node + 0x20 + i, 1)[0] for i in range(0x10)):
            problems.append('the vector at +0x20 is not zero')
        if h.uc.mem_read(node + COLOR, 1)[0] != 0 or h.uc.mem_read(node + NIL, 1)[0] != 0:
            problems.append('the colour/nil bytes are not 0')
        if _nodes_allocated(h, log) != 1:
            problems.append('operator new ran %d times' % _nodes_allocated(h, log))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_node_free(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        node = h.alloc(0x34, bytes(0x34))
        block = h.alloc(8, bytes(8))
        h.uc.mem_write(node + 0x24, _dword(block))
        h.uc.mem_write(node + 0x28, _dword(0xAAAAAAAA))
        h.uc.mem_write(node + 0x2c, _dword(0xBBBBBBBB))
        diffs = h.compare(NODE_FREE, args=(node,), ret=None)
        if diffs:
            return diffs
        _call(h, NODE_FREE, args=(node,))
        problems = []
        if any(_u32(h, node + 0x24 + 4 * i) for i in range(3)):
            problems.append('the vector was not cleared: %r' % struct.unpack('<III', h.uc.mem_read(node + 0x24, 12)))
        if _freed(h, log) != [block]:
            problems.append('operator delete got %r' % _freed(h, log))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_exception_copy(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        _patch_import(h, IAT_BASE, BASE_SYM,
                      b'\xFF\x05' + _dword(log + 0)                # inc [base builds]
                      + b'\x89\x0D' + _dword(log + 4)              # ecx -> this
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + 0x14)  # [esp+4] -> base src
                      + b'\xC7\x01' + _dword(0xAAAAAAAA)           # mov [ecx], AAAA
                      + b'\xC2\x04\x00')
        _patch_import(h, IAT_STR, STR_SYM,
                      b'\xFF\x05' + _dword(log + 8)                # inc [string copies]
                      + b'\x89\x0D' + _dword(log + 0xc)            # ecx -> string this
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + 0x10)  # [esp+4] -> src
                      + b'\xC7\x01' + _dword(0xBBBBBBBB)
                      + b'\xC2\x04\x00')
        this = h.alloc(0x40, bytes(0x40))
        src = h.alloc(0x40, b'\x11' * 0x40)
        diffs = h.compare(ERROR_COPY, args=(src,), regs={UC_X86_REG_ECX: this})
        if diffs:
            return diffs
        _call(h, ERROR_COPY, args=(src,), regs={UC_X86_REG_ECX: this})
        problems = []
        if _u32(h, this) != VT_OUT_OF_RANGE:
            problems.append('the vtable is %08X' % _u32(h, this))
        if _u32(h, log) != 1 or _u32(h, log + 8) != 1:
            problems.append('the copies ran %d/%d times' % (_u32(h, log), _u32(h, log + 8)))
        if _u32(h, log + 4) != this or _u32(h, log + 0xc) != this + 0xc:
            problems.append('the copies got %08X/%08X' % (_u32(h, log + 4), _u32(h, log + 0xc)))
        if _u32(h, log + 0x10) != src + 0xc:
            problems.append('the string source is %08X' % _u32(h, log + 0x10))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_insert_sequence(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        container = _new_map(h)
        problems = []
        for key in KEYS:
            rec = _record(h, key)
            out = h.alloc(8, bytes(8))
            diffs = h.compare(INSERT, args=(out, rec), regs={UC_X86_REG_ECX: container}, ret=None)
            if diffs:
                return ['key %d: %s' % (key, d) for d in diffs]
            _call(h, INSERT, args=(out, rec), regs={UC_X86_REG_ECX: container})
            if h.uc.mem_read(out + 4, 1)[0] != 1:
                problems.append('key %d was reported as already present' % key)
            added = _u32(h, out)
            if _u32(h, added + 0xc) != key:
                problems.append('key %d gave node %08X (key %d)' % (key, added, _u32(h, added + 0xc)))
        if _u32(h, container + 8) != len(KEYS):
            problems.append('the count is %d' % _u32(h, container + 8))
        if _inorder(h, container) != sorted(KEYS):
            problems.append('the in-order walk is %r' % _inorder(h, container))
        root = _root(h, container)
        if h.uc.mem_read(root + COLOR, 1)[0] != 1:
            problems.append('the root is not black')
        if _nodes_allocated(h, log) != len(KEYS) + 1:
            problems.append('operator new ran %d times' % _nodes_allocated(h, log))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_insert_duplicate(h):
    heap0 = h.heap_ptr
    try:
        _allocator(h)
        container = _new_map(h)
        _build(h, container, KEYS)
        existing = _find(h, container, 4)
        rec = _record(h, 4)
        out = h.alloc(8, bytes(8))
        diffs = h.compare(INSERT, args=(out, rec), regs={UC_X86_REG_ECX: container}, ret=None)
        if diffs:
            return diffs
        _call(h, INSERT, args=(out, rec), regs={UC_X86_REG_ECX: container})
        problems = []
        if h.uc.mem_read(out + 4, 1)[0] != 0:
            problems.append('the duplicate was reported as inserted')
        if _u32(h, out) != existing:
            problems.append('the duplicate returned %08X, want %08X' % (_u32(h, out), existing))
        if _u32(h, container + 8) != len(KEYS):
            problems.append('the count changed to %d' % _u32(h, container + 8))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _erase_case(h, key, want_successor):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        container = _new_map(h)
        _build(h, container, KEYS)
        target = _find(h, container, key)
        if target is None:
            return ['key %d is not in the tree' % key]
        successor = _find(h, container, want_successor)
        out = h.alloc(8, bytes(8))
        diffs = h.compare(ERASE, args=(out, target), regs={UC_X86_REG_ECX: container}, ret=None)
        if diffs:
            return ['key %d: %s' % (key, d) for d in diffs]
        _call(h, ERASE, args=(out, target), regs={UC_X86_REG_ECX: container})
        problems = []
        if _u32(h, out) != successor:
            problems.append('the successor is %08X, want %08X' % (_u32(h, out), successor))
        if _u32(h, container + 8) != len(KEYS) - 1:
            problems.append('the count is %d' % _u32(h, container + 8))
        if target not in _freed(h, log):
            problems.append('the node %08X was not released (freed %r)' % (target, _freed(h, log)))
        if _inorder(h, container) != sorted(k for k in KEYS if k != key):
            problems.append('the in-order walk is %r' % _inorder(h, container))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_erase_leaf(h):
    return _erase_case(h, 4, 5)


def test_erase_one_child(h):
    return _erase_case(h, 9, 10)


def test_erase_two_children(h):
    return _erase_case(h, 2, 3)


def test_erase_root(h):
    return _erase_case(h, 5, 6)


def test_erase_extremes(h):
    heap0 = h.heap_ptr
    try:
        _allocator(h)
        for key, successor, extreme in ((1, 2, 0), (10, 9, 8)):
            container = _new_map(h)
            _build(h, container, KEYS)
            target = _find(h, container, key)
            want = _find(h, container, successor)
            out = h.alloc(8, bytes(8))
            diffs = h.compare(ERASE, args=(out, target), regs={UC_X86_REG_ECX: container}, ret=None)
            if diffs:
                return ['key %d: %s' % (key, d) for d in diffs]
            _call(h, ERASE, args=(out, target), regs={UC_X86_REG_ECX: container})
            head = _head(h, container)
            if _u32(h, head + extreme) != want:
                return ['key %d: the head extreme is %08X, want %08X' % (key, _u32(h, head + extreme), want)]
        return None
    finally:
        h.heap_ptr = heap0


def test_erase_range(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        container = _new_map(h)
        _build(h, container, KEYS)
        first = _find(h, container, 3)
        last = _find(h, container, 8)
        out = h.alloc(8, bytes(8))
        diffs = h.compare(ERASE_RANGE, args=(out, first, last), regs={UC_X86_REG_ECX: container}, ret=None)
        if diffs:
            return diffs
        _call(h, ERASE_RANGE, args=(out, first, last), regs={UC_X86_REG_ECX: container})
        problems = []
        if _u32(h, container + 8) != 5:
            problems.append('the count is %d' % _u32(h, container + 8))
        if _u32(h, out) != last:
            problems.append('the returned iterator is %08X, want %08X' % (_u32(h, out), last))
        if _inorder(h, container) != [1, 2, 8, 9, 10]:
            problems.append('the in-order walk is %r' % _inorder(h, container))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_erase_whole_range(h):
    heap0 = h.heap_ptr
    try:
        _allocator(h)
        container = _new_map(h)
        _build(h, container, KEYS)
        head = _head(h, container)
        out = h.alloc(8, bytes(8))
        diffs = h.compare(ERASE_RANGE, args=(out, _u32(h, head), head), regs={UC_X86_REG_ECX: container}, ret=None)
        if diffs:
            return diffs
        _call(h, ERASE_RANGE, args=(out, _u32(h, head), head), regs={UC_X86_REG_ECX: container})
        problems = []
        if _u32(h, container + 8) != 0:
            problems.append('the count is %d' % _u32(h, container + 8))
        if _u32(h, out) != head:
            problems.append('the returned iterator is %08X, want the head %08X' % (_u32(h, out), head))
        links = struct.unpack('<III', h.uc.mem_read(head, 12))
        if links != (head, head, head):
            problems.append('the head is not a self circle: %08X/%08X/%08X' % links)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_clear(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        container = _new_map(h)
        _build(h, container, KEYS)
        head = _head(h, container)
        diffs = h.compare(CLEAR, regs={UC_X86_REG_ECX: container}, ret=None)
        if diffs:
            return diffs
        _call(h, CLEAR, regs={UC_X86_REG_ECX: container})
        problems = []
        if _u32(h, container + 8) != 0:
            problems.append('the count is %d' % _u32(h, container + 8))
        links = struct.unpack('<III', h.uc.mem_read(head, 12))
        if links != (head, head, head):
            problems.append('the head is not a self circle: %08X/%08X/%08X' % links)
        if len(_freed(h, log)) != len(KEYS):
            problems.append('%d nodes were released, want %d' % (len(_freed(h, log)), len(KEYS)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_erase_tree(h):
    heap0 = h.heap_ptr
    try:
        log = _allocator(h)
        container = _new_map(h)
        _build(h, container, KEYS)
        root = _root(h, container)
        diffs = h.compare(ERASE_TREE, args=(root,), regs={UC_X86_REG_ECX: container}, ret=None)
        if diffs:
            return diffs
        _call(h, ERASE_TREE, args=(root,), regs={UC_X86_REG_ECX: container})
        problems = []
        if len(_freed(h, log)) != len(KEYS):
            problems.append('%d nodes were released, want %d' % (len(_freed(h, log)), len(KEYS)))
        if _u32(h, container + 8) != len(KEYS):
            problems.append('the count is %d, it should be untouched' % _u32(h, container + 8))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_insert_at_root(h):
    heap0 = h.heap_ptr
    try:
        _allocator(h)
        container = _new_map(h)
        head = _head(h, container)
        rec = _record(h, 42)
        out = h.alloc(8, bytes(8))
        diffs = h.compare(INSERT_AT, args=(out, 1, head, rec), regs={UC_X86_REG_ECX: container}, ret=None)
        if diffs:
            return diffs
        _call(h, INSERT_AT, args=(out, 1, head, rec), regs={UC_X86_REG_ECX: container})
        problems = []
        node = _u32(h, out)
        links = struct.unpack('<III', h.uc.mem_read(head, 12))
        if links != (node, node, node):
            problems.append('the head links to %08X/%08X/%08X, want %08X' % (links + (node,)))
        if _u32(h, node + 4) != head:
            problems.append('the root\'s parent is %08X' % _u32(h, node + 4))
        if h.uc.mem_read(node + COLOR, 1)[0] != 1:
            problems.append('the single root is not black')
        if _u32(h, node + 0xc) != 42:
            problems.append('the key is %d' % _u32(h, node + 0xc))
        if _u32(h, container + 8) != 1:
            problems.append('the count is %d' % _u32(h, container + 8))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
