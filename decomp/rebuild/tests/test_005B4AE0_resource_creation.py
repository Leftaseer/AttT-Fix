"""0x5B4AE0 named-resource creation; allocation, strings, container and interfaces are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x005B4AE0
OPERATOR_NEW = 0x005E3EAE
NEW_ARRAY = 0x005E3B10
RESOURCE_CTOR = 0x004DF920
CONTAINER_ADD = 0x005B4A50
STR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


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
    log = h.alloc(0x80, bytes(0x80))
    obj = h.alloc(0x40, bytes(0x40))
    resource = h.alloc(0x54, bytes(0x54))
    key_buffer = h.alloc(0x40, bytes(0x40))
    interface = h.alloc(0x20, bytes(0x20))
    name = h.alloc(0x20, b'resource-name\0')
    key = h.alloc(0x20, b'resource-key\0')

    name_size = _stub(h, _log_ecx(log, 0x34) + b'\xA1' + _dword(log + 0x60) + b'\xC3')
    resource_vtable = h.alloc(0x34, bytes(0x34))
    h.uc.mem_write(resource_vtable + 0x30, _dword(name_size))
    h.uc.mem_write(resource, _dword(resource_vtable))

    register = _stub(h, _arg(4, log + 0x40) + _arg(8, log + 0x44) + _arg(0x0c, log + 0x48) +
                     b'\xFF\x05' + _dword(log + 0x4c) + b'\xA1' + _dword(log + 0x64) +
                     b'\xC2\x0C\x00')
    find = _stub(h, _arg(4, log + 0x50) + _arg(8, log + 0x54) + _arg(0x0c, log + 0x58) +
                 b'\xFF\x05' + _dword(log + 0x5c) + b'\xB8' + _dword(interface) + b'\xC2\x0C\x00')
    manager_vtable = h.alloc(0xd4, bytes(0xd4))
    h.uc.mem_write(manager_vtable + 0x28, _dword(find))
    h.uc.mem_write(manager_vtable + 0xd0, _dword(register))
    manager = h.alloc(4, _dword(manager_vtable))
    h.uc.mem_write(obj + 0x18, _dword(manager))

    _import(h, STR_SLOT, STR_SYM, _log_ecx(log, 0x00) + _arg(4, log + 0x08) + b'\x8B\xC1\xC2\x04\x00')
    _import(h, STR_DTOR_SLOT, STR_DTOR_SYM, _log_ecx(log, 0x0c) + b'\xC3')
    _hook(h, OPERATOR_NEW, _arg(4, log + 0x14) + b'\xFF\x05' + _dword(log + 0x18) +
          b'\xB8' + _dword(resource) + b'\xC3')
    _hook(h, NEW_ARRAY, _arg(4, log + 0x1c) + b'\xFF\x05' + _dword(log + 0x20) +
          b'\xB8' + _dword(key_buffer) + b'\xC3')
    _hook(h, RESOURCE_CTOR, _log_ecx(log, 0x24) + _arg(4, log + 0x28) + _arg(8, log + 0x2c) +
          b'\xFF\x05' + _dword(log + 0x30) + b'\xB8' + _dword(resource) + b'\xC2\x08\x00')
    _hook(h, CONTAINER_ADD, b'\x89\x0D' + _dword(log + 0x68) + b'\xFF\x05' + _dword(log + 0x78) +
          _arg(4, log + 0x74) + b'\x8B\x00\xA3' + _dword(log + 0x6c) +
          b'\x8B\x44\x24\x04\x8B\x40\x04\xA3' + _dword(log + 0x70) + b'\xC2\x04\x00')
    return log, obj, resource, key_buffer, interface, name, key, manager


def _check(h, fixture, status):
    log, obj, resource, key_buffer, interface, name, key, manager = fixture
    h.uc.mem_write(obj + 0x20, bytes(0x10))
    h.uc.mem_write(obj + 0x24, _dword(0xDEADBEEF))
    h.uc.mem_write(log + 0x60, _dword(0x12345678))
    h.uc.mem_write(log + 0x64, _dword(status))
    h.uc.mem_write(key_buffer, bytes(0x40))
    label = 'status %d' % status
    diffs = h.compare(FN, args=(name, key), regs={UC_X86_REG_ECX: obj}, ret='eax', mem=False)
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]
    h.uc.mem_write(log, bytes(0x60))
    h.uc.mem_write(log + 0x68, bytes(0x18))
    result = h.call(FN, args=(name, key), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['%s: %s' % (label, result['fault'])]
    problems = []
    if result['eax'] != status & 0xFFFFFFFF:
        problems.append('%s: result is %#x' % (label, result['eax']))
    success = status >= 0
    expected = ((0x04, 1, 'string constructor calls'), (0x08, name, 'string name'),
                (0x10, 1, 'string destructor calls'), (0x14, 0x54, 'resource allocation size'),
                (0x18, 1, 'resource allocations'), (0x1c, len(b'resource-key\0'), 'key allocation size'),
                (0x20, 1, 'key allocations'), (0x24, resource, 'resource constructor self'),
                (0x2c, 0, 'resource constructor flag'), (0x30, 1, 'resource constructor calls'),
                (0x34, resource, 'name-size object'), (0x38, 1, 'name-size calls'),
                (0x40, manager, 'registration manager'), (0x44, key_buffer, 'registered key'),
                (0x48, 0x12345678, 'registered name size'), (0x4c, 1, 'registration calls'),
                (0x50, manager if success else 0, 'interface manager'), (0x54, 0, 'interface flag'),
                (0x58, 0x00620B04 if success else 0, 'interface name'), (0x5c, int(success), 'interface calls'),
                (0x68, obj + 4 if success else 0, 'container'), (0x6c, resource if success else 0, 'container object'),
                (0x70, key_buffer if success else 0, 'container key'), (0x78, int(success), 'container calls'))
    for offset, want, label_name in expected:
        got = _u32(h, log + offset)
        if got != want:
            problems.append('%s: %s is %#x, want %#x' % (label, label_name, got, want))
    if _u32(h, obj + 0x20) != resource:
        problems.append('%s: resource field was not stored' % label)
    want_interface = interface if success else 0xDEADBEEF
    if _u32(h, obj + 0x24) != want_interface:
        problems.append('%s: interface field is wrong' % label)
    if bytes(h.uc.mem_read(key_buffer, len(b'resource-key\0'))) != b'resource-key\0':
        problems.append('%s: copied key is wrong' % label)
    return problems


def test_named_resource_creation(h):
    heap0 = h.heap_ptr
    try:
        fixture = _fixture(h)
        problems = []
        for status in (0, 7, -1):
            problems += _check(h, fixture, status)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
