"""0x4C3C00 AIL filter lookup; the list helper and the two imports are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004C3C00
LIST_HEAD = 0x004C2F40
ENUM_SLOT = 0x00607824
ENUM_SYM = '__imp___AIL_enumerate_filters@12'
EQ_SLOT = 0x006071E4
EQ_SYM = '__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z'
FILTER = 0x0BBB
FILL = 0xCD

ORDER = 0x04
HEAD_SELF, HEAD_COUNT = 0x18, 0x1C
ENUM_NEXT, ENUM_FILTER, ENUM_NAME, ENUM_COUNT = 0x20, 0x28, 0x30, 0x38
EQ_ARG1, EQ_ARG2, EQ_COUNT = 0x3C, 0x40, 0x44
LOG_SIZE = 0x58
DELTA = 8

HEAD_OP, ENUM_OP, EQ_OP = range(1, 4)
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


def test_filter_lookup(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        self_ = h.alloc(0x20, bytes([FILL]) * 0x20)
        head = h.alloc(0x10, bytes(0x10))
        name = h.alloc(0x10, b'filter\x00' + bytes(9))
        arg = h.alloc(0x10, bytes([FILL]) * 0x10)

        _hook(h, LIST_HEAD, _tag(log, HEAD_OP) + _store_ecx(log, HEAD_SELF) + _inc(log, HEAD_COUNT) +
              b'\xB8' + _dword(head) + b'\xC3')
        _import(h, ENUM_SLOT, ENUM_SYM,
                _tag(log, ENUM_OP) +
                b'\x8B\x15' + _dword(log + ENUM_COUNT) + _inc(log, ENUM_COUNT) +
                b'\x8B\x44\x24\x04' + b'\x89\x04\x95' + _dword(log + ENUM_NEXT) +
                b'\x8B\x44\x24\x08' + b'\x89\x04\x95' + _dword(log + ENUM_FILTER) +
                b'\x8B\x44\x24\x0c' + b'\x89\x04\x95' + _dword(log + ENUM_NAME) +
                b'\x8B\x44\x24\x04' + b'\xC7\x00' + _dword(0) +
                b'\x8B\x44\x24\x08' + b'\xC7\x00' + _dword(FILTER) +
                b'\x8B\x44\x24\x0c' + b'\xC7\x00' + _dword(name) +
                b'\xB8\x01\x00\x00\x00\xC2\x0C\x00')
        _import(h, EQ_SLOT, EQ_SYM,
                _tag(log, EQ_OP) + _arg(4, log + EQ_ARG1) + _arg(8, log + EQ_ARG2) +
                b'\x8B\x05' + _dword(log + EQ_COUNT) + _inc(log, EQ_COUNT) +
                b'\x31\xC9\x83\xF8\x01\x75\x02\xB1\x01\x89\xC8\xC3')

        diffs = h.compare(FN, args=[arg], regs={UC_X86_REG_ECX: self_}, ret=None, mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        result = h.call(FN, args=[arg], regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']]
        problems = []
        if result['eax'] != self_:
            problems.append('return value is %#x, want self' % result['eax'])
        want_order = [HEAD_OP, ENUM_OP, EQ_OP, ENUM_OP, EQ_OP]
        got_order = [_u32(h, log + ORDER + 4 * i) for i in range(len(want_order))]
        if got_order != want_order:
            problems.append('call order is %s, want %s' % (got_order, want_order))
        if _u32(h, log + HEAD_SELF) != self_ + 4 or _u32(h, log + HEAD_COUNT) != 1:
            problems.append('list head helper was not called on +4')
        if _u32(h, self_ + 8) != head or _u32(h, self_ + 0x0c) != 0:
            problems.append('list head fields are wrong')
        if _u32(h, self_ + 0) != FILTER:
            problems.append('filter result is %#x' % _u32(h, self_ + 0))
        if _u32(h, log + ENUM_COUNT) != 2 or _u32(h, log + EQ_COUNT) != 2:
            problems.append('enumeration is %d / matches %d, want 2 / 2' %
                            (_u32(h, log + ENUM_COUNT), _u32(h, log + EQ_COUNT)))
        for i, (offset, label) in enumerate(((ENUM_NEXT, 'handle'), (ENUM_FILTER, 'filter'),
                                             (ENUM_NAME, 'name'))):
            first = _u32(h, log + offset)
            second = _u32(h, log + offset + 4)
            if not first or first != second:
                problems.append('enumeration %s pointer went from %#x to %#x' % (label, first, second))
        pointers = [_u32(h, log + ENUM_NEXT), _u32(h, log + ENUM_FILTER), _u32(h, log + ENUM_NAME)]
        if len(set(pointers)) != 3:
            problems.append('enumeration outputs are not three locals: %s' % (pointers,))
        if _u32(h, log + EQ_ARG2) != name:
            problems.append('name argument is wrong')
        if _u32(h, log + EQ_ARG1) != arg:
            problems.append('string argument is %#x, want %#x' % (_u32(h, log + EQ_ARG1), arg))
        image = bytes(h.uc.mem_read(self_, 0x20))
        bad = [hex(o) for o in [4] + list(range(0x10, 0x20)) if image[o] != FILL]
        if bad:
            problems.append('unexpected writes at %s' % (bad,))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
