"""0x486280 string-backed setup call; string operations and the callee are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00486280
CALLEE = 0x00485BA0
COPY_SLOT = 0x00607334
DTOR_SLOT = 0x00607330
COPY_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z'
DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
STRING_WORDS = (0x11111111, 0x22222222, 0x33333333, 0x44444444,
                0x55555555, 0x66666666, 0x77777777)
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


def _copy_code(log):
    code = _log_ecx(log, 0x00) + _arg(4, log + 0x08)
    for index, value in enumerate(STRING_WORDS):
        if index:
            code += b'\xC7\x41' + bytes([index * 4]) + _dword(value)
        else:
            code += b'\xC7\x01' + _dword(value)
    return code + b'\x8B\xC1\xC2\x04\x00'


def _callee_code(log):
    code = _log_ecx(log, 0x14)
    for index in range(7):
        code += _arg(4 + index * 4, log + 0x1c + index * 4)
    return code + b'\xC2\x1C\x00'


def test_string_setup(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        obj = h.alloc(0x100, bytes(0x100))
        incoming_words = (0xA0000001, 0xA0000002, 0xA0000003, 0xA0000004,
                          0xA0000005, 0xA0000006, 0xA0000007)
        tail_args = (0xA0000008, 0xA0000009)
        args = incoming_words + tail_args

        _import(h, COPY_SLOT, COPY_SYM, _copy_code(log))
        _import(h, DTOR_SLOT, DTOR_SYM, _log_ecx(log, 0x0c) + b'\xC3')
        _hook(h, CALLEE, _callee_code(log))

        diffs = h.compare(FN, args=args, regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x40))
        result = h.call(FN, args=args, regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return [result['fault']]

        incoming_string = h.arg_sp - len(args) * 4
        problems = []
        local_string = _u32(h, log + 0x00)
        expected = ((0x04, 1, 'copy constructor calls'),
                    (0x08, incoming_string, 'copy constructor source'),
                    (0x0c, incoming_string, 'destructor object'),
                    (0x10, 1, 'destructor calls'),
                    (0x14, obj, 'callee self'),
                    (0x18, 1, 'callee calls'))
        for offset, want, name in expected:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (name, got, want))
        if not local_string or local_string == incoming_string:
            problems.append('copy constructor destination is invalid')
        for index, want in enumerate(STRING_WORDS):
            got = _u32(h, log + 0x1c + index * 4)
            if got != want:
                problems.append('forwarded string word %d is %#x, want %#x' % (index, got, want))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
