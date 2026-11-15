"""The volume tree plumbing at 0x427CE0..0x427F10: the two-map float hand-off (0x427CE0), the clamped setter
(0x427D70), the map key lookup (0x427DD0), the global Lua registration (0x427E40), the two iterator arrows
(0x427EA0/0x427EB0), the map reset (0x427EC0), the two-container destructor (0x427EF0) and the Lua setter
(0x427F10).

The volume objects are vtable stubs in the heap: slot 7 reads a float, slot 6 records the value it is told with."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

APPLY = 0x00427CE0
SET_VALUE = 0x00427D70
LUA_SET = 0x00427F10
UPPER_BOUND = 0x00427DD0
RESET_MAP = 0x00427EC0
ARROW_NEXT = 0x00427EA0
ARROW_PREV = 0x00427EB0
DESTROY = 0x00427EF0
REGISTER = 0x00427E40
CALLBACK = 0x00427A70

FREE_BLOCK = 0x005E3E9C
MAX_VALUE = 0x0068AE40
CONFIG_SLOT = 0x006C884C
LUA_STATE_SLOT = 0x008D122C

NEWSTATE = 0x00402870
PUSH_NUMBER = 0x004030A0
CREATETABLE = 0x004033D0
GETFIELD = 0x00403300

LUA_TLIGHTUSERDATA = 2
LUA_TTABLE = 5
LUA_TFUNCTION = 6

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


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


def _string(h, text):
    return h.alloc(len(text) + 1, text + b'\0')


def _map(h, children):
    """a map container: a self-linked head whose +0 chain visits the children (each node's +8 is its object)"""
    head = h.alloc(0x34, bytes(0x34))
    h.uc.mem_write(head, _dword(head) + _dword(head) + _dword(head))
    h.uc.mem_write(head + 0x31, b'\x01')
    previous = head
    for child in children:
        node = h.alloc(0x34, bytes(0x34))
        h.uc.mem_write(node, _dword(head))
        h.uc.mem_write(node + 8, _dword(child))
        h.uc.mem_write(previous, _dword(node))
        previous = node
    return head


def _unit(h):
    """an object the tree walks: virtual +0x1C returns its float, +0x18 records (float, 1) at this+0x2C"""
    log = h.alloc(16, bytes(16))
    value = h.alloc(4, bytes(4))
    getter = _stub(h, b'\xB8' + _dword(value) + b'\xD9\x00\xC3')      # mov eax, value; flds [eax]; ret
    setter = _stub(h, b'\xBA' + _dword(log)                           # mov edx, log
                      + b'\x89\x0A'                                   # mov [edx], ecx
                      + b'\xD9\x44\x24\x04'                           # fld dword [esp+4]
                      + b'\xD9\x5A\x04'                               # fstp dword [edx+4]
                      + b'\x8B\x44\x24\x08'                           # mov eax, [esp+8]
                      + b'\x89\x42\x08'                               # mov [edx+8], eax
                      + b'\xFF\x42\x0C'                               # inc dword [edx+0xC]
                      + b'\xC2\x08\x00')                              # ret 8
    table = h.alloc(32, bytes(32))
    h.uc.mem_write(table + 0x18, _dword(setter))
    h.uc.mem_write(table + 0x1C, _dword(getter))
    obj = h.alloc(0x30, bytes(0x30))
    h.uc.mem_write(obj, _dword(table))
    return {'unit': obj, 'log': log, 'value': value}


def _load(h, unit, value):
    h.uc.mem_write(unit['value'], struct.pack('<f', value))
    h.uc.mem_write(unit['unit'] + 0x2C, struct.pack('<f', value))
    h.uc.mem_write(unit['log'], bytes(16))


def _check(h, unit, old, new):
    problems = []
    if _f32(h, unit['unit'] + 0x2C) != new:
        problems.append('unit %08X holds %r, want %r' % (unit['unit'], _f32(h, unit['unit'] + 0x2C), new))
    own, told, flag, count = struct.unpack('<IfII', h.uc.mem_read(unit['log'], 16))
    if count != 1:
        problems.append('the setter of %08X ran %d times' % (unit['unit'], count))
    elif own != unit['unit']:
        problems.append('the setter got %08X, want %08X' % (own, unit['unit']))
    elif told != old or flag != 1:
        problems.append('the setter was told %r/%d, want %r/1' % (told, flag, old))
    return problems


def _holder(h, units, children=()):
    holder = h.alloc(0x18, bytes(0x18))
    h.uc.mem_write(holder + 4, _dword(_map(h, [u['unit'] for u in units])))
    h.uc.mem_write(holder + 0x10, _dword(_map(h, [c['holder'] for c in children])))
    return holder


def test_apply_float_tree(h):
    heap0 = h.heap_ptr
    try:
        outer = [_unit(h) for _ in range(3)]
        inner = [_unit(h) for _ in range(2)]
        child = {'holder': None}
        child['holder'] = _holder(h, inner)
        holder = _holder(h, outer, [child])
        for unit, value in zip(outer, (1.5, -2.25, 8.0)):
            _load(h, unit, value)
        for unit, value in zip(inner, (4.0, 6.5)):
            _load(h, unit, value)
        diffs = h.compare(APPLY, args=(_bits(0.75),), regs={UC_X86_REG_ECX: holder,
                                                            UC_X86_REG_EAX: 0xDEADBEEF}, ret=None)
        if diffs:
            return diffs
        for unit, value in zip(outer, (1.5, -2.25, 8.0)):
            _load(h, unit, value)
        for unit, value in zip(inner, (4.0, 6.5)):
            _load(h, unit, value)
        _call(h, APPLY, args=(_bits(0.75),), regs={UC_X86_REG_ECX: holder, UC_X86_REG_EAX: 0xDEADBEEF})
        problems = []
        for unit, value in zip(outer, (1.5, -2.25, 8.0)):
            problems += _check(h, unit, value, 0.75)
        for unit, value in zip(inner, (4.0, 6.5)):
            problems += _check(h, unit, value, 0.75)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_apply_float_empty(h):
    heap0 = h.heap_ptr
    try:
        holder = _holder(h, [])
        diffs = h.compare(APPLY, args=(_bits(3.0),), regs={UC_X86_REG_ECX: holder,
                                                           UC_X86_REG_EAX: 0}, ret=None)
        return diffs or None
    finally:
        h.heap_ptr = heap0


def _volume_object(h, units):
    obj = h.alloc(0xAC, bytes(0xAC))
    h.uc.mem_write(obj + 0x9C, _dword(_map(h, [u['unit'] for u in units])))
    h.uc.mem_write(obj + 0xA8, _dword(_map(h, [])))
    return obj


def test_set_value(h):
    heap0 = h.heap_ptr
    old_slot = bytes(h.uc.mem_read(CONFIG_SLOT, 4))
    try:
        maximum = _f32(h, MAX_VALUE)
        unit = _unit(h)
        _load(h, unit, 2.5)
        obj = _volume_object(h, [unit])
        config = h.alloc(0x98, bytes(0x98))

        def setup(h):
            h.uc.mem_write(CONFIG_SLOT, _dword(config))

        cases = [(-1.0, 0.0), (0.0, 0.0), (maximum * 0.5, maximum * 0.5), (maximum, maximum),
                 (maximum * 2.0, maximum)]
        for value, want in cases:
            _load(h, unit, 2.5)
            h.uc.mem_write(config + 0x90, bytes(4))
            h.uc.mem_write(CONFIG_SLOT, bytes(4))
            diffs = h.compare(SET_VALUE, args=(_bits(value),), regs={UC_X86_REG_ECX: obj,
                                                                    UC_X86_REG_EAX: 0x33},
                              setup=setup, ret=None)
            if diffs:
                return ['value %r: %s' % (value, d) for d in diffs]
            _load(h, unit, 2.5)
            h.uc.mem_write(config + 0x90, bytes(4))
            h.uc.mem_write(CONFIG_SLOT, _dword(config))
            _call(h, SET_VALUE, args=(_bits(value),), regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x33})
            problems = _check(h, unit, 2.5, want)
            if _f32(h, obj + 0x94) != want:
                problems.append('value %r: +0x94 is %r' % (value, _f32(h, obj + 0x94)))
            if _f32(h, config + 0x90) != want:
                problems.append('value %r: the config keeps %r' % (value, _f32(h, config + 0x90)))
            if problems:
                return problems
        return None
    finally:
        h.uc.mem_write(CONFIG_SLOT, old_slot)
        _restore(h)
        h.heap_ptr = heap0


def _bst(h):
    head = h.alloc(0x34, bytes(0x34))
    h.uc.mem_write(head, _dword(head) + _dword(head) + _dword(head))
    h.uc.mem_write(head + 0x31, b'\x01')
    nodes = {}

    def node(key):
        n = h.alloc(0x34, bytes(0x34))
        h.uc.mem_write(n, _dword(head) + _dword(head) + _dword(head))
        h.uc.mem_write(n + 0xC, _dword(key))
        nodes[key] = n
        return n

    root = node(20)
    node(10)
    node(5)
    node(15)
    node(30)
    node(25)
    node(40)
    h.uc.mem_write(nodes[20], _dword(nodes[10]) + _dword(head) + _dword(nodes[30]))
    h.uc.mem_write(nodes[10], _dword(nodes[5]) + _dword(nodes[20]) + _dword(nodes[15]))
    h.uc.mem_write(nodes[5], _dword(head) + _dword(nodes[10]) + _dword(head))
    h.uc.mem_write(nodes[15], _dword(head) + _dword(nodes[10]) + _dword(head))
    h.uc.mem_write(nodes[30], _dword(nodes[25]) + _dword(nodes[20]) + _dword(nodes[40]))
    h.uc.mem_write(nodes[25], _dword(head) + _dword(nodes[30]) + _dword(head))
    h.uc.mem_write(nodes[40], _dword(head) + _dword(nodes[30]) + _dword(head))
    h.uc.mem_write(head + 4, _dword(root))
    return head, nodes


def test_upper_bound(h):
    heap0 = h.heap_ptr
    try:
        head, nodes = _bst(h)
        container = h.alloc(8, bytes(8))
        h.uc.mem_write(container + 4, _dword(head))
        out = h.alloc(4, b'\xCC' * 4)
        cases = [(0, head), (5, nodes[5]), (6, head), (10, nodes[10]), (11, head),
                 (20, nodes[20]), (26, head), (30, nodes[30]), (40, nodes[40]), (41, head), (0xFFFFFFFF, head)]
        for key, want in cases:
            key_ptr = h.alloc(4, _dword(key))
            diffs = h.compare(UPPER_BOUND, args=(out, key_ptr), regs={UC_X86_REG_ECX: container},
                              ret='eax')
            if diffs:
                return ['key %d: %s' % (key, d) for d in diffs]
            h.uc.mem_write(out, b'\xCC' * 4)
            res = _call(h, UPPER_BOUND, args=(out, key_ptr), regs={UC_X86_REG_ECX: container})
            if _u32(h, out) != want:
                return ['key %d: found %08X, want %08X' % (key, _u32(h, out), want)]
            if res['eax'] != out:
                return ['key %d: returned %08X, want the out slot %08X' % (key, res['eax'], out)]
        return None
    finally:
        h.heap_ptr = heap0


def test_reset_map(h):
    heap0 = h.heap_ptr
    try:
        obj = h.alloc(0xC, bytes(0xC))
        diffs = h.compare(RESET_MAP, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        _call(h, RESET_MAP, regs={UC_X86_REG_ECX: obj})
        head = _u32(h, obj + 4)
        if not head:
            return ['no head']
        if h.uc.mem_read(head + 0x31, 1)[0] != 1:
            return ['the head is not marked nil']
        links = struct.unpack('<III', h.uc.mem_read(head, 12))
        if links[0] != head or links[1] != head or links[2] != head:
            return ['the head links to %08X/%08X/%08X' % links]
        if _u32(h, obj + 8):
            return ['the count is %d' % _u32(h, obj + 8)]
        return None
    finally:
        h.heap_ptr = heap0


def _step(h, entry, slot, start, want):
    h.uc.mem_write(slot, _dword(start))
    diffs = h.compare(entry, regs={UC_X86_REG_ECX: slot}, ret='eax')
    if diffs:
        return diffs
    h.uc.mem_write(slot, _dword(start))
    res = _call(h, entry, regs={UC_X86_REG_ECX: slot})
    if _u32(h, slot) != want:
        return ['from %08X moved to %08X, want %08X' % (start, _u32(h, slot), want)]
    if res['eax'] != slot:
        return ['returned %08X, want the iterator %08X' % (res['eax'], slot)]
    return None


def test_iterator_next(h):
    heap0 = h.heap_ptr
    try:
        head, nodes = _bst(h)
        slot = h.alloc(4, bytes(4))
        plan = [(nodes[5], nodes[10]), (nodes[10], nodes[15]), (nodes[15], nodes[20]),
                (nodes[20], nodes[25]), (nodes[25], nodes[30]), (nodes[30], nodes[40]),
                (nodes[40], head), (head, head)]
        for start, want in plan:
            problems = _step(h, ARROW_NEXT, slot, start, want)
            if problems:
                return problems
        return None
    finally:
        h.heap_ptr = heap0


def test_iterator_prev(h):
    heap0 = h.heap_ptr
    try:
        head, nodes = _bst(h)
        slot = h.alloc(4, bytes(4))
        plan = [(nodes[40], nodes[30]), (nodes[30], nodes[25]), (nodes[25], nodes[20]),
                (nodes[20], nodes[15]), (nodes[15], nodes[10]), (nodes[10], nodes[5]),
                (nodes[5], head), (head, head)]
        for start, want in plan:
            problems = _step(h, ARROW_PREV, slot, start, want)
            if problems:
                return problems
        return None
    finally:
        h.heap_ptr = heap0


def test_destroy_pair(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(24, bytes(24))
        count = h.alloc(4, bytes(4))
        _hook(h, FREE_BLOCK, b'\x8B\x0D' + _dword(count)              # mov ecx, [count]
                                + b'\x8B\x44\x24\x04'                 # mov eax, [esp+4]
                                + b'\x89\x04\x8D' + _dword(log)       # mov [log+ecx*4], eax
                                + b'\xFF\x05' + _dword(count)         # inc dword [count]
                                + b'\xB8\x00\x00\x00\x00'             # mov eax, 0
                                + b'\xC3')                            # ret
        obj = h.alloc(0x14, bytes(0x14))
        heads, nodes = [], []
        for offset in (0, 0xC):
            head = h.alloc(0x34, bytes(0x34))
            free_node = h.alloc(0x34, bytes(0x34))
            h.uc.mem_write(head, _dword(free_node) + _dword(head))
            h.uc.mem_write(free_node, _dword(head))
            h.uc.mem_write(obj + offset + 4, _dword(head))
            heads.append(head)
            nodes.append(free_node)
        diffs = h.compare(DESTROY, regs={UC_X86_REG_ECX: obj}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(count, bytes(4))
        h.uc.mem_write(log, bytes(24))
        for offset in (0, 0xC):
            head = heads[offset // 0xC]
            free_node = nodes[offset // 0xC]
            h.uc.mem_write(head, _dword(free_node) + _dword(head))
            h.uc.mem_write(free_node, _dword(head))
            h.uc.mem_write(obj + offset + 4, _dword(head))
        _call(h, DESTROY, regs={UC_X86_REG_ECX: obj})
        got = _u32(h, count)
        if got != 4:
            return ['the block delete ran %d times, want 4' % got]
        order = struct.unpack('<4I', h.uc.mem_read(log, 16))
        want = (nodes[1], heads[1], nodes[0], heads[0])
        if order != want:
            return ['freed %s, want %s' % (['%08X' % x for x in order], ['%08X' % x for x in want])]
        if _u32(h, obj + 4) or _u32(h, obj + 0x10):
            return ['the containers still point at %08X/%08X' % (_u32(h, obj + 4), _u32(h, obj + 0x10))]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _state(h):
    state = _call(h, NEWSTATE)['eax']
    h.uc.mem_write(LUA_STATE_SLOT, _dword(state))
    return state


def test_register_globals(h):
    heap0 = h.heap_ptr
    old_slot = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    try:
        alpha = _string(h, b'alpha')
        beta = _string(h, b'beta')
        entries = h.alloc(0x30, bytes(0x30))
        h.uc.mem_write(entries, _dword(alpha))
        h.uc.mem_write(entries + 0x10, _dword(beta))

        def setup(h):
            state = _state(h)
            _call(h, CREATETABLE, args=(state, 0, 0))

        diffs = h.compare(REGISTER, args=(entries,), setup=setup, ret=None)
        if diffs:
            return diffs
        setup(h)
        state = _u32(h, LUA_STATE_SLOT)
        _call(h, REGISTER, args=(entries,))
        top = _u32(h, state + 8)
        kind = _u32(h, top - 4)
        if kind != LUA_TTABLE:
            return ['the stack top is kind %d, want the table' % kind]
        for name, record in ((alpha, entries), (beta, entries + 0x10)):
            _call(h, GETFIELD, args=(state, -1, name))
            top = _u32(h, state + 8)
            closure, kind = struct.unpack('<II', h.uc.mem_read(top - 8, 8))
            h.uc.mem_write(state + 8, _dword(top - 8))       # pop the value so the table stays on top
            if kind != LUA_TFUNCTION:
                return ['%s is kind %d' % (name, kind)]
            is_c = h.uc.mem_read(closure + 6, 1)[0]
            nup = h.uc.mem_read(closure + 7, 1)[0]
            f = _u32(h, closure + 0x10)
            up_value, up_kind = struct.unpack('<II', h.uc.mem_read(closure + 0x14, 8))
            if is_c != 1 or nup != 1 or f != CALLBACK:
                return ['%s: \'%s\' closure is %d/%d with %08X' % (name, name, is_c, nup, f)]
            if up_value != record or up_kind != LUA_TLIGHTUSERDATA:
                return ['%s: upvalue %08X of kind %d, want record %08X' % (name, up_value, up_kind, record)]
        return None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old_slot)
        _restore(h)
        h.heap_ptr = heap0


def test_lua_set(h):
    heap0 = h.heap_ptr
    old_slot = bytes(h.uc.mem_read(LUA_STATE_SLOT, 4))
    old_config = bytes(h.uc.mem_read(CONFIG_SLOT, 4))
    try:
        maximum = _f32(h, MAX_VALUE)
        unit = _unit(h)
        obj = _volume_object(h, [unit])
        config = h.alloc(0x98, bytes(0x98))
        args = h.alloc(0x14, bytes(0x14))
        cases = [(-2.0, 0.0), (0.0, 0.0), (maximum * 0.5, maximum * 0.5), (maximum * 2.0, maximum)]
        for value, want in cases:
            _load(h, unit, 3.0)

            def setup(h):
                state = _state(h)
                _call(h, PUSH_NUMBER, args=(state, _bits(value)))
                h.uc.mem_write(CONFIG_SLOT, _dword(config))

            h.uc.mem_write(CONFIG_SLOT, bytes(4))
            h.uc.mem_write(config + 0x90, bytes(4))
            diffs = h.compare(LUA_SET, args=(args,), regs={UC_X86_REG_ECX: obj}, setup=setup,
                              ret='eax')
            if diffs:
                return ['value %r: %s' % (value, d) for d in diffs]
            _load(h, unit, 3.0)
            h.uc.mem_write(CONFIG_SLOT, bytes(4))
            h.uc.mem_write(config + 0x90, bytes(4))
            setup(h)
            res = _call(h, LUA_SET, args=(args,), regs={UC_X86_REG_ECX: obj})
            problems = _check(h, unit, 3.0, want)
            if res['eax'] != 0:
                problems.append('value %r: returned %d' % (value, res['eax']))
            if _f32(h, obj + 0x94) != want:
                problems.append('value %r: +0x94 is %r' % (value, _f32(h, obj + 0x94)))
            if _f32(h, config + 0x90) != want:
                problems.append('value %r: the config keeps %r' % (value, _f32(h, config + 0x90)))
            if problems:
                return problems
        return None
    finally:
        h.uc.mem_write(LUA_STATE_SLOT, old_slot)
        h.uc.mem_write(CONFIG_SLOT, old_config)
        _restore(h)
        h.heap_ptr = heap0
