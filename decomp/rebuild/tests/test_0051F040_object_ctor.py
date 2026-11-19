"""0x51F040 object constructor; allocation, string, table and helper calls are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x0051F040
STR_DEFAULT_SLOT = 0x006071E0
STR_DEFAULT_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
LIST_HEAD = 0x004C2F40
OPERATOR_NEW = 0x005E3EAE
TABLE_CTOR = 0x00435E00
TABLE_ASSIGN = 0x0057A860
TABLE_DTOR = 0x004220A0
VECTOR_INIT = 0x004D6040
GLOBAL_LIST = 0x006CA8E0
VT1 = 0x006143E4
TABLE_VT = 0x00607CC4
VT3 = 0x00613608
SENTINEL = 0x0060FE3C
NODE_VT = 0x00614388
CALLBACK = 0x0051D450
FILL = 0xCD

ORDER = 0x04
STR_SELF, STR_COUNT = 0x20, 0x24
HEAD_SELF, HEAD_COUNT = 0x28, 0x2C
NEW_SIZE, NEW_COUNT = 0x30, 0x34
TCTOR_SELF, TCTOR_ARG, TCTOR_COUNT = 0x38, 0x3C, 0x40
ASSIGN_SELF, ASSIGN_SRC, ASSIGN_COUNT = 0x44, 0x48, 0x4C
DTOR_SELF, DTOR_COUNT = 0x50, 0x54
VEC_SELF, VEC_N, VEC_COUNT = 0x58, 0x5C, 0x60
LOG_SIZE = 0x70
DELTA = 4

STR_OP, HEAD_OP, NEW_OP, TCTOR_OP, ASSIGN_OP, DTOR_OP, VEC_OP = range(1, 8)
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


def _tag(log, op):
    return b'\x8B\x15' + _dword(log) + b'\xFF\x05' + _dword(log) + \
        b'\xC7\x04\x95' + _dword(log + ORDER) + _dword(op)


def _store_ecx(log, offset):
    return b'\x89\x0D' + _dword(log + offset)


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _inc(log, offset):
    return b'\xFF\x05' + _dword(log + offset)


def test_object_ctor(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        self_ = h.alloc(0x100, bytes([FILL]) * 0x100)
        head = h.alloc(0x10, bytes(0x10))
        node = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(GLOBAL_LIST, _dword(0))

        _import(h, STR_DEFAULT_SLOT, STR_DEFAULT_SYM, _tag(log, STR_OP) + _store_ecx(log, STR_SELF) +
                _inc(log, STR_COUNT) + b'\x8B\xC1\xC3')
        _hook(h, LIST_HEAD, _tag(log, HEAD_OP) + _store_ecx(log, HEAD_SELF) + _inc(log, HEAD_COUNT) +
              b'\xB8' + _dword(head) + b'\xC3')
        _hook(h, OPERATOR_NEW, _tag(log, NEW_OP) + _arg(4, log + NEW_SIZE) + _inc(log, NEW_COUNT) +
              b'\xB8' + _dword(node) + b'\xC3')
        _hook(h, TABLE_CTOR, _tag(log, TCTOR_OP) + _store_ecx(log, TCTOR_SELF) +
              _arg(4, log + TCTOR_ARG) + _inc(log, TCTOR_COUNT) + b'\x8B\xC1\xC2\x04\x00')
        _hook(h, TABLE_ASSIGN, _tag(log, ASSIGN_OP) + _store_ecx(log, ASSIGN_SELF) +
              _arg(4, log + ASSIGN_SRC) + _inc(log, ASSIGN_COUNT) + b'\x8B\xC1\xC2\x04\x00')
        _hook(h, TABLE_DTOR, _tag(log, DTOR_OP) + _store_ecx(log, DTOR_SELF) + _inc(log, DTOR_COUNT) +
              b'\xC3')
        _hook(h, VECTOR_INIT, _tag(log, VEC_OP) + _store_ecx(log, VEC_SELF) + _arg(4, log + VEC_N) +
              _inc(log, VEC_COUNT) + b'\xC2\x04\x00')

        diffs = h.compare(FN, regs={UC_X86_REG_ECX: self_}, ret=None, mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(GLOBAL_LIST, _dword(0))
        h.uc.mem_write(log, bytes(LOG_SIZE))
        result = h.call(FN, regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']]
        problems = []
        if result['eax'] != self_:
            problems.append('return value is %#x, want self' % result['eax'])
        want_order = [STR_OP, HEAD_OP, NEW_OP, TCTOR_OP, ASSIGN_OP, DTOR_OP, VEC_OP]
        got_order = [_u32(h, log + ORDER + 4 * i) for i in range(len(want_order))]
        if got_order != want_order:
            problems.append('call order is %s, want %s' % (got_order, want_order))
        expected = ((0x00, VT1, 'vtable'), (0x04, 0, 'field 04'), (0x08, 0, 'field 08'),
                    (0x0c, 0, 'field 0c'), (0x10, 0, 'field 10'), (0x14, 0, 'field 14'),
                    (0x18, 0, 'field 18'), (0x1c, 0, 'field 1c'),
                    (0x20, TABLE_VT, 'first table vtable'), (0x24, 0, 'first table field'),
                    (0x28, 0xFFFFFFFF, 'first table count'),
                    (0x54, VT3, 'third vtable'), (0x58, 0, 'field 58'), (0x5c, 0, 'field 5c'),
                    (0x60, SENTINEL, 'sentinel 60'), (0x64, 0, 'field 64'), (0x68, 0, 'field 68'),
                    (0x6c, SENTINEL, 'sentinel 6c'), (0x70, 0, 'field 70'), (0x74, 0, 'field 74'),
                    (0x78, SENTINEL, 'sentinel 78'), (0x7c, 0, 'field 7c'), (0x80, 0, 'field 80'),
                    (0x88, 0, 'vector end'), (0x8c, 0, 'vector cap'), (0x90, 0, 'vector field'),
                    (0xa0, 0, 'field a0'), (0xa8, 0, 'float a8'),
                    (0xb0, head, 'list head'), (0xb4, 0, 'list count'),
                    (0xbc, TABLE_VT, 'second table vtable'), (0xc0, 0, 'second table field'),
                    (0xc4, 0xFFFFFFFF, 'second table count'))
        for offset, want, label in expected:
            got = _u32(h, self_ + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (label, got, want))
        if _u32(h, log + STR_SELF) != self_ + 0x2c or _u32(h, log + STR_COUNT) != 1:
            problems.append('default string constructor was not called on +0x2c')
        if _u32(h, log + HEAD_SELF) != self_ + 0xac or _u32(h, log + HEAD_COUNT) != 1:
            problems.append('list head helper was not called on +0xac')
        if _u32(h, log + NEW_SIZE) != 0x10 or _u32(h, log + NEW_COUNT) != 1:
            problems.append('node allocation is not 0x10 bytes')
        if _u32(h, log + TCTOR_SELF) != _u32(h, log + ASSIGN_SRC) or _u32(h, log + TCTOR_ARG) != 0:
            problems.append('temporary table was not built in place')
        if _u32(h, log + ASSIGN_SELF) != self_ + 0xbc:
            problems.append('table assignment target is %#x' % _u32(h, log + ASSIGN_SELF))
        if _u32(h, log + DTOR_SELF) != _u32(h, log + ASSIGN_SRC) or _u32(h, log + DTOR_COUNT) != 1:
            problems.append('temporary table was not destroyed')
        if _u32(h, log + VEC_SELF) != self_ + 0x84 or _u32(h, log + VEC_N) != 0x10:
            problems.append('vector init is wrong')
        if _u32(h, GLOBAL_LIST) != node:
            problems.append('global list head is %#x' % _u32(h, GLOBAL_LIST))
        list_node = [_u32(h, node + 4 * i) for i in range(4)]
        if list_node != [NODE_VT, 0, self_, CALLBACK]:
            problems.append('registered node is %s' % (list_node,))
        image = bytes(h.uc.mem_read(self_, 0x100))
        untouched = list(range(0x2c, 0x54)) + [0x84] + list(range(0x94, 0x9c)) + \
            list(range(0x9d, 0xa0)) + list(range(0xa4, 0xa8)) + [0xac] + \
            list(range(0xb9, 0xbc)) + list(range(0xc8, 0x100))
        bad = [hex(o) for o in untouched if image[o] != FILL]
        if bad:
            problems.append('unexpected writes at %s' % (bad,))
        if image[0x9c] != 0 or image[0xb8] != 0:
            problems.append('flag bytes are %#x / %#x' % (image[0x9c], image[0xb8]))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
