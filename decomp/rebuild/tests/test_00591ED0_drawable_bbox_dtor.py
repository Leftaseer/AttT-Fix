"""0x591ED0 DrawableBBox destructor; editor unregister, vector release, delete, and base dtor are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00591ED0
UNREGISTER = 0x005ADCC0
RELEASE_RANGE = 0x004E1BF0
DELETE = 0x005E3E9C
BASE_DTOR = 0x004AD020
EDITOR_PTR = 0x006C88D8
VTABLE = 0x0061F6F4
saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _hook(h, target, code):
    stub = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(stub, stub + len(code))
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


def _range_code(log):
    return (b'\xA3' + _dword(log + 0x10)                         # mov [eax out], eax
            + b'\x8B\x05' + _dword(log + 0x0c)                  # mov eax, [count]
            + b'\x8B\x54\x24\x04'                               # first
            + b'\x89\x14\x85' + _dword(log + 0x20)
            + b'\x8B\x54\x24\x08'                               # last
            + b'\x89\x14\x85' + _dword(log + 0x28)
            + b'\x8B\x54\x24\x0C'                               # vector
            + b'\x89\x14\x85' + _dword(log + 0x30)
            + b'\x8B\x54\x24\x10'                               # owner
            + b'\x89\x14\x85' + _dword(log + 0x38)
            + b'\xFF\x05' + _dword(log + 0x0c)
            + b'\xC3')


def _delete_code(log):
    return (b'\x8B\x05' + _dword(log + 0x14)
            + b'\x8B\x54\x24\x04'
            + b'\x89\x14\x85' + _dword(log + 0x40)
            + b'\xFF\x05' + _dword(log + 0x14)
            + b'\xC3')


def _case(h, log, editor, enabled):
    obj = h.alloc(0x220, bytes(0x220))
    first_begin = h.alloc(0x30, bytes(0x30))
    second_begin = h.alloc(0x30, bytes(0x30))
    h.uc.mem_write(editor + 0x40, bytes([enabled]))
    h.uc.mem_write(obj + 0x1c4, _dword(obj + 0x1c4))
    h.uc.mem_write(obj + 0x1c8, _dword(first_begin))
    h.uc.mem_write(obj + 0x1cc, _dword(first_begin + 0x18))
    h.uc.mem_write(obj + 0x1d0, _dword(first_begin + 0x30))
    h.uc.mem_write(obj + 0x1d4, _dword(obj + 0x1d4))
    h.uc.mem_write(obj + 0x1d8, _dword(second_begin))
    h.uc.mem_write(obj + 0x1dc, _dword(second_begin + 0x18))
    h.uc.mem_write(obj + 0x1e0, _dword(second_begin + 0x30))

    diffs = h.compare(FN, regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
    if diffs:
        return ['enabled %d: %s' % (enabled, d) for d in diffs]
    h.uc.mem_write(log, bytes(0x50))
    result = h.call(FN, regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['enabled %d: %s' % (enabled, result['fault'])]

    problems = []
    expected = ((0x00, editor if enabled else 0, 'editor self'),
                (0x04, int(enabled), 'editor unregister calls'),
                (0x08, obj if enabled else 0, 'unregistered object'),
                (0x0c, 2, 'range-release calls'), (0x14, 2, 'delete calls'),
                (0x18, obj, 'base destructor self'), (0x1c, 1, 'base destructor calls'))
    for offset, want, label in expected:
        got = _u32(h, log + offset)
        if got != want:
            problems.append('enabled %d: %s is %#x, want %#x' % (enabled, label, got, want))
    vectors = (obj + 0x1d4, obj + 0x1c4)
    begins = (second_begin, first_begin)
    for index in range(2):
        checks = ((0x20 + index * 4, begins[index], 'range first %d' % index),
                  (0x28 + index * 4, begins[index] + 0x18, 'range last %d' % index),
                  (0x40 + index * 4, begins[index], 'deleted block %d' % index))
        for offset, want, label in checks:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('enabled %d: %s is %#x, want %#x' % (enabled, label, got, want))
    if _u32(h, log + 0x10) != first_begin:
        problems.append('enabled %d: EAX range argument is wrong' % enabled)
    if _u32(h, obj) != h.to_rebuilt(VTABLE) or _u32(h, obj + 0x1bc) != 0:
        problems.append('enabled %d: object fields are wrong' % enabled)
    for vector in vectors:
        if _u32(h, vector + 4) or _u32(h, vector + 8) or _u32(h, vector + 0x0c):
            problems.append('enabled %d: vector %#x was not cleared' % (enabled, vector))
    return problems


def test_drawable_bbox_dtor(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x50, bytes(0x50))
        editor = h.alloc(0x50, bytes(0x50))
        _patch(h, EDITOR_PTR, _dword(editor))
        _hook(h, UNREGISTER, _log_ecx(log, 0x00) + _arg(4, log + 0x08) + b'\xC2\x04\x00')
        _hook(h, RELEASE_RANGE, _range_code(log))
        _hook(h, DELETE, _delete_code(log))
        _hook(h, BASE_DTOR, _log_ecx(log, 0x18) + b'\xC3')

        problems = []
        for enabled in (0, 1):
            problems += _case(h, log, editor, enabled)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
