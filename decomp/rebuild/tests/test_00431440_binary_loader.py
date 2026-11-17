"""0x431440 binary object loader; std::fstream imports and the object reader are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00431440
READ_OBJECT = 0x004313A0
CSTR_SLOT = 0x0060732C
CTOR_SLOT = 0x00607194
FAIL_SLOT = 0x00607198
DTOR_SLOT = 0x0060719C
CSTR_SYM = '__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ'
CTOR_SYM = '__imp_??0?$basic_fstream@DU?$char_traits@D@std@@@std@@QAE@PBDHH@Z'
FAIL_SYM = '__imp_?fail@ios_base@std@@QBE_NXZ'
DTOR_SYM = '__imp_??_D?$basic_fstream@DU?$char_traits@D@std@@@std@@QAEXXZ'
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
    log = h.alloc(0x60, bytes(0x60))
    obj = h.alloc(0x40, bytes(0x40))
    path = h.alloc(0x1c, bytes(0x1c))
    text = h.alloc(0x20, b'objects.bin\0')
    descriptor = h.alloc(8, bytes(8))
    h.uc.mem_write(descriptor + 4, _dword(0x20))

    _import(h, CSTR_SLOT, CSTR_SYM, _log_ecx(log, 0x00) + b'\xA1' + _dword(log + 0x40) + b'\xC3')
    _import(h, CTOR_SLOT, CTOR_SYM, _log_ecx(log, 0x08) + _arg(4, log + 0x10) +
            _arg(8, log + 0x14) + _arg(0x0c, log + 0x18) + _arg(0x10, log + 0x1c) +
            b'\xC7\x01' + _dword(descriptor) + b'\x8B\xC1\xC2\x10\x00')
    _import(h, FAIL_SLOT, FAIL_SYM, _log_ecx(log, 0x20) + b'\xA1' + _dword(log + 0x44) + b'\xC3')
    _import(h, DTOR_SLOT, DTOR_SYM, _log_ecx(log, 0x28) + b'\xC3')
    _hook(h, READ_OBJECT, _log_ecx(log, 0x30) + _arg(4, log + 0x38) +
          b'\xA1' + _dword(log + 0x48) + b'\xC2\x04\x00')
    return log, obj, path, text


def _check(h, fixture, fail, read_result):
    log, obj, path, text = fixture
    h.uc.mem_write(log + 0x40, _dword(text))
    h.uc.mem_write(log + 0x44, _dword(fail))
    h.uc.mem_write(log + 0x48, _dword(read_result))
    label = 'fail %d read %d' % (fail, read_result)
    diffs = h.compare(FN, args=(path,), regs={UC_X86_REG_ECX: obj}, ret='al', mem=False)
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]
    h.uc.mem_write(log, bytes(0x40))
    result = h.call(FN, args=(path,), regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['%s: %s' % (label, result['fault'])]
    problems = []
    want = 0 if fail else read_result
    if result['eax'] & 0xFF != want:
        problems.append('%s: result is %#x, want %#x' % (label, result['eax'] & 0xFF, want))
    expected = ((0, path, 'path'), (4, 1, 'c_str calls'), (0x0c, 1, 'constructor calls'),
                (0x10, text, 'filename'), (0x14, 0x22, 'open mode'), (0x18, 0x40, 'shared mode'),
                (0x1c, 1, 'constructor flag'), (0x24, 1, 'fail calls'), (0x2c, 1, 'destructor calls'),
                (0x30, obj if not fail else 0, 'reader object'), (0x34, int(not fail), 'reader calls'))
    for offset, value, name in expected:
        got = _u32(h, log + offset)
        if got != value:
            problems.append('%s: %s is %#x, want %#x' % (label, name, got, value))
    stream = _u32(h, log + 8)
    if not stream or _u32(h, log + 0x20) != stream + 0x20 or _u32(h, log + 0x28) != stream:
        problems.append('%s: fstream subobject addresses are wrong' % label)
    if not fail and _u32(h, log + 0x38) != stream + 8:
        problems.append('%s: reader got %#x, want stream+8 %#x' % (label, _u32(h, log + 0x38), stream + 8))
    return problems


def test_binary_object_loader(h):
    heap0 = h.heap_ptr
    try:
        fixture = _fixture(h)
        problems = []
        for case in ((1, 1), (0, 1), (0, 0)):
            problems += _check(h, fixture, *case)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
