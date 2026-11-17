"""0x424F20 visible-control collection and mouse picking; virtual methods and ray/sort helpers are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00424F20
RAY = 0x00424A90
SORT_SMALL = 0x005084E0
SORT_LARGE = 0x005085E0
saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _log_ecx(log, offset):
    return b'\x89\x0D' + _dword(log + offset) + b'\xFF\x05' + _dword(log + offset + 4)


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _fixture(h, positions, visible, hits, slot_count, empty_slots, with_old):
    log = h.alloc(0x100, bytes(0x100))
    obj = h.alloc(0x80, bytes(0x80))
    scene = h.alloc(0x680, bytes(0x680))
    camera = h.alloc(0x50, bytes(0x50))
    entries = h.alloc(max(8, 8 * len(positions)), bytes(max(8, 8 * len(positions))))
    slots = h.alloc(max(4, 4 * slot_count), bytes(max(4, 4 * slot_count)))
    head = h.alloc(0x0c, bytes(0x0c))
    h.uc.mem_write(head, _dword(head))

    callbacks = _stub(h, _log_ecx(log, 0x00) + b'\xB8' + _dword(0x11223344) + b'\xC3')
    release = _stub(h, _log_ecx(log, 0x08) + b'\xB8' + _dword(0x22334455) + b'\xC3')
    addref = _stub(h, _log_ecx(log, 0x10) + b'\xB8' + _dword(0x33445566) + b'\xC3')
    is_visible = _stub(h, _log_ecx(log, 0x18) + b'\x0F\xB6\x41\x04\xC3')
    position = _stub(h, _log_ecx(log, 0x20) + b'\x8B\x41\x08\xC3')
    hit = _stub(h, _log_ecx(log, 0x28) + _arg(4, log + 0x30) + _arg(8, log + 0x34) +
                b'\x0F\xB6\x41\x0C\xC2\x08\x00')
    vtable = h.alloc(0x1c, bytes(0x1c))
    for offset, target in ((4, callbacks), (8, addref), (0x0c, release),
                           (0x10, position), (0x14, is_visible), (0x18, hit)):
        h.uc.mem_write(vtable + offset, _dword(target))

    old = h.alloc(0x10, _dword(vtable)) if with_old else 0
    controls = []
    previous = head
    for i, coords in enumerate(positions):
        p = h.alloc(0x0c, struct.pack('<fff', *coords))
        control = h.alloc(0x10, _dword(vtable))
        h.uc.mem_write(control + 4, bytes([visible[i]]))
        h.uc.mem_write(control + 8, _dword(p))
        h.uc.mem_write(control + 0x0c, bytes([hits[i]]))
        node = h.alloc(0x0c, bytes(0x0c))
        h.uc.mem_write(previous, _dword(node))
        h.uc.mem_write(node + 8, _dword(control))
        controls.append(control)
        previous = node
    h.uc.mem_write(previous, _dword(head))

    for i in empty_slots:
        h.uc.mem_write(slots + 4 * i, bytes(4))
    for i in range(slot_count):
        if i not in empty_slots:
            h.uc.mem_write(slots + 4 * i, _dword(0x60000000 + i))
    h.uc.mem_write(scene + 0x66c, _dword(slots))
    h.uc.mem_write(scene + 0x670, _dword(slot_count))
    for i, value in enumerate((0.5, 1.0, 1.0)):
        h.uc.mem_write(camera + 0x44 + 4 * i, _dword(_bits(value)))
    h.uc.mem_write(obj + 0x38, _dword(old))
    h.uc.mem_write(obj + 0x40, _dword(head))
    h.uc.mem_write(obj + 0x48, _dword(scene))
    h.uc.mem_write(obj + 0x50, _dword(camera))
    h.uc.mem_write(obj + 0x58, _dword(entries))
    h.uc.mem_write(obj + 0x5c, _dword(0xFFFFFFFF))

    _hook(h, SORT_SMALL, _log_ecx(log, 0x50) + b'\xB8' + _dword(0x44556677) + b'\xC3')
    _hook(h, SORT_LARGE, _log_ecx(log, 0x58) + _arg(4, log + 0x60) + _arg(8, log + 0x64) +
          b'\xB8' + _dword(0x55667788) + b'\xC2\x08\x00')
    ray = _log_ecx(log, 0x68) + _arg(4, log + 0x70) + _arg(8, log + 0x74)
    for arg_offset, values in ((4, (2.0, 3.0, 4.0)), (8, (5.0, 6.0, 7.0))):
        ray += b'\x8B\x44\x24' + bytes([arg_offset])
        for i, value in enumerate(values):
            ray += b'\xC7\x40' + bytes([4 * i]) + _dword(_bits(value))
    ray += b'\xB8' + _dword(0x66778899) + b'\xC2\x08\x00'
    _hook(h, RAY, ray)
    return log, obj, scene, entries, controls, old


def _run(h, fixture):
    log, obj = fixture[:2]
    diffs = h.compare(FN, args=(0x12345678,), regs={UC_X86_REG_ECX: obj}, ret='eax', mem=False)
    if diffs:
        return None, diffs
    h.uc.mem_write(log, bytes(0x100))
    result = h.call(FN, args=(0x12345678,), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return result, [result['fault']]
    return result, []


def _check_log(h, log, offset, count, last, label, problems):
    if _u32(h, log + offset + 4) != count or (count and _u32(h, log + offset) != last):
        problems.append('%s: callback log at %#x is (%#x, %d), want (%#x, %d)' % (
            label, offset, _u32(h, log + offset), _u32(h, log + offset + 4), last, count))


def test_control_picking_hit(h):
    heap0 = h.heap_ptr
    try:
        fixture = _fixture(h, [(1.0, 2.0, 3.0), (2.0, 3.0, 4.0)], [1, 1], [0, 1],
                           3, [0, 2], True)
        log, obj, scene, entries, controls, old = fixture
        result, problems = _run(h, fixture)
        if result is None:
            return problems
        if result['eax'] != 0x33445566:
            problems.append('hit: addref result is %#x' % result['eax'])
        if _u32(h, obj + 0x38) != controls[1] or _u32(h, obj + 0x5c) != 2:
            problems.append('hit: hovered control or visible count is wrong')
        for i, distance in enumerate((5.25, 15.25)):
            if _u32(h, entries + i * 8) != controls[i] or _u32(h, entries + i * 8 + 4) != _bits(distance):
                problems.append('hit: distance entry %d is wrong' % i)
        _check_log(h, log, 0x00, 2, old, 'empty-slot callbacks', problems)
        _check_log(h, log, 0x08, 1, old, 'old release', problems)
        _check_log(h, log, 0x10, 1, controls[1], 'new addref', problems)
        _check_log(h, log, 0x18, 2, controls[1], 'visibility', problems)
        _check_log(h, log, 0x20, 2, controls[1], 'positions', problems)
        _check_log(h, log, 0x28, 2, controls[1], 'hit tests', problems)
        _check_log(h, log, 0x50, 1, obj + 0x54, 'small sort', problems)
        _check_log(h, log, 0x58, 0, 0, 'large sort', problems)
        _check_log(h, log, 0x68, 1, obj, 'ray setup', problems)
        for offset, value in ((0x30, 2.0), (0x34, 5.0)):
            if _u32(h, log + offset) == 0:
                problems.append('hit: ray arguments were not forwarded')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_control_picking_miss_and_empty(h):
    heap0 = h.heap_ptr
    try:
        problems = []
        miss = _fixture(h, [(1.0, 2.0, 3.0)], [1], [0], 2, [], True)
        log, obj, scene, entries, controls, old = miss
        result, diffs = _run(h, miss)
        if diffs:
            return diffs
        if _u32(h, obj + 0x38) != 0:
            problems.append('miss: hovered control was not cleared')
        _check_log(h, log, 0x00, 0, 0, 'miss empty-slot callbacks', problems)
        _check_log(h, log, 0x08, 1, old, 'miss old release', problems)
        _check_log(h, log, 0x28, 1, controls[0], 'miss hit tests', problems)

        _restore(h)
        h.heap_ptr = heap0
        empty = _fixture(h, [], [], [], 0, [], False)
        log, obj, scene = empty[:3]
        result, diffs = _run(h, empty)
        if diffs:
            return diffs
        if result['eax'] != scene:
            problems.append('empty: return value is %#x, want scene %#x' % (result['eax'], scene))
        if _u32(h, obj + 0x5c) != 0:
            problems.append('empty: visible count was not cleared')
        _check_log(h, log, 0x50, 0, 0, 'empty small sort', problems)
        _check_log(h, log, 0x68, 0, 0, 'empty ray setup', problems)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_control_picking_large_sort(h):
    heap0 = h.heap_ptr
    try:
        count = 39
        positions = [(float(i), float(i + 1), float(i + 2)) for i in range(count)]
        fixture = _fixture(h, positions, [1] * count, [0] * count, 1, [], False)
        log, obj = fixture[:2]
        result, problems = _run(h, fixture)
        if result is None:
            return problems
        if _u32(h, obj + 0x5c) != count:
            problems.append('large: visible count is wrong')
        _check_log(h, log, 0x50, 0, 0, 'large small sort', problems)
        _check_log(h, log, 0x58, 1, obj + 0x54, 'large sort', problems)
        if _u32(h, log + 0x60) != 0 or _u32(h, log + 0x64) != count - 1:
            problems.append('large: quicksort bounds are wrong')
        _check_log(h, log, 0x28, count, fixture[4][-1], 'large hit tests', problems)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
