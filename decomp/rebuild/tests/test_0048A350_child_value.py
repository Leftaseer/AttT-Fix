"""0x48A350 child construction and cached render value; allocation and construction are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x0048A350
ALLOCATE = 0x005E3EAE
CHILD_CTOR = 0x004792A0
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


def test_child_render_value(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x30, bytes(0x30))
        parent = h.alloc(0x60, bytes(0x60))
        child = h.alloc(0xec, bytes(0xec))
        info = h.alloc(0x30, bytes(0x30))
        render_value = 0x12345678
        h.uc.mem_write(child + 0x34, _dword(info))
        h.uc.mem_write(info + 0x2c, _dword(render_value))
        args = (0xC0000001, 0xC0000002, 0xC0000003, 0xC0000004,
                0xC0000005, 0xC0000006, 0xC0000007)

        _hook(h, ALLOCATE, _arg(4, log + 0x00) + b'\xFF\x05' + _dword(log + 0x04) +
              b'\xB8' + _dword(child) + b'\xC3')
        _hook(h, CHILD_CTOR, _log_ecx(log, 0x08) + _arg(4, log + 0x10) +
              _arg(8, log + 0x14) + b'\x8B\xC1\xC2\x08\x00')
        _import(h, DTOR_SLOT, DTOR_SYM, _log_ecx(log, 0x18) + b'\xC3')

        diffs = h.compare(FN, args=args, regs={UC_X86_REG_ECX: parent}, ret=None, mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x30))
        h.uc.mem_write(parent + 0x50, bytes(8))
        result = h.call(FN, args=args, regs={UC_X86_REG_ECX: parent})
        if result['fault']:
            return [result['fault']]

        name = h.arg_sp - len(args) * 4
        expected = ((0x00, 0xec, 'allocation size'), (0x04, 1, 'allocation calls'),
                    (0x08, child, 'child constructor self'), (0x0c, 1, 'child constructor calls'),
                    (0x10, name, 'child constructor name'), (0x14, 2, 'child constructor mode'),
                    (0x18, name, 'string destructor self'), (0x1c, 1, 'string destructor calls'))
        problems = []
        for offset, want, label in expected:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (label, got, want))
        if _u32(h, parent + 0x50) != child:
            problems.append('child was not stored')
        if _u32(h, parent + 0x54) != render_value:
            problems.append('render value was not cached')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
