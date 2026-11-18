"""0x54C0D0 string-returning callback wrapper; the callback and string operations are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x0054C0D0
COPY_SLOT = 0x00607334
DTOR_SLOT = 0x00607330
COPY_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z'
DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
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


def test_string_callback_wrapper(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x30, bytes(0x30))
        obj = h.alloc(0x30, bytes(0x30))
        inner = h.alloc(0x20, bytes(0x20))
        output = h.alloc(0x1c, bytes(0x1c))
        returned = h.alloc(0x1c, bytes(0x1c))
        callback = _stub(h, _log_ecx(log, 0x00) + _arg(4, log + 0x08) +
                         _arg(8, log + 0x0c) + b'\xFF\x05' + _dword(log + 0x10) +
                         b'\xB8' + _dword(returned) + b'\xC2\x08\x00')
        h.uc.mem_write(obj + 0x1c, _dword(callback))
        h.uc.mem_write(obj + 0x24, _dword(inner))

        _import(h, COPY_SLOT, COPY_SYM, _log_ecx(log, 0x14) + _arg(4, log + 0x1c) +
                b'\x8B\xC1\xC2\x04\x00')
        _import(h, DTOR_SLOT, DTOR_SYM, _log_ecx(log, 0x20) + b'\xC3')

        diffs = h.compare(FN, args=(output,), regs={UC_X86_REG_ECX: obj}, ret='eax', mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x30))
        result = h.call(FN, args=(output,), regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return [result['fault']]
        if result['eax'] != output:
            return ['result is %#x, want %#x' % (result['eax'], output)]

        temporary = _u32(h, log + 0x08)
        expected = ((0x00, inner, 'callback self'), (0x04, 1, 'callback self calls'),
                    (0x0c, obj, 'callback owner'), (0x10, 1, 'callback calls'),
                    (0x14, output, 'copy constructor destination'), (0x18, 1, 'copy constructor calls'),
                    (0x1c, returned, 'copy constructor source'),
                    (0x20, temporary, 'temporary destructor self'), (0x24, 1, 'temporary destructor calls'))
        problems = []
        for offset, want, label in expected:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (label, got, want))
        if not temporary:
            problems.append('callback output was not logged')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
