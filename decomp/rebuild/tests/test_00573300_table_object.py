"""0x573300 table-backed object constructor; construction helpers are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00573300
TABLE_COPY = 0x00435D90
BASE_CTOR = 0x00571940
ARRAY_CTOR = 0x00591D70
TABLE_DTOR = 0x004220A0
VTABLE = 0x0061D2CC
TABLE_WORDS = (0xD0000001, 0xD0000002, 0xD0000003)
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


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _log_ecx(log, offset):
    return b'\x89\x0D' + _dword(log + offset) + b'\xFF\x05' + _dword(log + offset + 4)


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _table_copy_code(log):
    code = _log_ecx(log, 0x00) + _arg(4, log + 0x08)
    for index, value in enumerate(TABLE_WORDS):
        if index:
            code += b'\xC7\x41' + bytes([index * 4]) + _dword(value)
        else:
            code += b'\xC7\x01' + _dword(value)
    return code + b'\x8B\xC1\xC2\x04\x00'


def _base_code(log):
    code = _log_ecx(log, 0x0c)
    for index in range(4):
        code += _arg(4 + index * 4, log + 0x14 + index * 4)
    return code + b'\xC2\x10\x00'


def test_table_object_ctor(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x50, bytes(0x50))
        obj = h.alloc(0x90, bytes(0x90))
        value = 0xD0000004
        args = TABLE_WORDS + (value,)

        _hook(h, TABLE_COPY, _table_copy_code(log))
        _hook(h, BASE_CTOR, _base_code(log))
        _hook(h, ARRAY_CTOR, _log_ecx(log, 0x24) + _arg(4, log + 0x2c) +
              _arg(8, log + 0x30) + b'\xC2\x08\x00')
        _hook(h, TABLE_DTOR, _log_ecx(log, 0x34) + b'\xC3')

        diffs = h.compare(FN, args=args, regs={UC_X86_REG_ECX: obj}, ret='eax', mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x50))
        result = h.call(FN, args=args, regs={UC_X86_REG_ECX: obj})
        if result['fault']:
            return [result['fault']]
        if result['eax'] != obj:
            return ['result is %#x, want %#x' % (result['eax'], obj)]

        incoming_table = h.arg_sp - len(args) * 4
        expected = [(0x08, incoming_table, 'table copy source'),
                    (0x0c, obj, 'base constructor self'), (0x10, 1, 'base constructor calls'),
                    (0x20, value, 'base constructor value'),
                    (0x24, obj + 0x78, 'array constructor self'), (0x28, 1, 'array constructor calls'),
                    (0x2c, 0x10, 'array size'),
                    (0x34, incoming_table, 'table destructor self'), (0x38, 1, 'table destructor calls')]
        for index, word in enumerate(TABLE_WORDS):
            expected.append((0x14 + index * 4, word, 'base table word %d' % index))
        problems = []
        for offset, want, label in expected:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (label, got, want))
        copy_destination = _u32(h, log + 0x00)
        if not copy_destination or _u32(h, log + 0x04) != 1:
            problems.append('table copy was not logged once')
        zero_pointer = _u32(h, log + 0x30)
        if not zero_pointer or _u32(h, zero_pointer) != 0:
            problems.append('array default value is not zero')
        if _u32(h, obj) != h.to_rebuilt(VTABLE):
            problems.append('vtable is %#x' % _u32(h, obj))
        if _u32(h, obj + 0x74) != 0:
            problems.append('+0x74 is not zero')
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
