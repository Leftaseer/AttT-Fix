"""0x485BA0 resource-open wrapper; the reader, processor, and string destructor are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00485BA0
OPEN = 0x00459050
PROCESS = 0x004857E0
CLOSE = 0x00459010
DTOR_SLOT = 0x00607330
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


def _case(h, log, obj, args, loaded):
    h.uc.mem_write(obj + 0xf4, bytes([loaded]))
    diffs = h.compare(FN, args=args, regs={UC_X86_REG_ECX: obj}, ret='al', mem=False)
    if diffs:
        return ['loaded %d: %s' % (loaded, d) for d in diffs]
    h.uc.mem_write(log, bytes(0x40))
    result = h.call(FN, args=args, regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['loaded %d: %s' % (loaded, result['fault'])]

    name = h.arg_sp - len(args) * 4
    reader = obj + 0xc8
    expected = ((0x00, reader, 'reader open self'), (0x04, 1, 'reader open calls'),
                (0x08, name, 'reader name'), (0x0c, 1, 'reader mode'),
                (0x10, obj if loaded else 0, 'processor self'), (0x14, int(loaded), 'processor calls'),
                (0x18, reader if loaded else 0, 'reader close self'), (0x1c, int(loaded), 'reader close calls'),
                (0x20, name, 'string destructor self'), (0x24, 1, 'string destructor calls'))
    problems = []
    for offset, want, label in expected:
        got = _u32(h, log + offset)
        if got != want:
            problems.append('loaded %d: %s is %#x, want %#x' % (loaded, label, got, want))
    if result['eax'] & 0xff != loaded:
        problems.append('loaded %d: result is %#x' % (loaded, result['eax'] & 0xff))
    return problems


def test_resource_open_wrapper(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x40, bytes(0x40))
        obj = h.alloc(0x100, bytes(0x100))
        args = (0xB0000001, 0xB0000002, 0xB0000003, 0xB0000004,
                0xB0000005, 0xB0000006, 0xB0000007)

        _hook(h, OPEN, _log_ecx(log, 0x00) + _arg(4, log + 0x08) + _arg(8, log + 0x0c) +
              b'\xB8\x55\x00\x00\x00\xC2\x08\x00')
        _hook(h, PROCESS, _log_ecx(log, 0x10) + b'\xC3')
        _hook(h, CLOSE, _log_ecx(log, 0x18) + b'\xC3')
        _import(h, DTOR_SLOT, DTOR_SYM, _log_ecx(log, 0x20) + b'\xC3')

        problems = []
        for loaded in (0, 1):
            problems += _case(h, log, obj, args, loaded)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
