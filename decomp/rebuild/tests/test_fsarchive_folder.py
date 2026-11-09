"""The archive's folder tree: FsFolderList's sentinel, construction, deep copy, clear and destroy
(0x5777F0 / 0x577A90 / 0x5779A0 / 0x577620 / 0x577810 / 0x5787D0 / 0x5788A0 / 0x470ED0) and FsFolder's
construction, copy, destruction and AddChild (0x577C60 / 0x577CC0 / 0x577B10 / 0x577A20 / 0x578180 /
0x578A20).

A folder is {std::string name; list children; FsFolder *parent}; the list is {empty allocator; sentinel; size}
and its nodes are {next; prev; FsFolder value}.  The sentinel of every list has self links and no value."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

SENTINEL = 0x005777F0
INIT_LIST = 0x00577A90
COPY_LIST = 0x005779A0
CLEAR_LIST = 0x00577620
DESTROY_LIST = 0x00577810
INSERT_RANGE = 0x005787D0
APPEND = 0x005788A0
ADD_SIZE = 0x00470ED0
CREATE_NODE = 0x00578180
INIT_FOLDER = 0x00577C60
INIT_FOLDER_NAMED = 0x00577CC0
COPY_FOLDER = 0x00577B10
DESTROY_FOLDER = 0x00577A20
ADD_CHILD = 0x00578A20


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _put_string(h, addr, text=b''):
    """a VC8 string: allocator, inline buffer, size, capacity"""
    assert len(text) < 16
    h.uc.mem_write(addr, bytes(4))
    h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
    h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))


def _read_string(h, addr):
    size = _u32(h, addr + 20)
    cap = _u32(h, addr + 24)
    data = h.uc.mem_read(addr + 4, 4)
    ptr = (addr + 4) if cap < 16 else struct.unpack('<I', data)[0]
    return bytes(h.uc.mem_read(ptr, size))


def _sentinel(h):
    s = h.alloc(0x34, bytes(0x34))
    h.uc.mem_write(s, struct.pack('<II', s, s))
    return s


def _folder(h, name=b'', parent=0, children=()):
    """a valid folder; children are existing folder addresses appended as list nodes"""
    f = h.alloc(0x2C, bytes(0x2C))
    _put_string(h, f, name)
    head = _sentinel(h)
    h.uc.mem_write(f + 0x20, struct.pack('<II', head, 0))
    h.uc.mem_write(f + 0x28, struct.pack('<I', parent))
    for child in children:
        _append_value(h, f + 0x1C, child)
    return f, head


def _append_value(h, listaddr, folder):
    """link a node holding a copy of the folder's 0x2C bytes at the end of the list"""
    head = _u32(h, listaddr + 4)
    last = _u32(h, head + 4)
    node = h.alloc(0x34, bytes(0x34))
    h.uc.mem_write(node, struct.pack('<II', head, last))
    h.uc.mem_write(node + 8, bytes(h.uc.mem_read(folder, 0x2C)))
    h.uc.mem_write(head + 4, struct.pack('<I', node))
    h.uc.mem_write(last, struct.pack('<I', node))
    h.uc.mem_write(listaddr + 8, struct.pack('<I', _u32(h, listaddr + 8) + 1))
    return node


def _list_of(h, folders):
    """a standalone list object with a node per folder"""
    listobj = h.alloc(0x0C, bytes(0x0C))
    head = _sentinel(h)
    h.uc.mem_write(listobj + 4, struct.pack('<II', head, 0))
    nodes = []
    for folder in folders:
        nodes.append(_append_value(h, listobj, folder))
    return listobj, head, nodes


def _list_folders(h, listobj):
    """the folder addresses of a list in order"""
    head = _u32(h, listobj + 4)
    out = []
    node = _u32(h, head)
    while node != head:
        out.append(node + 8)
        node = _u32(h, node)
    return out


def test_sentinel(h):
    """0x5777F0 allocates a 0x34-byte node whose links point at itself; it carries no value."""
    diffs = h.compare(SENTINEL, ret='eax')
    if diffs:
        return diffs
    res = h.call(SENTINEL)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax']
    if (_u32(h, node), _u32(h, node + 4)) != (node, node):
        return ['links %08X/%08X, expected self' % (_u32(h, node), _u32(h, node + 4))]
    return None


def test_init_list(h):
    """0x577A90 gives the list a fresh sentinel and size 0."""
    listobj = h.alloc(0x0C, bytes(0x0C))
    diffs = h.compare(INIT_LIST, regs={UC_X86_REG_ECX: listobj}, ret=None)
    if diffs:
        return diffs
    res = h.call(INIT_LIST, regs={UC_X86_REG_ECX: listobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    head = _u32(h, listobj + 4)
    if head in (0, 4):
        return ['no sentinel: %08X' % head]
    if (_u32(h, head), _u32(h, head + 4)) != (head, head):
        return ['sentinel links %08X/%08X' % (_u32(h, head), _u32(h, head + 4))]
    if _u32(h, listobj + 8) != 0:
        return ['size %d' % _u32(h, listobj + 8)]
    return None


def test_copy_list(h):
    """0x5779A0 deep-copies the nodes: new sentinel, same order, every folder value copied (its own children
    sentinel and string)."""
    child1 = _folder(h, b'data', 0x11110000)[0]
    child2 = _folder(h, b'maps', 0x22220000)[0]
    src, _, _ = _list_of(h, [child1, child2])
    dst = h.alloc(0x0C, bytes(0x0C))
    diffs = h.compare(COPY_LIST, args=[src], regs={UC_X86_REG_ECX: dst}, ret=None)
    if diffs:
        return diffs
    res = h.call(COPY_LIST, args=[src], regs={UC_X86_REG_ECX: dst})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, dst + 8) != 2:
        return ['size %d' % _u32(h, dst + 8)]
    got = _list_folders(h, dst)
    if len(got) != 2:
        return ['%d nodes' % len(got)]
    if _read_string(h, got[0]) != b'data' or _read_string(h, got[1]) != b'maps':
        return ['names %r/%r' % (_read_string(h, got[0]), _read_string(h, got[1]))]
    if _u32(h, got[0] + 0x28) != 0x11110000:
        return ['parent %08X' % _u32(h, got[0] + 0x28)]
    if _u32(h, got[0] + 0x20) == _u32(h, child1 + 0x20):
        return ['children sentinel shared with the source']
    return None


def test_clear_list(h):
    """0x577620 destroys every folder of the ring, relinks the sentinel and zeroes the size."""
    leaf = _folder(h, b'leaf')[0]
    parent = _folder(h, b'parent', 0, [leaf])[0]
    listobj, head, nodes = _list_of(h, [parent])
    diffs = h.compare(CLEAR_LIST, regs={UC_X86_REG_ECX: listobj}, ret=None)
    if diffs:
        return diffs
    res = h.call(CLEAR_LIST, regs={UC_X86_REG_ECX: listobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, listobj + 8) != 0:
        return ['size %d' % _u32(h, listobj + 8)]
    if (_u32(h, head), _u32(h, head + 4)) != (head, head):
        return ['sentinel not reset: %08X/%08X' % (_u32(h, head), _u32(h, head + 4))]
    return None


def test_destroy_list(h):
    """0x577810 is Clear plus freeing the sentinel and clearing the head field."""
    one = _folder(h, b'one')[0]
    two = _folder(h, b'two')[0]
    listobj, _, _ = _list_of(h, [one, two])
    diffs = h.compare(DESTROY_LIST, regs={UC_X86_REG_ECX: listobj}, ret=None)
    if diffs:
        return diffs
    res = h.call(DESTROY_LIST, regs={UC_X86_REG_ECX: listobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, listobj + 4) != 0 or _u32(h, listobj + 8) != 0:
        return ['head %08X size %d' % (_u32(h, listobj + 4), _u32(h, listobj + 8))]
    return None


def test_insert_range(h):
    """0x5787D0 copies a range of another list before the position, in order."""
    a = _folder(h, b'a')[0]
    b = _folder(h, b'b')[0]
    src, src_head, _ = _list_of(h, [a, b])
    dst, dst_head, _ = _list_of(h, [])
    args = [dst_head, _u32(h, src_head), src_head, src]
    diffs = h.compare(INSERT_RANGE, args=args, regs={UC_X86_REG_ECX: dst}, ret=None)
    if diffs:
        return diffs
    res = h.call(INSERT_RANGE, args=args, regs={UC_X86_REG_ECX: dst})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    got = _list_folders(h, dst)
    if [ _read_string(h, f) for f in got ] != [b'a', b'b']:
        return ['order %r' % [_read_string(h, f) for f in got]]
    if _u32(h, dst + 8) != 2:
        return ['size %d' % _u32(h, dst + 8)]
    return None


def test_append(h):
    """0x5788A0 copies the folder into a node at the end of the list."""
    first = _folder(h, b'first')[0]
    second = _folder(h, b'second')[0]
    listobj, head, _ = _list_of(h, [first])
    diffs = h.compare(APPEND, args=[second], regs={UC_X86_REG_ECX: listobj}, ret=None)
    if diffs:
        return diffs
    res = h.call(APPEND, args=[second], regs={UC_X86_REG_ECX: listobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    got = _list_folders(h, listobj)
    if [_read_string(h, f) for f in got] != [b'first', b'second']:
        return ['order %r' % [_read_string(h, f) for f in got]]
    if _u32(h, head + 4) != got[-1] - 8:
        return ['head->prev %08X != last node %08X' % (_u32(h, head + 4), got[-1] - 8)]
    return None


def test_add_size(h):
    """0x470ED0 adds to the list size while the list stays below its 0x5D1745D limit."""
    listobj = h.alloc(0x0C, bytes(0x0C))
    for size, count in ((0, 1), (0x5D17458, 4), (5, 0)):
        h.uc.mem_write(listobj + 8, struct.pack('<I', size))
        diffs = h.compare(ADD_SIZE, args=[count], regs={UC_X86_REG_ECX: listobj}, ret=None)
        if diffs:
            return ['size %X + %d: %s' % (size, count, d) for d in diffs]
        res = h.call(ADD_SIZE, args=[count], regs={UC_X86_REG_ECX: listobj})
        if res['fault']:
            return ['size %X + %d: fault %s' % (size, count, res['fault'])]
        if _u32(h, listobj + 8) != size + count:
            return ['size %X + %d: got %X' % (size, count, _u32(h, listobj + 8))]
    return None


def test_create_node(h):
    """0x578180 allocates the 0x34-byte node, links it and deep-copies the folder."""
    child = _folder(h, b'child', 0x12340000)[0]
    folder = _folder(h, b'root', 0xCAFE0000, [child])[0]
    next_node = h.alloc(0x34, bytes(0x34))
    prev_node = h.alloc(0x34, bytes(0x34))
    args = [next_node, prev_node, folder]
    diffs = h.compare(CREATE_NODE, args=args, ret='eax')
    if diffs:
        return diffs
    res = h.call(CREATE_NODE, args=args)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax']
    if (_u32(h, node), _u32(h, node + 4)) != (next_node, prev_node):
        return ['links %08X/%08X' % (_u32(h, node), _u32(h, node + 4))]
    value = node + 8
    if _read_string(h, value) != b'root' or _u32(h, value + 0x28) != 0xCAFE0000:
        return ['value name %r parent %08X' % (_read_string(h, value), _u32(h, value + 0x28))]
    if _u32(h, value + 0x24) != 1:
        return ['copied children %d' % _u32(h, value + 0x24)]
    copied_child = _u32(h, _u32(h, value + 0x20))
    if _read_string(h, copied_child + 8) != b'child':
        return ['copied child %r' % _read_string(h, copied_child + 8)]
    return None


def test_init_folder(h):
    """0x577C60 builds an empty-named folder with a fresh children list and leaves the parent unwritten."""
    folder = h.alloc(0x2C, bytes(0x2C))
    diffs = h.compare(INIT_FOLDER, regs={UC_X86_REG_ECX: folder}, ret=None)
    if diffs:
        return diffs
    res = h.call(INIT_FOLDER, regs={UC_X86_REG_ECX: folder})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _read_string(h, folder) != b'' or _u32(h, folder + 0x24) != 0:
        return ['name %r size %d' % (_read_string(h, folder), _u32(h, folder + 0x24))]
    head = _u32(h, folder + 0x20)
    if (_u32(h, head), _u32(h, head + 4)) != (head, head):
        return ['sentinel links %08X/%08X' % (_u32(h, head), _u32(h, head + 4))]
    if _u32(h, folder + 0x28) != 0:
        return ['parent %08X written' % _u32(h, folder + 0x28)]
    return None


def test_init_folder_named(h):
    """0x577CC0 copies the name, builds the empty children list and stores the parent."""
    name = h.alloc(0x1C, bytes(0x1C))
    _put_string(h, name, b'maps\\kingdom')
    folder = h.alloc(0x2C, bytes(0x2C))
    args = [name, 0x0BADF00D]
    diffs = h.compare(INIT_FOLDER_NAMED, args=args, regs={UC_X86_REG_ECX: folder}, ret=None)
    if diffs:
        return diffs
    res = h.call(INIT_FOLDER_NAMED, args=args, regs={UC_X86_REG_ECX: folder})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _read_string(h, folder) != b'maps\\kingdom' or _u32(h, folder + 0x28) != 0x0BADF00D:
        return ['name %r parent %08X' % (_read_string(h, folder), _u32(h, folder + 0x28))]
    if _u32(h, folder + 0x24) != 0:
        return ['size %d' % _u32(h, folder + 0x24)]
    return None


def test_copy_folder(h):
    """0x577B10 copies the name, deep-copies the children list and the parent."""
    grandchild = _folder(h, b'grandchild')[0]
    child = _folder(h, b'child', 0x9000, [grandchild])[0]
    src = _folder(h, b'src', 0xABCD1234, [child])[0]
    dst = h.alloc(0x2C, bytes(0x2C))
    diffs = h.compare(COPY_FOLDER, args=[src], regs={UC_X86_REG_ECX: dst}, ret=None)
    if diffs:
        return diffs
    res = h.call(COPY_FOLDER, args=[src], regs={UC_X86_REG_ECX: dst})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _read_string(h, dst) != b'src' or _u32(h, dst + 0x28) != 0xABCD1234:
        return ['name %r parent %08X' % (_read_string(h, dst), _u32(h, dst + 0x28))]
    if _u32(h, dst + 0x24) != 1:
        return ['children %d' % _u32(h, dst + 0x24)]
    copied = _u32(h, _u32(h, dst + 0x20)) + 8
    if _read_string(h, copied) != b'child' or _u32(h, copied + 0x24) != 1:
        return ['copied child %r/%d' % (_read_string(h, copied), _u32(h, copied + 0x24))]
    return None


def test_destroy_folder(h):
    """0x577A20 destroys the children list (recursively) and the name."""
    leaf = _folder(h, b'leaf')[0]
    child = _folder(h, b'child', 0, [leaf])[0]
    folder, head = _folder(h, b'root', 0, [child])
    diffs = h.compare(DESTROY_FOLDER, regs={UC_X86_REG_ECX: folder}, ret=None)
    if diffs:
        return diffs
    res = h.call(DESTROY_FOLDER, regs={UC_X86_REG_ECX: folder})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, folder + 0x20) != 0 or _u32(h, folder + 0x24) != 0:
        return ['children head %08X size %d' % (_u32(h, folder + 0x20), _u32(h, folder + 0x24))]
    return None


def test_add_child(h):
    """0x578A20 appends a {name; empty children; this} folder and returns it."""
    parent, head = _folder(h, b'parent')
    name = h.alloc(0x1C, bytes(0x1C))
    _put_string(h, name, b'castle')
    diffs = h.compare(ADD_CHILD, args=[name], regs={UC_X86_REG_ECX: parent}, ret='eax')
    if diffs:
        return diffs
    res = h.call(ADD_CHILD, args=[name], regs={UC_X86_REG_ECX: parent})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, parent + 0x24) != 1:
        return ['size %d' % _u32(h, parent + 0x24)]
    node = _u32(h, head + 4)
    child = node + 8
    if res['eax'] != child:
        return ['eax %08X != child %08X' % (res['eax'], child)]
    if _read_string(h, child) != b'castle' or _u32(h, child + 0x28) != parent:
        return ['name %r parent %08X' % (_read_string(h, child), _u32(h, child + 0x28))]
    if _u32(h, child + 0x24) != 0:
        return ['child size %d' % _u32(h, child + 0x24)]
    return None
