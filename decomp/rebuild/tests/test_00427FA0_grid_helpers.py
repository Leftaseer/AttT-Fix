"""The grid helpers at 0x427FA0..0x4281D0: the post-incrementing iterator (0x427FA0), the map constructor with the
extra EDX register argument (0x427FC0), the two-container pair constructor (0x427FF0), the cell insertion through
0x005AD6C0 (0x00428050) and the circular cell numbering pass (0x004281D0) with its functor and animation stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX

POST_INC = 0x00427FA0
MAP_CTOR = 0x00427FC0
PAIR_CTOR = 0x00427FF0
ADD_CELL = 0x00428050
NUMBER_CELLS = 0x004281D0

NODE_NEW = 0x00427C00
LIST_NEW = 0x004C2F40
FIND = 0x00427DD0
SUCCESSOR = 0x00427720
SET_TIME = 0x00427530
FIND_OR_ADD = 0x005AD6C0
NOTIFY = 0x004E0EF0

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _d(addr):
    return struct.pack('<I', addr)


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


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
    return stub


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


def _key_tree(h):
    """an empty map head and the keys 5 and 10 (10 the root with 5 on its left)"""
    head = h.alloc(0x34, bytes(0x34))
    h.uc.mem_write(head, _d(head) + _d(head) + _d(head))
    h.uc.mem_write(head + 0x31, b'\x01')
    nodes = {}
    for key in (10, 5):
        n = h.alloc(0x34, bytes(0x34))
        h.uc.mem_write(n, _d(head) + _d(head) + _d(head))
        h.uc.mem_write(n + 0xC, _d(key))
        nodes[key] = n
    h.uc.mem_write(nodes[10], _d(nodes[5]) + _d(head) + _d(head))
    h.uc.mem_write(nodes[5], _d(head) + _d(nodes[10]) + _d(head))
    h.uc.mem_write(head + 4, _d(nodes[10]))
    return head, nodes


def test_post_increment(h):
    heap0 = h.heap_ptr
    try:
        head, nodes = _key_tree(h)
        slot = h.alloc(4, bytes(4))
        out = h.alloc(4, b'\xCC' * 4)
        cases = [(nodes[5], nodes[10]), (nodes[10], head)]
        for start, want in cases:
            h.uc.mem_write(slot, _d(start))
            h.uc.mem_write(out, b'\xCC' * 4)
            diffs = h.compare(POST_INC, args=(out, 0), regs={UC_X86_REG_ECX: slot}, ret='eax')
            if diffs:
                return diffs
            h.uc.mem_write(slot, _d(start))
            h.uc.mem_write(out, b'\xCC' * 4)
            res = _call(h, POST_INC, args=(out, 0), regs={UC_X86_REG_ECX: slot})
            if _u32(h, out) != start:
                return ['from %08X: out holds %08X' % (start, _u32(h, out))]
            if _u32(h, slot) != want:
                return ['from %08X: the iterator moved to %08X, want %08X' % (start, _u32(h, slot), want)]
            if res['eax'] != out:
                return ['from %08X: returned %08X, want the out slot %08X' % (start, res['eax'], out)]
        return None
    finally:
        h.heap_ptr = heap0


def _fresh_map_state(h, obj):
    """checks that obj+4 holds a fresh empty map: a nil-marked head linked to itself and a zero count"""
    head = _u32(h, obj + 4)
    if not head:
        return ['%08X: no head' % obj]
    if h.uc.mem_read(head + 0x31, 1)[0] != 1:
        return ['%08X: the head is not marked nil' % obj]
    links = struct.unpack('<III', h.uc.mem_read(head, 12))
    if links != (head, head, head):
        return ['%08X: the head links to %08X/%08X/%08X' % ((obj,) + links)]
    if _u32(h, obj + 8):
        return ['%08X: the count is %d' % (obj, _u32(h, obj + 8))]
    return None


def test_map_constructor(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x10, b'\xAA' * 0x10)
        diffs = h.compare(MAP_CTOR, args=(0, 0), regs={UC_X86_REG_ECX: obj, UC_X86_REG_EDX: 0x1234},
                          ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(obj, b'\xAA' * 0x10)
        res = _call(h, MAP_CTOR, args=(0, 0), regs={UC_X86_REG_ECX: obj, UC_X86_REG_EDX: 0x1234})
        if res['eax'] != obj:
            return ['returned %08X, want the object %08X' % (res['eax'], obj)]
        return _fresh_map_state(h, obj)
    finally:
        h.heap_ptr = heap0


def test_pair_constructor(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x18, b'\xAA' * 0x18)
        diffs = h.compare(PAIR_CTOR, regs={UC_X86_REG_ECX: obj}, ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(obj, b'\xAA' * 0x18)
        res = _call(h, PAIR_CTOR, regs={UC_X86_REG_ECX: obj})
        if res['eax'] != obj:
            return ['returned %08X, want the object %08X' % (res['eax'], obj)]
        for offset in (4, 0x10):
            head = _u32(h, obj + offset)
            if not head:
                return ['+%#x: no head' % offset]
            links = struct.unpack('<II', h.uc.mem_read(head, 8))
            if links != (head, head):
                return ['+%#x: the head links to %08X/%08X' % ((offset,) + links)]
        if _u32(h, obj + 8) or _u32(h, obj + 0x14):
            return ['the counts are %d/%d' % (_u32(h, obj + 8), _u32(h, obj + 0x14))]
        return None
    finally:
        h.heap_ptr = heap0


def test_add_cell(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(16, bytes(16))
        count = h.alloc(4, bytes(4))
        notify_log = h.alloc(8, bytes(8))
        notify_count = h.alloc(4, bytes(4))
        obj = h.alloc(8, bytes(8))
        container = h.alloc(0xC, bytes(0xC))
        head = h.alloc(0x34, bytes(0x34))
        node = h.alloc(0x34, bytes(0x34))
        h.uc.mem_write(node + 4, _d(head))
        h.uc.mem_write(obj + 4, _d(container))
        h.uc.mem_write(container, _d(0))
        h.uc.mem_write(container + 4, _d(head))
        h.uc.mem_write(container + 8, _d(0))
        _hook(h, FIND_OR_ADD, b'\x8B\x44\x24\x04'                  # mov eax, [esp+4]
                                + b'\xA3' + _d(log)                 # mov [log], eax
                                + b'\x8B\x44\x24\x08'               # mov eax, [esp+8]
                                + b'\xA3' + _d(log + 4)             # mov [log+4], eax
                                + b'\x8B\x44\x24\x0C'               # mov eax, [esp+0xC]
                                + b'\x8B\x00'                       # mov eax, [eax]
                                + b'\xA3' + _d(log + 8)             # mov [log+8], eax
                                + b'\xFF\x05' + _d(count)           # inc dword [count]
                                + b'\xB8' + _d(node)                # mov eax, node
                                + b'\xC2\x0C\x00')                  # ret 0xC
        _hook(h, NOTIFY, b'\x89\x0D' + _d(notify_log)               # mov [notify_log], ecx
                           + b'\x8B\x44\x24\x04'                    # mov eax, [esp+4]
                           + b'\xA3' + _d(notify_log + 4)           # mov [notify_log+4], eax
                           + b'\xFF\x05' + _d(notify_count)         # inc dword [notify_count]
                           + b'\xC2\x04\x00')                       # ret 4
        diffs = h.compare(ADD_CELL, args=(0x1234,), regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(count, bytes(4))
        h.uc.mem_write(log, bytes(16))
        h.uc.mem_write(notify_count, bytes(4))
        h.uc.mem_write(notify_log, bytes(8))
        h.uc.mem_write(container + 4, _d(head))
        h.uc.mem_write(head, bytes(4))
        _call(h, ADD_CELL, args=(0x1234,), regs={UC_X86_REG_ECX: obj})
        if _u32(h, count) != 1:
            return ['the node lookup ran %d times' % _u32(h, count)]
        got = struct.unpack('<III', h.uc.mem_read(log, 12))
        if got != (container, head, 0x1234):
            return ['the lookup got %08X/%08X/%d, want %08X/%08X/4660'
                    % (got[0], got[1], got[2], container, head)]
        if _u32(h, notify_count) != 1:
            return ['the notification ran %d times' % _u32(h, notify_count)]
        got = struct.unpack('<II', h.uc.mem_read(notify_log, 8))
        if got != (obj, 1):
            return ['the notification got %08X/%d, want %08X/1' % (got + (obj,))]
        if _u32(h, container + 4) != node:
            return ['the container head is %08X, want the node %08X' % (_u32(h, container + 4), node)]
        if _u32(h, head) != node:
            return ['the predecessor points at %08X, want the node %08X' % (_u32(h, head), node)]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _cell_map(h):
    """a map head with the keys 0 and 1 (1 the root, 0 on its left; the head keeps leftmost rightmost and root)"""
    head = h.alloc(0x34, bytes(0x34))
    h.uc.mem_write(head, _d(head) + _d(head) + _d(head))
    h.uc.mem_write(head + 0x31, b'\x01')
    nodes = {}
    for key in (1, 0):
        n = h.alloc(0x34, bytes(0x34))
        h.uc.mem_write(n, _d(head) + _d(head) + _d(head))
        h.uc.mem_write(n + 0xC, _d(key))
        nodes[key] = n
    h.uc.mem_write(nodes[1], _d(nodes[0]) + _d(head) + _d(head))
    h.uc.mem_write(nodes[0], _d(head) + _d(nodes[1]) + _d(head))
    h.uc.mem_write(head, _d(nodes[0]) + _d(nodes[1]) + _d(nodes[1]))
    return head, nodes


def test_number_cells(h):
    heap0 = h.heap_ptr
    try:
        cells = h.alloc(4, bytes(4))
        key_word = h.alloc(4, bytes(4))
        times = h.alloc(32, bytes(32))
        time_count = h.alloc(4, bytes(4))
        head, nodes = _cell_map(h)
        obj = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(obj + 0x74, _d(2))
        h.uc.mem_write(obj + 0x80, _d(0))
        h.uc.mem_write(obj + 0x84, _d(0))
        h.uc.mem_write(obj + 0x88, _d(0))
        h.uc.mem_write(obj + 0x8c, _d(head))
        h.uc.mem_write(obj + 0x90, _d(0))
        functor = _stub(h, b'\xA1' + _d(cells)                       # mov eax, [cells]
                          + b'\xFF\x05' + _d(cells)                 # inc dword [cells]
                          + b'\x8B\x44\x24\x08'                     # mov eax, [esp+8]  (x)
                          + b'\x03\x44\x24\x0C'                     # add eax, [esp+0xC] (y)
                          + b'\x83\xE0\x01'                         # and eax, 1
                          + b'\xA3' + _d(key_word)                  # mov [key_word], eax
                          + b'\xB8' + _d(key_word)                  # mov eax, key_word
                          + b'\xC2\x0C\x00')                        # ret 0xC
        h.uc.mem_write(obj + 0x4C, _d(functor))
        _hook(h, SET_TIME, b'\xA1' + _d(time_count)                 # mov eax, [time_count]
                            + b'\xC1\xE0\x03'                       # shl eax, 3
                            + b'\x05' + _d(times)                   # add eax, times
                            + b'\x89\x08'                           # mov [eax], ecx
                            + b'\x8B\x54\x24\x04'                   # mov edx, [esp+4]
                            + b'\x89\x50\x04'                       # mov [eax+4], edx
                            + b'\xFF\x05' + _d(time_count)          # inc dword [time_count]
                            + b'\xC2\x04\x00')                      # ret 4
        diffs = h.compare(NUMBER_CELLS, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(cells, bytes(4))
        h.uc.mem_write(time_count, bytes(4))
        h.uc.mem_write(times, bytes(32))
        for key in (0, 1):
            h.uc.mem_write(nodes[key] + 0x14, bytes(4))
            h.uc.mem_write(nodes[key] + 0x1C, b'\xAA')
        _call(h, NUMBER_CELLS, regs={UC_X86_REG_ECX: obj})
        if _u32(h, cells) != 11:
            return ['the functor mapped %d cells, want 11' % _u32(h, cells)]
        if _u32(h, time_count) != 2:
            return ['the time setter ran %d times, want 2' % _u32(h, time_count)]
        problems = []
        wants = (7.0 / 11.0, 4.0 / 11.0)
        for i, key in enumerate((0, 1)):
            at, value = struct.unpack('<II', h.uc.mem_read(times + i * 8, 8))
            if at != nodes[key] + 0x10:
                problems.append('entry %d is for %08X, want %08X' % (i, at, nodes[key] + 0x10))
            elif value != _bits(wants[i]):
                problems.append('entry %d holds %r, want %r' % (i, struct.unpack('<f', struct.pack('<I', value))[0], wants[i]))
            if h.uc.mem_read(nodes[key] + 0x1C, 1)[0] != 1:
                problems.append('node %d was not marked as hit' % key)
            if _u32(h, nodes[key] + 0x14):
                problems.append('node %d kept the weight %r' % (key, struct.unpack('<f', h.uc.mem_read(nodes[key] + 0x14, 4))[0]))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
