"""0x42B8D0 (record dispatch), 0x42B8F0 / 0x42B900 (destructor thunks), 0x42B910 (scene destructor),
0x42BAF0 (deleting destructor), 0x42BB10 (highlight kind), 0x42BB90 (troop selection) and 0x42BC70 (slot click)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

DISPATCH = 0x0042B8D0
THUNK_SCENE = 0x0042B8F0
THUNK_COLLECTOR = 0x0042B900
SCENE_DTOR = 0x0042B910
DELETING_DTOR = 0x0042BAF0
HIGHLIGHT_KIND = 0x0042BB10
SELECT_SLOT = 0x0042BB90
SLOT_CLICK = 0x0042BC70

HERO = 0x00425F60
BASE_DTOR = 0x004B2010
OP_DELETE = 0x005E3E9C
DISPATCH_FN = 0x006C8858
DISPATCH_OFFSET = 0x006C885C
CLASS_TABLE = 0x006BF684

SCENE_VTABLES = (0x0060888C, 0x0060886C, 0x00608848)

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, stub):
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    h.uc.ctl_remove_cache(target, target + 5)


def _callee_stub(h, log, value, pop, args):
    """logs ECX and the stack arguments, returns `value` and pops `pop` bytes"""
    code = b'\x89\x0D' + _dword(log)
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _cdecl_stub(h, log, value, pop, args):
    """cdecl variant: logs the stack arguments only"""
    code = b''
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _recorder(h, log, counter, extra):
    """thiscall one-argument recorder: [counter] entries of (ECX, argument); the argument also goes to `extra`"""
    code = b'\x8B\xC1'                                             # mov eax, ecx
    code += b'\x8B\x15' + _dword(counter)                           # mov edx, [counter]
    code += b'\x89\x04\x95' + _dword(log)                           # mov [edx*4+log], eax
    code += b'\x8B\x44\x24\x04' + b'\x89\x04\x95' + _dword(extra)   # the argument
    code += b'\x42' + b'\x89\x15' + _dword(counter)                 # inc edx; mov [counter], edx
    code += b'\x33\xC0' + b'\xC2\x04\x00'                           # xor eax, eax; ret 4
    return _stub(h, code)


def _float_recorder(h, log, counter, extra):
    """thiscall two-float-argument recorder: (ECX, x, y) in three parallel arrays at log, extra, extra+0x20"""
    code = b'\x8B\xC1'
    code += b'\x8B\x15' + _dword(counter)
    code += b'\x89\x04\x95' + _dword(log)
    code += b'\x8B\x44\x24\x04' + b'\x89\x04\x95' + _dword(extra)
    code += b'\x8B\x44\x24\x08' + b'\x89\x04\x95' + _dword(extra + 0x20)
    code += b'\x42' + b'\x89\x15' + _dword(counter)
    code += b'\x33\xC0' + b'\xC2\x08\x00'
    return _stub(h, code)


def test_dispatch_table(h):
    """record `index`'s function gets this plus the record's offset as its this and the argument on the stack"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x40, bytes(0x40))
        log = h.alloc(0x10, bytes(0x10))
        stub = _callee_stub(h, log, 0x5A5A, 4, 1)
        _patch(h, DISPATCH_FN + 8 * 2, _dword(stub))
        _patch(h, DISPATCH_OFFSET + 8 * 2, _dword(0x10))
        diffs = h.compare(DISPATCH, args=[2, 0x11223344], regs={UC_X86_REG_ECX: s}, ret=None)
        if diffs:
            return diffs
        h.call(DISPATCH, args=[2, 0x11223344], regs={UC_X86_REG_ECX: s})
        problems = []
        if _u32(h, log) != s + 0x10:
            problems.append('the function got this %#x' % _u32(h, log))
        if _u32(h, log + 4) != 0x11223344:
            problems.append('the function got %#x' % _u32(h, log + 4))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_destructor_thunks(h):
    """the +0x74 thunk subtracts 0x74, the +4 thunk 4, and both pass the free flag on"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x100, bytes(0x100))
        log_scene = h.alloc(0x10, bytes(0x10))
        log_collector = h.alloc(0x10, bytes(0x10))
        stub_scene = _callee_stub(h, log_scene, 0x5A5A, 4, 1)
        stub_collector = _callee_stub(h, log_collector, 0x5A5A, 4, 1)
        _hook(h, DELETING_DTOR, stub_scene)
        diffs = h.compare(THUNK_SCENE, args=[5], regs={UC_X86_REG_ECX: s + 0x74}, ret='eax')
        if diffs:
            return diffs
        h.call(THUNK_SCENE, args=[5], regs={UC_X86_REG_ECX: s + 0x74})
        _hook(h, DELETING_DTOR, stub_collector)
        diffs = h.compare(THUNK_COLLECTOR, args=[5], regs={UC_X86_REG_ECX: s + 4}, ret='eax')
        if diffs:
            return diffs
        h.call(THUNK_COLLECTOR, args=[5], regs={UC_X86_REG_ECX: s + 4})
        problems = []
        if _u32(h, log_scene) != s or _u32(h, log_scene + 4) != 5:
            problems.append('the +0x74 thunk gave %#x, %#x' % (_u32(h, log_scene), _u32(h, log_scene + 4)))
        if _u32(h, log_collector) != s or _u32(h, log_collector + 4) != 5:
            problems.append('the +4 thunk gave %#x, %#x' % (_u32(h, log_collector), _u32(h, log_collector + 4)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _destructor_setup(h, scene, objects, log, counter, flags):
    slots = [0x170 + 4 * i for i in range(11)] + [0x94, 0x98, 0x9c, 0x88, 0xa4, 0xdc, 0x10c, 0x130,
                                                  0x148, 0x154, 0xd0, 0x15c, 0x160, 0x16c]
    vtable = h.alloc(4, _dword(_recorder(h, log, counter, flags)))
    for off in slots:
        o = h.alloc(8, _dword(vtable))
        objects.append(o)
        h.uc.mem_write(scene + off, _dword(o))
    return slots


def test_scene_destructor(h):
    """every object slot is released once through its first vtable entry with 1; the 14 single slots are cleared (the
    eleven troop slots are left in place) and the base destructor runs"""
    heap0 = h.heap_ptr
    try:
        scene = h.alloc(0x1a0, bytes(0x1a0))
        objects = []
        log = h.alloc(0x80, bytes(0x80))
        flags = h.alloc(0x80, bytes(0x80))
        counter = h.alloc(4, bytes(4))
        base_log = h.alloc(4, bytes(4))
        slots = _destructor_setup(h, scene, objects, log, counter, flags)
        _hook(h, BASE_DTOR, _callee_stub(h, base_log, 0, 0, 0))
        diffs = h.compare(SCENE_DTOR, regs={UC_X86_REG_ECX: scene}, ret=None)
        if diffs:
            return diffs
        h.call(SCENE_DTOR, regs={UC_X86_REG_ECX: scene})
        problems = []
        if _u32(h, counter) != len(slots):
            problems.append('%d objects released' % _u32(h, counter))
        else:
            for i, o in enumerate(objects):
                if _u32(h, log + 4 * i) != o or _u32(h, flags + 4 * i) != 1:
                    problems.append('release %d got %#x, %d' % (i, _u32(h, log + 4 * i), _u32(h, flags + 4 * i)))
                    break
        for i, off in enumerate(slots):
            if _u32(h, scene + off) != (objects[i] if i < 11 else 0):
                problems.append('the slot +%#x holds %#x' % (off, _u32(h, scene + off)))
                break
        if _u32(h, scene) != SCENE_VTABLES[0] or _u32(h, scene + 4) != SCENE_VTABLES[1]:
            problems.append('the scene vtables are %#x, %#x' % (_u32(h, scene), _u32(h, scene + 4)))
        if _u32(h, scene + 0x74) != SCENE_VTABLES[2]:
            problems.append('the +0x74 vtable is %#x' % _u32(h, scene + 0x74))
        if _u32(h, base_log) != scene:
            problems.append('the base destructor got %#x' % _u32(h, base_log))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_deleting_destructor(h):
    """the object is released only when the free flag is set; this is returned either way"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x10, bytes(0x10))
        dtor_log = h.alloc(4, bytes(4))
        delete_log = h.alloc(4, bytes(4))
        _hook(h, SCENE_DTOR, _callee_stub(h, dtor_log, 0, 0, 0))
        _hook(h, OP_DELETE, _cdecl_stub(h, delete_log, 0, 0, 1))
        diffs = h.compare(DELETING_DTOR, args=[1], regs={UC_X86_REG_ECX: s}, ret='eax')
        if diffs:
            return diffs
        res = h.call(DELETING_DTOR, args=[1], regs={UC_X86_REG_ECX: s})
        problems = []
        if res['eax'] != s:
            problems.append('the result with the flag is %#x' % res['eax'])
        if _u32(h, dtor_log) != s:
            problems.append('the destructor got %#x' % _u32(h, dtor_log))
        if _u32(h, delete_log) != s:
            problems.append('the release got %#x' % _u32(h, delete_log))
        h.uc.mem_write(delete_log, bytes(4))
        diffs = h.compare(DELETING_DTOR, args=[0], regs={UC_X86_REG_ECX: s}, ret='eax')
        if diffs:
            return diffs
        res = h.call(DELETING_DTOR, args=[0], regs={UC_X86_REG_ECX: s})
        if res['eax'] != s:
            problems.append('the result without the flag is %#x' % res['eax'])
        if _u32(h, delete_log):
            problems.append('the object is released without the flag')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_highlight_kind(h):
    """the kind byte by the hero's class for ids 0..9 (0 by default); the id's upper 24 bits are kept"""
    heap0 = h.heap_ptr
    try:
        hero = h.alloc(0x1e0, bytes(0x1e0))
        _hook(h, HERO, _stub(h, b'\xB8' + _dword(hero) + b'\xC3'))
        wanted = {0: 0, 1: 4, 2: 7, 3: 7, 4: 7, 5: 9, 6: 9, 7: 9, 8: 9, 9: 10, 10: 0, 0x12345605: 0}
        problems = []
        for class_id, kind in wanted.items():
            h.uc.mem_write(hero + 0x1d8, _dword(class_id))
            diffs = h.compare(HIGHLIGHT_KIND, ret='eax')
            if diffs:
                return ['class %d: %s' % (class_id, d) for d in diffs]
            got = h.call(HIGHLIGHT_KIND)['eax']
            if got != (class_id & ~0xff | kind):
                problems.append('class %#x gives %#x' % (class_id, got))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _selection_setup(h):
    scene = h.alloc(0x180, bytes(0x180))
    level = h.alloc(0x30, bytes(0x30))
    mark = h.alloc(0x30, bytes(0x30))
    vtable = h.alloc(0xa0, bytes(0xa0))
    pics = [h.alloc(4, _dword(v)) for v in (0x11, 0x22, 0x33)]
    log34, extra34, counter34 = h.alloc(0x20, bytes(0x20)), h.alloc(0x20, bytes(0x20)), h.alloc(4, bytes(4))
    log6c = h.alloc(8, bytes(8))
    log94, extra94, counter94 = h.alloc(0x20, bytes(0x20)), h.alloc(0x40, bytes(0x40)), h.alloc(4, bytes(4))
    h.uc.mem_write(vtable + 0x34, _dword(_recorder(h, log34, counter34, extra34)))
    h.uc.mem_write(vtable + 0x6c, _dword(_callee_stub(h, log6c, 0, 4, 1)))
    h.uc.mem_write(vtable + 0x94, _dword(_float_recorder(h, log94, counter94, extra94)))
    h.uc.mem_write(level, _dword(vtable))
    h.uc.mem_write(mark, _dword(vtable))
    h.uc.mem_write(scene + 0xd0, _dword(level))
    h.uc.mem_write(scene + 0x164, _dword(mark))
    h.uc.mem_write(scene + 0x15c, _dword(pics[1]))
    h.uc.mem_write(scene + 0x160, _dword(pics[2]))
    for i in range(3):
        h.uc.mem_write(scene + 0xdc + 0xc * i, _dword(pics[i]))
    return scene, level, mark, pics, (log34, extra34, counter34), log6c, (log94, extra94, counter94)


def _hero_class(h, hero, class_id):
    _hook(h, HERO, _stub(h, b'\xB8' + _dword(hero) + b'\xC3'))     # ECX is not an argument of the getter
    h.uc.mem_write(hero + 0x1d8, _dword(class_id))


def test_troop_selection(h):
    """an allowed slot is stored, its picture and rectangle go to the level picture, and the hero-class picture is
    chosen for the mark (class 3 gives kind 7, so slot 2 shows the other picture)"""
    heap0 = h.heap_ptr
    try:
        scene, level, mark, pics, (log34, extra34, counter34), log6c, (log94, extra94, counter94) = \
            _selection_setup(h)
        hero = h.alloc(0x1e0, bytes(0x1e0))
        _hero_class(h, hero, 3)
        _patch(h, CLASS_TABLE, bytes(6) + struct.pack('<H', 1 << 2))
        diffs = h.compare(SELECT_SLOT, args=[2], regs={UC_X86_REG_ECX: scene}, ret=None)
        if diffs:
            return diffs
        h.call(SELECT_SLOT, args=[2], regs={UC_X86_REG_ECX: scene})
        problems = []
        if h.uc.mem_read(scene + 0x158, 1) != b'\x02':
            problems.append('the kind byte is %d' % h.uc.mem_read(scene + 0x158, 1)[0])
        if _u32(h, counter34) != 2:
            problems.append('%d picture switches' % _u32(h, counter34))
        else:
            if _u32(h, log34) != level or _u32(h, extra34) != pics[2]:
                problems.append('the level picture got %#x, %#x' % (_u32(h, log34), _u32(h, extra34)))
            if _u32(h, log34 + 4) != mark or _u32(h, extra34 + 4) != pics[2]:
                problems.append('the mark got %#x, %#x' % (_u32(h, log34 + 4), _u32(h, extra34 + 4)))
        if _u32(h, log6c) != level or _u32(h, log6c + 4) != scene + 0xd4 + 0x18:
            problems.append('the rectangle is %#x, %#x' % (_u32(h, log6c), _u32(h, log6c + 4)))
        if _u32(h, counter94) != 2:
            problems.append('%d position resets' % _u32(h, counter94))
        else:
            if _u32(h, log94) != level:
                problems.append('the first position reset is %#x' % _u32(h, log94))
            if _u32(h, log94 + 4) != mark:
                problems.append('the second position reset is %#x' % _u32(h, log94 + 4))
        if problems:
            return problems
        # slot 7 is the hero's own kind: the mark takes its class picture (+0x15C); logs start over
        h.uc.mem_write(scene + 0xdc + 0xc * 7, _dword(0x7766))
        _patch(h, CLASS_TABLE, bytes(6) + struct.pack('<H', 1 << 7))
        for p, n in ((log34, 0x20), (extra34, 0x20), (counter34, 4), (log6c, 8), (log94, 0x20), (extra94, 0x40),
                     (counter94, 4)):
            h.uc.mem_write(p, bytes(n))
        diffs = h.compare(SELECT_SLOT, args=[7], regs={UC_X86_REG_ECX: scene}, ret=None)
        if diffs:
            return diffs
        h.call(SELECT_SLOT, args=[7], regs={UC_X86_REG_ECX: scene})
        if _u32(h, extra34) != 0x7766:
            problems.append('the level picture is %#x' % _u32(h, extra34))
        if _u32(h, extra34 + 4) != pics[1]:
            problems.append('the mark took %#x' % _u32(h, extra34 + 4))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_troop_selection_denied(h):
    """a slot the hero's class does not allow changes nothing"""
    heap0 = h.heap_ptr
    try:
        scene, level, mark, pics, (log34, extra34, counter34), log6c, (log94, extra94, counter94) = \
            _selection_setup(h)
        hero = h.alloc(0x1e0, bytes(0x1e0))
        _hero_class(h, hero, 3)
        _patch(h, CLASS_TABLE, bytes(6) + struct.pack('<H', 1 << 4))
        diffs = h.compare(SELECT_SLOT, args=[2], regs={UC_X86_REG_ECX: scene}, ret=None)
        if diffs:
            return diffs
        h.call(SELECT_SLOT, args=[2], regs={UC_X86_REG_ECX: scene})
        problems = []
        if _u32(h, counter34) or _u32(h, counter94) or _u32(h, log6c):
            problems.append('a denied slot was shown')
        if h.uc.mem_read(scene + 0x158, 1) != b'\x00':
            problems.append('the kind byte is %d' % h.uc.mem_read(scene + 0x158, 1)[0])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_slot_click(h):
    """the click handler selects the kind at the item's +0x50"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x10, bytes(0x10))
        item = h.alloc(0x60, bytes(0x60))
        log = h.alloc(8, bytes(8))
        _hook(h, SELECT_SLOT, _callee_stub(h, log, 0, 4, 1))
        h.uc.mem_write(item + 0x50, b'\x07')
        diffs = h.compare(SLOT_CLICK, args=[item], regs={UC_X86_REG_ECX: s}, ret=None)
        if diffs:
            return diffs
        h.call(SLOT_CLICK, args=[item], regs={UC_X86_REG_ECX: s})
        problems = []
        if _u32(h, log) != s:
            problems.append('the selection got %#x' % _u32(h, log))
        if _u32(h, log + 4) != 7:
            problems.append('the selection kind is %d' % _u32(h, log + 4))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
