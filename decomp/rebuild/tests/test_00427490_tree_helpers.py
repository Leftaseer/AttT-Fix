"""std::map tree machinery at 0x427490..0x427770:
0x00427490 / 0x004274B0 (cdecl): follow +8 / +0 links while they are not the head; return the last real node.
0x004275D0 (ECX): the pointer at +4 plus 4.
0x004275E0 (ECX, ret 4): the lookup probe below the head's +4 (keys at +0xC, unsigned).
0x00427610 / 0x00427660 (ECX, ret 4): the two rotations.
0x004276C0 / 0x00427720 (ECX): advance the iterator slot in place.
0x00427770 (cdecl): 12-byte element copy.  Nodes: +0, +4 parent, +8, +0x31 the head/nil flag."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

NODE = 0x38
FLAG = 0x31

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _restore(h):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()


def _mknode(h, links):
    """links: dict offset -> value (offset 0x31 is a byte)"""
    p = h.alloc(NODE, bytes(NODE))
    _fillnode(h, p, links)
    return p


def _fillnode(h, p, links):
    h.uc.mem_write(p, bytes(NODE))
    for off, value in links.items():
        if off == FLAG:
            h.uc.mem_write(p + off, bytes([value]))
        else:
            h.uc.mem_write(p + off, _dword(value))


def test_min_max(h):
    heap0 = h.heap_ptr
    try:
        head = _mknode(h, {FLAG: 1})
        mid = _mknode(h, {8: head, 0: head})
        top = _mknode(h, {8: mid, 0: mid})
        cases = [(0x00427490, top, mid), (0x00427490, mid, mid), (0x004274B0, top, mid),
                 (0x004274B0, mid, mid)]
        for entry, n, want in cases:
            diffs = h.compare(entry, args=[n], ret='eax')
            if diffs:
                return ['%08X(%08X): %s' % (entry, n, d) for d in diffs]
            res = h.call(entry, args=[n])
            if res['fault']:
                return ['%08X: replacement faulted: %s' % (entry, res['fault'])]
            if res['eax'] != want:
                return ['%08X: returned %08X instead of %08X' % (entry, res['eax'], want)]
        return None
    finally:
        h.heap_ptr = heap0


def test_004275D0(h):
    obj = h.alloc(0x10, bytes(0x10))
    target = h.alloc(0x20, b'\xEE' * 0x20)
    h.uc.mem_write(obj + 4, _dword(target))
    diffs = h.compare(0x004275D0, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x004275D0, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % (res['fault'],)]
    if res['eax'] != target + 4:
        return ['returned %08X' % res['eax']]
    return None


def test_004275E0(h):
    heap0 = h.heap_ptr
    try:
        head = _mknode(h, {FLAG: 1})
        a = _mknode(h, {4: head, 0: head, 8: head})
        b = _mknode(h, {4: a, 0: head, 8: head})
        h.uc.mem_write(a + 0xc, _dword(10))
        h.uc.mem_write(b + 0xc, _dword(20))
        h.uc.mem_write(head + 4, _dword(a))
        key = h.alloc(4, _dword(15))
        tree = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(tree + 4, _dword(head))

        def probe(k):
            node, last, nxt = head, head, _u32(h, head + 4)
            if h.uc.mem_read(nxt + FLAG, 1)[0]:
                return node
            while True:
                node = nxt
                if _u32(h, node + 0xc) < k:
                    nxt = _u32(h, node + 8)
                    node = last
                else:
                    nxt = _u32(h, node)
                last = node
                if h.uc.mem_read(nxt + FLAG, 1)[0]:
                    return node

        for k in (15, 25, 5, 20):
            h.uc.mem_write(key, _dword(k))
            _fillnode(h, a, {4: head, 0: b, 8: head})
            h.uc.mem_write(a + 0xc, _dword(10))
            expected = probe(k)
            diffs = h.compare(0x004275E0, args=[key], regs={UC_X86_REG_ECX: tree}, ret='eax')
            if diffs:
                return ['key %d: %s' % (k, d) for d in diffs]
            h.uc.mem_write(key, _dword(k))
            _fillnode(h, a, {4: head, 0: b, 8: head})
            h.uc.mem_write(a + 0xc, _dword(10))
            res = h.call(0x004275E0, args=[key], regs={UC_X86_REG_ECX: tree})
            if res['fault']:
                return ['key %d: replacement faulted: %s' % (k, res['fault'])]
            if res['eax'] != expected:
                return ['key %d: returned %08X instead of %08X' % (k, res['eax'], expected)]
        return None
    finally:
        h.heap_ptr = heap0


def _rotation_case(h, entry, up, down, branch, deep):
    """Builds: tree object -> head (+4 = root); root -> up child -> [down real child]; returns (tree, node)."""
    head = _mknode(h, {FLAG: 1})
    parent = _mknode(h, {4: head})
    node = _mknode(h, {4: parent})
    child = _mknode(h, {4: node})
    inner = _mknode(h, {4: child})
    _fillnode(h, node, {up: child, down: head, 4: parent})
    _fillnode(h, child, {down: inner if deep else head, 4: node})
    _fillnode(h, inner, {up: head, down: head, 4: child})
    if branch == 'root':
        _fillnode(h, parent, {4: head})
        h.uc.mem_write(head + 4, _dword(node))
    else:
        link = down if branch == 'left' else up
        _fillnode(h, parent, {4: head, link: node})
        h.uc.mem_write(head + 4, _dword(parent))
    tree = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(tree + 4, _dword(head))
    return tree, node


def test_rotations(h):
    heap0 = h.heap_ptr
    try:
        for entry, up, down in ((0x00427610, 8, 0), (0x00427660, 0, 8)):
            for branch in ('root', 'left', 'right'):
                for deep in (False, True):
                    tree, node = _rotation_case(h, entry, up, down, branch, deep)
                    diffs = h.compare(entry, args=[node], regs={UC_X86_REG_ECX: tree}, ret=None)
                    if diffs:
                        return ['%08X/%s/%s: %s' % (entry, branch, deep, d) for d in diffs]
                    tree, node = _rotation_case(h, entry, up, down, branch, deep)
                    child = _u32(h, node + up)
                    parent = _u32(h, node + 4)
                    head = _u32(h, tree + 4)
                    res = h.call(entry, args=[node], regs={UC_X86_REG_ECX: tree})
                    if res['fault']:
                        return ['%08X/%s/%s: replacement faulted: %s' % (entry, branch, deep, res['fault'])]
                    if _u32(h, node + 4) != child or _u32(h, child + down) != node:
                        return ['%08X/%s/%s: the node was not adopted by the raised child' % (entry, branch, deep)]
                    if branch == 'root':
                        if _u32(h, head + 4) != child:
                            return ['%08X/root: the head does not point at the raised child' % (entry,)]
                    else:
                        link = down if branch == 'left' else up
                        if _u32(h, parent + link) != child:
                            return ['%08X/%s: the parent link is %08X instead of %08X'
                                    % (entry, branch, _u32(h, parent + link), child)]
        return None
    finally:
        h.heap_ptr = heap0


def test_iterators(h):
    heap0 = h.heap_ptr
    try:
        # descend: a real child whose own back link reaches the head through a real grandchild
        for entry, child_off, back_off in ((0x004276C0, 0, 8), (0x00427720, 8, 0)):
            head = _mknode(h, {FLAG: 1})
            node = _mknode(h, {4: head})
            child = _mknode(h, {4: node})
            grand = _mknode(h, {4: child})
            _fillnode(h, node, {child_off: child, back_off: head, 4: head})
            _fillnode(h, child, {back_off: grand, 4: node})
            _fillnode(h, grand, {back_off: head, child_off: head, 4: child})
            slot = h.alloc(4, _dword(node))
            diffs = h.compare(entry, regs={UC_X86_REG_ECX: slot}, ret=None)
            if diffs:
                return ['%08X/descend: %s' % (entry, d) for d in diffs]
            h.uc.mem_write(slot, _dword(node))
            res = h.call(entry, regs={UC_X86_REG_ECX: slot})
            if res['fault']:
                return ['%08X/descend: replacement faulted: %s' % (entry, res['fault'])]
            if _u32(h, slot) != grand:
                return ['%08X/descend: the iterator is %08X instead of %08X' % (entry, _u32(h, slot), grand)]
            # climb: the child link is the head; the node is its real parent's back link
            head = _mknode(h, {FLAG: 1})
            parent = _mknode(h, {4: head})
            node = _mknode(h, {4: parent})
            _fillnode(h, node, {child_off: head, back_off: head, 4: parent})
            # the climb test compares the node with the parent's child link (the +0 one when advancing)
            _fillnode(h, parent, {4: head, child_off: node})
            h.uc.mem_write(head + 4, _dword(parent))
            slot = h.alloc(4, _dword(node))
            diffs = h.compare(entry, regs={UC_X86_REG_ECX: slot}, ret=None)
            if diffs:
                return ['%08X/climb: %s' % (entry, d) for d in diffs]
            h.uc.mem_write(slot, _dword(node))
            res = h.call(entry, regs={UC_X86_REG_ECX: slot})
            if res['fault']:
                return ['%08X/climb: replacement faulted: %s' % (entry, res['fault'])]
            if _u32(h, slot) != head:
                return ['%08X/climb: the iterator is %08X instead of %08X' % (entry, _u32(h, slot), head)]
            # past the end: the slot holds the head
            slot = h.alloc(4, _dword(head))
            diffs = h.compare(entry, regs={UC_X86_REG_ECX: slot}, ret=None)
            if diffs:
                return ['%08X/head: %s' % (entry, d) for d in diffs]
        return None
    finally:
        h.heap_ptr = heap0



def test_00427770(h):
    heap0 = h.heap_ptr
    try:
        src = h.alloc(0x40, bytes(range(0x40)))
        dest = h.alloc(0x40, b'\xEE' * 0x40)
        diffs = h.compare(0x00427770, args=[src, src + 0x18, dest], ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(dest, b'\xEE' * 0x40)
        res = h.call(0x00427770, args=[src, src + 0x18, dest])
        if res['fault']:
            return ['replacement faulted: %s' % (res['fault'],)]
        if res['eax'] != dest + 0x18:
            return ['returned %08X' % res['eax']]
        if bytes(h.uc.mem_read(dest, 0x18)) != bytes(range(0x18)):
            return ['the copy is %r' % (bytes(h.uc.mem_read(dest, 0x18)),)]
        if bytes(h.uc.mem_read(dest + 0x18, 0x28)) != b'\xEE' * 0x28:
            return ['bytes past the copy changed']
        # an empty range with a null dest: no iteration at all
        diffs = h.compare(0x00427770, args=[src, src, 0], ret='eax')
        if diffs:
            return ['empty/null dest: %s' % d for d in diffs]
        res = h.call(0x00427770, args=[src, src, 0])
        if res['fault']:
            return ['empty/null dest: replacement faulted: %s' % (res['fault'],)]
        if res['eax'] != 0:
            return ['empty/null dest: returned %08X' % res['eax']]
        return None
    finally:
        h.heap_ptr = heap0
