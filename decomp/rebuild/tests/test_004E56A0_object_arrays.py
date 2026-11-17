"""0x4E56A0 configured object-array initialization; configuration and object methods are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004E56A0
GET_GLOBAL = 0x00421510
FIND_CONFIG = 0x00424270
INIT_FIRST = 0x004E48B0
INIT_SECOND = 0x004E48F0
INIT_THIRD = 0x004E4B80
INIT_FOURTH = 0x004E4540
NEW_ARRAY = 0x005E3B10
DELETE_ARRAY = 0x005E3EBA
STR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
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


def _import(h, slot, symbol, code):
    stub = _stub(h, code)
    for address in (slot, h.symbols[symbol]):
        _patch(h, address, _dword(stub))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _log_ecx(log, offset):
    return b'\x89\x0D' + _dword(log + offset) + b'\xFF\x05' + _dword(log + offset + 4)


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _fixture(h):
    log = h.alloc(0xd0, bytes(0xd0))
    obj = h.alloc(0xb0, bytes(0xb0))
    old_array = h.alloc(0x20, bytes(0x20))
    new_array = h.alloc(0x1000, bytes(0x1000))
    second_array = h.alloc(0x20, bytes(0x20))
    global_object = h.alloc(0x10, bytes(0x10))
    config = h.alloc(0x200, bytes(0x200))

    setter = _stub(h, _log_ecx(log, 0x00) + _arg(4, log + 0x08) + _arg(8, log + 0x0c) +
                   b'\xC2\x08\x00')
    vtable = h.alloc(0x7c, bytes(0x7c))
    h.uc.mem_write(vtable + 0x78, _dword(setter))
    objects = [h.alloc(4, _dword(vtable)) for _ in range(4)]
    for i in range(2):
        h.uc.mem_write(new_array + i * 4, _dword(objects[i]))
        h.uc.mem_write(second_array + i * 4, _dword(objects[i + 2]))

    _import(h, STR_SLOT, STR_SYM, _log_ecx(log, 0x10) + _arg(4, log + 0x18) + b'\x8B\xC1\xC2\x04\x00')
    _import(h, STR_DTOR_SLOT, STR_DTOR_SYM, _log_ecx(log, 0x1c) + b'\xC3')
    _hook(h, GET_GLOBAL, b'\xFF\x05' + _dword(log + 0x24) + b'\xB8' + _dword(global_object) + b'\xC3')
    _hook(h, FIND_CONFIG, _log_ecx(log, 0x28) + _arg(4, log + 0x2c) + b'\xFF\x05' +
          _dword(log + 0x30) + b'\xB8' + _dword(config) + b'\xC2\x04\x00')
    _hook(h, DELETE_ARRAY, _arg(4, log + 0x34) + b'\xFF\x05' + _dword(log + 0x38) + b'\xC3')
    _hook(h, NEW_ARRAY, _arg(4, log + 0x3c) + b'\xFF\x05' + _dword(log + 0x40) +
          b'\xB8' + _dword(new_array) + b'\xC3')

    first = _log_ecx(log, 0x44) + _arg(4, log + 0x48) + b'\xFF\x05' + _dword(log + 0x4c)
    first += b'\xA1' + _dword(log + 0xc0) + b'\x89\x81\x88\x00\x00\x00'
    first += b'\xA1' + _dword(log + 0xc4) + b'\x89\x81\x9c\x00\x00\x00'
    first += b'\xA1' + _dword(log + 0xc8) + b'\x89\x81\x98\x00\x00\x00' + b'\xC2\x04\x00'
    _hook(h, INIT_FIRST, first)
    for target, offset in ((INIT_SECOND, 0x50), (INIT_THIRD, 0x5c), (INIT_FOURTH, 0x68)):
        _hook(h, target, _log_ecx(log, offset) + _arg(4, log + offset + 4) +
              b'\xFF\x05' + _dword(log + offset + 8) + b'\xC2\x04\x00')
    return log, obj, old_array, new_array, second_array, global_object, config, objects


def _check(h, fixture, first_count, second_count, with_old):
    log, obj, old_array, new_array, second_array, global_object, config, objects = fixture
    h.uc.mem_write(obj + 0x84, _dword(old_array if with_old else 0))
    h.uc.mem_write(obj + 0x88, _dword(0xDEADBEEF))
    h.uc.mem_write(obj + 0x98, _dword(0xDEADBEEF))
    h.uc.mem_write(obj + 0x9c, _dword(0xDEADBEEF))
    h.uc.mem_write(obj + 0x8c, _dword(_bits(1.25)))
    h.uc.mem_write(obj + 0x90, _dword(_bits(-2.5)))
    h.uc.mem_write(log + 0xc0, _dword(first_count))
    h.uc.mem_write(log + 0xc4, _dword(second_count))
    h.uc.mem_write(log + 0xc8, _dword(second_array))
    label = 'counts %d/%d old %d' % (first_count, second_count, with_old)
    diffs = h.compare(FN, regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]
    h.uc.mem_write(log, bytes(0xc0))
    result = h.call(FN, regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['%s: %s' % (label, result['fault'])]
    problems = []
    expected_fields = ((0x84, new_array), (0x88, first_count), (0x98, second_array), (0x9c, second_count))
    for offset, want in expected_fields:
        got = _u32(h, obj + offset)
        if got != want:
            problems.append('%s: field +%#x is %#x, want %#x' % (label, offset, got, want))
    calls = first_count + second_count
    if second_count:
        last = objects[2 + second_count - 1]
    elif first_count:
        last = objects[first_count - 1]
    else:
        last = 0
    expected = ((4, calls, 'setter calls'), (0, last, 'last setter object'),
                (8, _bits(1.25) if calls else 0, 'first float'), (0x0c, _bits(-2.5) if calls else 0, 'second float'),
                (0x14, 1, 'string constructor calls'), (0x18, 0x00612810, 'configuration literal'),
                (0x20, 1, 'string destructor calls'), (0x24, 1, 'global calls'),
                (0x28, global_object + 4, 'configuration container'), (0x30, 1, 'configuration lookups'),
                (0x34, old_array if with_old else 0, 'deleted array'), (0x38, int(with_old), 'delete calls'),
                (0x3c, 4000, 'array allocation size'), (0x40, 1, 'array allocations'),
                (0x44, obj, 'first initializer self'), (0x48, config + 0xd8, 'first config'), (0x4c, 1, 'first calls'),
                (0x50, obj, 'second initializer self'), (0x54, config + 0x118, 'second config'), (0x58, 1, 'second calls'),
                (0x5c, obj, 'third initializer self'), (0x60, config + 0x128, 'third config'), (0x64, 1, 'third calls'),
                (0x68, obj, 'fourth initializer self'), (0x6c, config + 0xac, 'fourth config'), (0x70, 1, 'fourth calls'))
    for offset, want, name in expected:
        got = _u32(h, log + offset)
        if got != want:
            problems.append('%s: %s is %#x, want %#x' % (label, name, got, want))
    return problems


def test_configured_object_arrays(h):
    heap0 = h.heap_ptr
    try:
        fixture = _fixture(h)
        problems = []
        for case in ((2, 2, True), (0, 0, False), (1, 0, False), (0, 1, False)):
            problems += _check(h, fixture, *case)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
