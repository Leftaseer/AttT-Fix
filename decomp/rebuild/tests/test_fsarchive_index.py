"""The archive's file index value and list: the copier, the node factory, the size guard and the insertions
(0x577660 / 0x5778F0 / 0x5778D0 / 0x577910 / 0x577830 / 0x577AD0 / 0x577B80).

A value is {std::string name; FsFolder *folder; unsigned size} (0x24 bytes), a list node is
{next; prev; FsFileInfo value} (0x2C), and the list is {empty allocator; sentinel; size}.  The sentinel of every
list has self links and no value."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

COPY_INFO = 0x00577660
CONSTRUCT_INFO = 0x005778F0
CREATE_SENTINEL = 0x005778D0
CREATE_NODE = 0x00577910
ADD_SIZE = 0x00577830
INSERT = 0x00577AD0
INSERT_RANGE = 0x00577B80


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


def _info(h, name=b'', folder=0, size=0):
    """a valid FsFileInfo"""
    info = h.alloc(0x24, bytes(0x24))
    _put_string(h, info, name)
    h.uc.mem_write(info + 0x1C, struct.pack('<II', folder, size))
    return info


def _sentinel(h):
    """a list sentinel: a 0x2C-byte node with self links"""
    s = h.alloc(0x2C, bytes(0x2C))
    h.uc.mem_write(s, struct.pack('<II', s, s))
    return s


def _append(h, listobj, info):
    """link a node holding a copy of the value at the end of the list"""
    head = _u32(h, listobj + 4)
    last = _u32(h, head + 4)
    node = h.alloc(0x2C, bytes(0x2C))
    h.uc.mem_write(node, struct.pack('<II', head, last))
    h.uc.mem_write(node + 8, bytes(h.uc.mem_read(info, 0x24)))
    h.uc.mem_write(head + 4, struct.pack('<I', node))
    h.uc.mem_write(last, struct.pack('<I', node))
    h.uc.mem_write(listobj + 8, struct.pack('<I', _u32(h, listobj + 8) + 1))
    return node


def _list_of(h, infos):
    listobj = h.alloc(0x0C, bytes(0x0C))
    head = _sentinel(h)
    h.uc.mem_write(listobj + 4, struct.pack('<II', head, 0))
    nodes = [_append(h, listobj, info) for info in infos]
    return listobj, head, nodes


def _list_values(h, listobj):
    """the values of a list in order"""
    head = _u32(h, listobj + 4)
    out = []
    node = _u32(h, head)
    while node != head:
        out.append(node + 8)
        node = _u32(h, node)
    return out


def test_copy_info(h):
    """0x577660 constructs the value in raw storage: the name (a deep copy), the folder and the size."""
    src = _info(h, b'kingdom.dat', 0x12340000, 0x5678)
    dst = h.alloc(0x24, bytes(0x24))
    diffs = h.compare(COPY_INFO, args=[dst, src], ret=None)
    if diffs:
        return diffs
    res = h.call(COPY_INFO, args=[dst, src])
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _read_string(h, dst) != b'kingdom.dat':
        return ['name %r' % _read_string(h, dst)]
    if _u32(h, dst + 0x1C) != 0x12340000 or _u32(h, dst + 0x20) != 0x5678:
        return ['folder %08X size %X' % (_u32(h, dst + 0x1C), _u32(h, dst + 0x20))]
    return None


def test_copy_info_null(h):
    """0x577660 with a null destination does nothing (the original's guard)."""
    src = _info(h, b'x', 0x10, 1)
    diffs = h.compare(COPY_INFO, args=[0, src], ret=None)
    if diffs:
        return diffs
    res = h.call(COPY_INFO, args=[0, src])
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    return None


def test_construct_info(h):
    """0x5778F0 is the stdcall thunk of the copier."""
    src = _info(h, b'ui\\button.tga', 0xCAFE0000, 0x40)
    dst = h.alloc(0x24, bytes(0x24))
    diffs = h.compare(CONSTRUCT_INFO, args=[dst, src], ret=None)
    if diffs:
        return diffs
    res = h.call(CONSTRUCT_INFO, args=[dst, src])
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _read_string(h, dst) != b'ui\\button.tga':
        return ['name %r' % _read_string(h, dst)]
    if _u32(h, dst + 0x1C) != 0xCAFE0000 or _u32(h, dst + 0x20) != 0x40:
        return ['folder %08X size %X' % (_u32(h, dst + 0x1C), _u32(h, dst + 0x20))]
    return None


def test_sentinel(h):
    """0x5778D0 allocates a 0x2C-byte node whose links point at itself."""
    diffs = h.compare(CREATE_SENTINEL, ret='eax')
    if diffs:
        return diffs
    res = h.call(CREATE_SENTINEL)
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    node = res['eax']
    if (_u32(h, node), _u32(h, node + 4)) != (node, node):
        return ['links %08X/%08X, expected self' % (_u32(h, node), _u32(h, node + 4))]
    return None


def test_create_node(h):
    """0x577910 allocates the 0x2C-byte node, links it and deep-copies the value."""
    info = _info(h, b'sound\\step.wav', 0x77770000, 0x1000)
    next_node = h.alloc(0x2C, bytes(0x2C))
    prev_node = h.alloc(0x2C, bytes(0x2C))
    args = [next_node, prev_node, info]
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
    if _read_string(h, value) != b'sound\\step.wav':
        return ['value name %r' % _read_string(h, value)]
    if _u32(h, value + 0x1C) != 0x77770000 or _u32(h, value + 0x20) != 0x1000:
        return ['value folder %08X size %X' % (_u32(h, value + 0x1C), _u32(h, value + 0x20))]
    return None


def test_add_size(h):
    """0x577830 adds to the list size while the list stays below its 0x71C71C7 limit."""
    listobj = h.alloc(0x0C, bytes(0x0C))
    for size, count in ((0, 1), (0x71C71C0, 4), (5, 0), (0x71C71C6, 1)):
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


def test_insert(h):
    """0x577AD0 creates the node before the position and grows the size."""
    info = _info(h, b'interface.dat', 0x11110000, 0x2222)
    listobj, head, _ = _list_of(h, [_info(h, b'first.dat', 0x10, 1)])
    args = [head, info]
    diffs = h.compare(INSERT, args=args, regs={UC_X86_REG_ECX: listobj}, ret=None)
    if diffs:
        return diffs
    res = h.call(INSERT, args=args, regs={UC_X86_REG_ECX: listobj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if _u32(h, listobj + 8) != 2:
        return ['size %d' % _u32(h, listobj + 8)]
    node = _u32(h, head + 4)
    if _u32(h, node) != head:
        return ['links %08X/%08X' % (_u32(h, node), _u32(h, node + 4))]
    if _u32(h, _u32(h, node + 4)) != node:
        return ['the previous node does not point back']
    values = _list_values(h, listobj)
    if [_read_string(h, v) for v in values] != [b'first.dat', b'interface.dat']:
        return ['order %r' % [_read_string(h, v) for v in values]]
    if _u32(h, values[1] + 0x1C) != 0x11110000 or _u32(h, values[1] + 0x20) != 0x2222:
        return ['value folder %08X size %X' % (_u32(h, values[1] + 0x1C), _u32(h, values[1] + 0x20))]
    return None


def test_insert_range(h):
    """0x577B80 copies a range of another list before the position, in order."""
    a = _info(h, b'a.tga', 0xAA000000, 0x10)
    b = _info(h, b'b.tga', 0xBB000000, 0x20)
    src, src_head, _ = _list_of(h, [a, b])
    dst, dst_head, _ = _list_of(h, [])
    args = [dst_head, _u32(h, src_head), src_head, 0]
    diffs = h.compare(INSERT_RANGE, args=args, regs={UC_X86_REG_ECX: dst}, ret=None)
    if diffs:
        return diffs
    res = h.call(INSERT_RANGE, args=args, regs={UC_X86_REG_ECX: dst})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    values = _list_values(h, dst)
    if [_read_string(h, v) for v in values] != [b'a.tga', b'b.tga']:
        return ['order %r' % [_read_string(h, v) for v in values]]
    if _u32(h, dst + 8) != 2:
        return ['size %d' % _u32(h, dst + 8)]
    if _u32(h, values[0] + 0x1C) != 0xAA000000 or _u32(h, values[1] + 0x1C) != 0xBB000000:
        return ['folders %08X/%08X' % (_u32(h, values[0] + 0x1C), _u32(h, values[1] + 0x1C))]
    return None
