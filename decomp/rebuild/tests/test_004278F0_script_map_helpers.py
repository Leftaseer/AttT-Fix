"""Script callbacks and map plumbing around 0x4278F0: the float hand-off callback (0x4278F0), the container front
read (0x427980), the map lower bound (0x427A40), the map node allocator (0x427C00), the map node deleting
destructor (0x427C40) and the two-map clear (0x427C70).

0x4278F0 pushes its float through the engine's Lua state (0x004030A0), so that test installs a fresh state in
0x008D122C.  The allocator and clear tests hook operator new 0x005E3EAE and the block delete 0x005E3E9C."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

LUA_STATE_SLOT = 0x008D122C

NEWSTATE = 0x00402870
GETTOP = 0x00402A60
OPERATOR_NEW = 0x005E3EAE
FREE_BLOCK = 0x005E3E9C

CALLBACK_PUSH = 0x004278F0
FRONT_READ = 0x00427980
MAP_LOWER_BOUND = 0x00427A40
MAP_NODE_NEW = 0x00427C00
MAP_NODE_DELETE = 0x00427C40
MAP_CLEAR = 0x00427C70

OBJECT_VTABLE = 0x00607C88

LUA_TNUMBER = 3

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _byte(h, addr):
    return h.uc.mem_read(addr, 1)[0]


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


def _fields(h, addr, count):
    return struct.unpack('<%dI' % count, h.uc.mem_read(addr, 4 * count))


def _state(h):
    """a fresh Lua state installed in the engine's global"""
    state = _call(h, NEWSTATE)['eax']
    h.uc.mem_write(LUA_STATE_SLOT, _dword(state))
    return state


def _top(h, state):
    return _call(h, GETTOP, args=(state,))['eax']


def test_callback_pushes_float(h):
    heap0 = h.heap_ptr
    old = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    try:
        obj = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(obj + 0x94, struct.pack('<f', 12.5))

        def setup(h):
            _state(h)

        diffs = h.compare(CALLBACK_PUSH, args=(0,), regs={UC_X86_REG_ECX: obj}, setup=setup, ret='eax')
        if diffs:
            return diffs
        setup(h)
        state = _u32(h, LUA_STATE_SLOT)
        res = h.call(CALLBACK_PUSH, args=(0,), regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != 1 or _top(h, state) != 1:
            return ['reported %d with %d values pushed' % (res['eax'], _top(h, state))]
        value, kind = struct.unpack('<fI', h.uc.mem_read(_u32(h, state + 8) - 8, 8))
        if value != 12.5 or kind != LUA_TNUMBER:
            return ['pushed %r of kind %d' % (value, kind)]
        return None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old)
        _restore(h)
        h.heap_ptr = heap0


def test_front_read(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0x10, bytes(0x10))
        block = h.alloc(0x10, _dword(0xCAFEBABE) + bytes(0xC))
        out = h.alloc(4, b'\xEE' * 4)
        h.uc.mem_write(obj + 4, _dword(block))
        diffs = h.compare(FRONT_READ, args=(out,), regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(out, b'\xEE' * 4)
        _call(h, FRONT_READ, args=(out,), regs={UC_X86_REG_ECX: obj})
        if _u32(h, out) != 0xCAFEBABE:
            return ['the front is %08X' % _u32(h, out)]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _node(h, key, left, right):
    n = h.alloc(0x38, bytes(0x38))
    h.uc.mem_write(n, _dword(left) + _dword(n) + _dword(right) + _dword(key))
    return n


def test_map_lower_bound(h):
    heap0 = h.heap_ptr
    try:
        nil = h.alloc(0x38, bytes(0x38))
        h.uc.mem_write(nil, _dword(nil) + _dword(nil) + _dword(nil))
        h.uc.mem_write(nil + 0x31, b'\x01')
        left = _node(h, 5, nil, nil)
        right = _node(h, 20, nil, nil)
        root = _node(h, 10, left, right)
        head = h.alloc(0x38, bytes(0x38))
        h.uc.mem_write(head, _dword(head) + _dword(root) + _dword(head))
        h.uc.mem_write(head + 0x31, b'\x01')
        obj = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(obj + 4, _dword(head))
        out = h.alloc(4, b'\xEE' * 4)
        key = h.alloc(4, bytes(4))

        def want(k):
            node, p = head, _u32(h, head + 4)
            if not _byte(h, p + 0x31):
                while True:
                    if _u32(h, p + 0xc) < k:
                        p = _u32(h, p + 8)
                    else:
                        node, p = p, _u32(h, p)
                    if _byte(h, p + 0x31):
                        break
            return node

        for k in (0, 3, 5, 7, 10, 15, 20, 25, 0xFFFFFFFF):
            h.uc.mem_write(key, _dword(k))
            h.uc.mem_write(out, b'\xEE' * 4)
            diffs = h.compare(MAP_LOWER_BOUND, args=(out, key), regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['key %d: %s' % (k, d) for d in diffs]
            h.uc.mem_write(out, b'\xEE' * 4)
            _call(h, MAP_LOWER_BOUND, args=(out, key), regs={UC_X86_REG_ECX: obj})
            if _u32(h, out) != want(k):
                return ['key %d: outbound node %08X, want %08X' % (k, _u32(h, out), want(k))]

        h.uc.mem_write(head + 4, _dword(head))                       # an empty map
        h.uc.mem_write(key, _dword(10))
        diffs = h.compare(MAP_LOWER_BOUND, args=(out, key), regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return ['empty: %s' % d for d in diffs]
        h.uc.mem_write(out, b'\xEE' * 4)
        _call(h, MAP_LOWER_BOUND, args=(out, key), regs={UC_X86_REG_ECX: obj})
        if _u32(h, out) != head:
            return ['empty: outbound node %08X, want the head %08X' % (_u32(h, out), head)]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_map_node_new(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x10, bytes(0x10))
        block = h.alloc(0x34, bytes(0x34))
        _hook(h, OPERATOR_NEW,
              b'\xFF\x05' + _dword(log)
              + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4)
              + b'\xB8' + _dword(block)
              + b'\xC3')

        def setup(h):
            h.uc.mem_write(log, bytes(0x10))
            h.uc.mem_write(block, b'\xEE' * 0x34)

        diffs = h.compare(MAP_NODE_NEW, setup=setup, ret='eax')
        if diffs:
            return diffs
        setup(h)
        res = h.call(MAP_NODE_NEW)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['eax'] != block or _u32(h, log) != 1 or _u32(h, log + 4) != 0x34:
            return ['returned %08X after %d news of %X' % (res['eax'], _u32(h, log), _u32(h, log + 4))]
        got = _fields(h, block, 3)
        if got != (0, 0, 0):
            return ['links (%08X, %08X, %08X)' % got]
        if _byte(h, block + 0x30) != 1 or _byte(h, block + 0x31) != 0:
            return ['flags %02X/%02X' % (_byte(h, block + 0x30), _byte(h, block + 0x31))]
        if h.uc.mem_read(block + 0xc, 0x24) != b'\xEE' * 0x24:
            return ['bytes between the links and the flags changed']
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_map_node_delete(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x10, bytes(0x10))
        _hook(h, FREE_BLOCK,
              b'\xFF\x05' + _dword(log)
              + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + 4)
              + b'\xC3')
        obj = h.alloc(0x20, bytes(0x20))

        def setup(h):
            h.uc.mem_write(log, bytes(0x10))
            h.uc.mem_write(obj, bytes(0x20))

        for flags in (0, 1, 2, 3):
            setup(h)
            diffs = h.compare(MAP_NODE_DELETE, args=(flags,), regs={UC_X86_REG_ECX: obj},
                              setup=setup, ret=None)
            if diffs:
                return ['flags %d: %s' % (flags, d) for d in diffs]
            setup(h)
            res = h.call(MAP_NODE_DELETE, args=(flags,), regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['flags %d: replacement faulted: %s' % (flags, res['fault'])]
            if res['eax'] != obj or _u32(h, obj) != OBJECT_VTABLE:
                return ['flags %d: returned %08X, vtable %08X' % (flags, res['eax'], _u32(h, obj))]
            want = 1 if flags & 1 else 0
            if _u32(h, log) != want or (want and _u32(h, log + 4) != obj):
                return ['flags %d: the delete ran %d times for %08X'
                        % (flags, _u32(h, log), _u32(h, log + 4))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_map_clear(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        _hook(h, FREE_BLOCK,
              b'\x8B\x44\x24\x04'                                # the block
              + b'\x8B\x0D' + _dword(log)                        # its index
              + b'\x89\x04\x8D' + _dword(log + 4)                # log it
              + b'\xFF\x05' + _dword(log)                        # ++index
              + b'\xC3')
        obj = h.alloc(0x20, bytes(0x20))
        nodes = [h.alloc(0x38, bytes(0x38)) for _ in range(5)]
        head1 = h.alloc(0x38, bytes(0x38))
        head2 = h.alloc(0x38, bytes(0x38))

        def setup(h):
            h.uc.mem_write(log, bytes(0x40))
            h.uc.mem_write(obj, bytes(0x20))
            h.uc.mem_write(obj + 4, _dword(head1))
            h.uc.mem_write(obj + 8, _dword(3))
            h.uc.mem_write(obj + 0x10, _dword(head2))
            h.uc.mem_write(obj + 0x14, _dword(2))
            h.uc.mem_write(head1, _dword(nodes[0]) + _dword(0x11111111))
            h.uc.mem_write(head1 + 0x31, b'\x01')
            h.uc.mem_write(nodes[0], _dword(nodes[1]))
            h.uc.mem_write(nodes[1], _dword(nodes[2]))
            h.uc.mem_write(nodes[2], _dword(head1))
            h.uc.mem_write(head2, _dword(nodes[3]) + _dword(0x22222222))
            h.uc.mem_write(head2 + 0x31, b'\x01')
            h.uc.mem_write(nodes[3], _dword(nodes[4]))
            h.uc.mem_write(nodes[4], _dword(head2))

        diffs = h.compare(MAP_CLEAR, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
        if diffs:
            return diffs
        setup(h)
        res = h.call(MAP_CLEAR, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log) != 5:
            return ['%d blocks deleted' % _u32(h, log)]
        order = [_u32(h, log + 4 + i * 4) for i in range(5)]
        want = [nodes[0], nodes[1], nodes[2], nodes[3], nodes[4]]
        if order != want:
            return ['deleted %s, want %s' % (['%08X' % p for p in order], ['%08X' % p for p in want])]
        if _fields(h, head1, 2) != (head1, head1) or _fields(h, head2, 2) != (head2, head2):
            return ['the heads were not unlinked (%08X, %08X), (%08X, %08X)'
                    % (_fields(h, head1, 2) + _fields(h, head2, 2))]
        if _u32(h, obj + 8) != 0 or _u32(h, obj + 0x14) != 0:
            return ['counts (%d, %d) after the clear' % (_u32(h, obj + 8), _u32(h, obj + 0x14))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0
