"""Constructors 0x479AB0, 0x479B30, 0x4B03B0 and 0x4B0B40; base classes, finalizers,
string imports and allocation are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

RES0 = 0x00479AB0
RES1 = 0x00479B30
RECORD_RES = 0x004B03B0
CLOCK_RES = 0x004B0B40
BASE = 0x004ABA60
FINISH = 0x00479930
SET = 0x004AB810
NEW_ARRAY = 0x005E3B10
LOAD = 0x004AFBF0
HANDLE_CTOR = 0x00437970
CLOCK_BASE = 0x00532120
HANDLE_DTOR = 0x00427820
STR_CTOR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
STR_DEF_SLOT = 0x006071E0
STR_CTOR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
STR_DEF_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(value):
    return struct.pack('<I', value)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


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


def _inc(slot):
    return b'\xFF\x05' + _dword(slot)


def _log_this(slot):
    return b'\x89\x0D' + _dword(slot)


def _log_arg(offset, slot):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(slot)


def _setup_resource_stubs(h, log, block=0):
    _import(h, STR_CTOR_SLOT, STR_CTOR_SYM,
            _log_arg(4, log) + _inc(log + 4) + b'\x8B\xC1\xC2\x04\x00')
    _import(h, STR_DTOR_SLOT, STR_DTOR_SYM, _inc(log + 8) + b'\xC3')
    _hook(h, BASE, _log_this(log + 0x0c) + _log_arg(8, log + 0x10) +
          _inc(log + 0x14) + b'\xC2\x08\x00')
    _hook(h, FINISH, _log_this(log + 0x18) + b'\x8B\x01\xA3' + _dword(log + 0x1c) +
          _inc(log + 0x20) + b'\xC3')
    _hook(h, SET, _log_this(log + 0x24) + _log_arg(4, log + 0x28) +
          _log_arg(8, log + 0x2c) + _inc(log + 0x30) + b'\xC2\x08\x00')
    _hook(h, NEW_ARRAY, _log_arg(4, log + 0x34) + _inc(log + 0x38) +
          b'\xB8' + _dword(block) + b'\xC3')
    _import(h, STR_DEF_SLOT, STR_DEF_SYM,
            _log_this(log + 0x3c) + _inc(log + 0x40) + b'\x8B\xC1\xC3')
    _hook(h, LOAD, _log_this(log + 0x44) + _log_arg(4, log + 0x48) +
          _inc(log + 0x4c) + b'\xC2\x04\x00')


def _check_common(h, log, obj):
    problems = []
    if (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8)) != (0x0060FA8B, 1, 1):
        problems.append('string literal/counts are %#x/%d/%d' %
                        (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8)))
    if (_u32(h, log + 0x0c), _u32(h, log + 0x10), _u32(h, log + 0x14)) != (obj, 0, 1):
        problems.append('base log is %#x/%#x/%d' %
                        (_u32(h, log + 0x0c), _u32(h, log + 0x10), _u32(h, log + 0x14)))
    return problems


def test_empty_name_resource_constructors(h):
    heap0 = h.heap_ptr
    log = h.alloc(0x60, bytes(0x60))
    _setup_resource_stubs(h, log)
    try:
        problems = []
        for fn, args in ((RES0, []), (RES1, [0x12345678])):
            obj = h.alloc(0x100, bytes(0x100))
            diffs = h.compare(fn, args=args, regs={UC_X86_REG_ECX: obj})
            if diffs:
                return ['%08X: %s' % (fn, '; '.join(diffs))]
            h.uc.mem_write(log, bytes(0x60))
            result = h.call(fn, args=args, regs={UC_X86_REG_ECX: obj})
            if result['fault']:
                return ['%08X: %s' % (fn, result['fault'])]
            if (_u32(h, log + 0x18), _u32(h, log + 0x1c), _u32(h, log + 0x20)) != (obj, 0x0060EB6C, 1):
                problems.append('%08X: finish log is %#x/%#x/%d' %
                                (fn, _u32(h, log + 0x18), _u32(h, log + 0x1c), _u32(h, log + 0x20)))
            if _u32(h, obj) != 0x0060EB6C or result['eax'] != obj:
                problems.append('%08X: result/vtable are %#x/%#x' % (fn, result['eax'], _u32(h, obj)))
            if fn == RES1:
                if (_u32(h, log + 0x24), _u32(h, log + 0x28), _u32(h, log + 0x2c),
                        _u32(h, log + 0x30)) != (obj, args[0], 0, 1):
                    problems.append('setter log is incorrect')
            elif _u32(h, log + 0x30):
                problems.append('default constructor called the setter')
            problems += _check_common(h, log, obj)
            h.uc.mem_write(log, bytes(0x60))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_record_resource_constructor(h):
    heap0 = h.heap_ptr
    log = h.alloc(0x60, bytes(0x60))
    block = h.alloc(100 * 12, bytes(100 * 12))
    _setup_resource_stubs(h, log, block)
    try:
        obj = h.alloc(0x300, bytes(0x300))
        element = 0x23456789
        diffs = h.compare(RECORD_RES, args=[element], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x60))
        result = h.call(RECORD_RES, args=[element], regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return [result['fault']]
        problems = _check_common(h, log, obj)
        expected_fields = ((0, 0x006104AC), (0x204, 0x006104A4), (0x208, block),
                           (0x20c, 0), (0x24c, 0))
        for offset, want in expected_fields:
            if _u32(h, obj + offset) != want:
                problems.append('field +%#x is %#x, want %#x' % (offset, _u32(h, obj + offset), want))
        if (_u32(h, log + 0x34), _u32(h, log + 0x38)) != (100 * 12, 1):
            problems.append('allocation log is %#x/%d' % (_u32(h, log + 0x34), _u32(h, log + 0x38)))
        if (_u32(h, log + 0x3c), _u32(h, log + 0x40)) != (obj + 0x210, 1):
            problems.append('default string log is %#x/%d' % (_u32(h, log + 0x3c), _u32(h, log + 0x40)))
        if (_u32(h, log + 0x44), _u32(h, log + 0x48), _u32(h, log + 0x4c)) != (obj, element, 1):
            problems.append('loader log is incorrect')
        if result['eax'] != obj:
            problems.append('returned %#x' % result['eax'])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_clock_table_constructor(h):
    heap0 = h.heap_ptr
    log = h.alloc(0x20, bytes(0x20))
    _hook(h, HANDLE_CTOR, _log_arg(4, log) + _log_arg(8, log + 4) +
          _inc(log + 8) + b'\x8B\xC1\xC2\x08\x00')
    _hook(h, CLOCK_BASE, _log_this(log + 0x0c) + _inc(log + 0x10) + b'\xC2\x04\x00')
    _hook(h, HANDLE_DTOR, _inc(log + 0x14) + b'\xC3')
    try:
        obj = h.alloc(0x400, bytes(0x400))
        diffs = h.compare(CLOCK_RES, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x20))
        result = h.call(CLOCK_RES, regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return [result['fault']]
        problems = []
        if (_u32(h, log), _u32(h, log + 4), _u32(h, log + 8)) != (0x006107E0, 1, 1):
            problems.append('handle constructor log is incorrect')
        if (_u32(h, log + 0x0c), _u32(h, log + 0x10), _u32(h, log + 0x14)) != (obj, 1, 1):
            problems.append('base/destructor log is incorrect')
        expected = ((0, 0x00610704), (0x1f4, 0x006106F4), (0x1fc, 0x006106D4),
                    (0x250, 0x006106C0), (0x258, 0x006106B8), (0x25c, 0x006106AC), (0x374, 0))
        for offset, want in expected:
            if _u32(h, obj + offset) != want:
                problems.append('field +%#x is %#x, want %#x' % (offset, _u32(h, obj + offset), want))
        if result['eax'] != obj:
            problems.append('returned %#x' % result['eax'])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
