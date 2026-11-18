"""0x519CE0 child render-object setup; allocation, strings and configuration calls are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00519CE0
OPERATOR_NEW = 0x005E3EAE
CHILD_CTOR = 0x00582FA0
MAKE_VALUE = 0x00435E00
SET_VALUE = 0x0057BB20
UPDATE_STATE = 0x0046CF30
VALUE_DTOR = 0x004220A0
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


def test_child_render_setup(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x70, bytes(0x70))
        obj = h.alloc(0x220, bytes(0x220))
        state = h.alloc(0xb0, bytes(0xb0))
        child = h.alloc(0x194, bytes(0x194))
        h.uc.mem_write(obj + 0x38, _dword(state))

        configure = _stub(h, _log_ecx(log, 0x3c) + _arg(4, log + 0x40) + _arg(8, log + 0x44) +
                          b'\xFF\x05' + _dword(log + 0x4c) + _arg(0x0c, log + 0x48) + b'\xC2\x0C\x00')
        vtable = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(vtable + 0x3c, _dword(configure))
        h.uc.mem_write(child, _dword(vtable))

        _hook(h, OPERATOR_NEW, _arg(4, log + 0x00) + b'\xFF\x05' + _dword(log + 0x04) +
              b'\xB8' + _dword(child) + b'\xC3')
        _hook(h, CHILD_CTOR, _log_ecx(log, 0x08) + _arg(4, log + 0x0c) + b'\xFF\x05' +
              _dword(log + 0x10) + b'\xB8' + _dword(child) + b'\xC2\x04\x00')
        _hook(h, MAKE_VALUE, _log_ecx(log, 0x14) + _arg(4, log + 0x18) + b'\xFF\x05' +
              _dword(log + 0x1c) + b'\xC2\x04\x00')
        _hook(h, SET_VALUE, _log_ecx(log, 0x20) + _arg(4, log + 0x24) + _arg(8, log + 0x28) +
              b'\xFF\x05' + _dword(log + 0x2c) + b'\xC2\x08\x00')
        _import(h, STR_SLOT, STR_SYM, _log_ecx(log, 0x30) + _arg(4, log + 0x34) +
                b'\xFF\x05' + _dword(log + 0x38) + b'\x8B\xC1\xC2\x04\x00')
        _import(h, STR_DTOR_SLOT, STR_DTOR_SYM, _log_ecx(log, 0x50) + b'\xC3')
        _hook(h, UPDATE_STATE, _log_ecx(log, 0x58) + b'\xC3')
        _hook(h, VALUE_DTOR, _log_ecx(log, 0x60) + b'\xC3')

        diffs = h.compare(FN, regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x70))
        result = h.call(FN, regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return [result['fault']]
        problems = []
        if _u32(h, obj + 0x21c) != child or _u32(h, obj + 0x110) != 4 or _u32(h, state + 0xac) != 5:
            problems.append('parent or shared state fields are wrong')
        expected = ((0x00, 0x194, 'allocation size'), (0x04, 1, 'allocation calls'),
                    (0x08, child, 'child constructor self'), (0x0c, 1, 'child constructor flag'), (0x10, 1, 'child constructor calls'),
                    (0x18, 0, 'value flag'), (0x1c, 1, 'value calls'), (0x24, 0x00614068, 'value literal'),
                    (0x28, 1, 'value setter flag'), (0x2c, 1, 'value setter calls'),
                    (0x34, 0x0061405C, 'name literal'), (0x38, 1, 'name constructor calls'),
                    (0x3c, child, 'virtual self'), (0x48, 1, 'virtual flag'), (0x4c, 1, 'virtual calls'),
                    (0x54, 1, 'name destructor calls'), (0x58, state + 0x80, 'state update self'),
                    (0x5c, 1, 'state update calls'), (0x64, 1, 'value destructor calls'))
        for offset, want, name in expected:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (name, got, want))
        value = _u32(h, log + 0x14)
        name = _u32(h, log + 0x30)
        if not value or _u32(h, log + 0x20) != value or _u32(h, log + 0x44) != value or _u32(h, log + 0x60) != value:
            problems.append('value string was not forwarded consistently')
        if not name or _u32(h, log + 0x40) != name or _u32(h, log + 0x50) != name:
            problems.append('name string was not forwarded consistently')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
