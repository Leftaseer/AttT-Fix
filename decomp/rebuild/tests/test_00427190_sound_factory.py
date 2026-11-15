"""0x427190 (config entry -> Sound2D), 0x4273F0 (debug dump item), 0x4274F0 (backwards record copy),
0x427520 (two-dword pair) and 0x427990 (lazy CConfig instance)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

SOUND_FACTORY = 0x00427190
DEBUG_ITEM = 0x004273F0
MOVE_BACK = 0x004274F0
PAIR_SET = 0x00427520
CONFIG_INSTANCE = 0x00427990

OP_NEW = 0x005E3EAE
# both the original body (as kept in the rebuilt image) and the replacement call the imports through the relinker's
# new IAT slots, not through the original 0x006073xx ones
STRING_CTOR = 0x008D2C98
STRING_DTOR = 0x008D2CBC
LOOKUP = 0x00561520
SOUND2D_CTOR = 0x004C3AE0
CONFIG_VALUE = 0x005613A0
ITEM_NAME = 0x00402FD0
RECORD = 0x00403120
SPRINTF = 0x008D3058
DUMP_SOURCE = 0x008D122C
DUMP_VALUE = 0x006C8848
DUMP_FORMAT = 0x00608254
DUMP_BUFFER = 0x006C8748
CONFIG_SLOT = 0x006C884C

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, stub):
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    h.uc.ctl_remove_cache(target, target + 5)


def _callee_stub(h, log, value, pop, args):
    """logs ECX and the stack arguments into `log`, returns `value` and pops `pop` bytes"""
    code = b'\x89\x0D' + _dword(log)
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _float_stub(h, value):
    """pops the one stack argument and returns `value` in st0"""
    p = h.alloc(4, struct.pack('<f', value))
    return _stub(h, b'\xD9\x05' + _dword(p) + b'\xC2\x04\x00')


def _literal_stub(h, log):
    """std::string's constructor from a C string: logs the literal and keeps it in the object's first dword (ECX is a
    stack address that differs, so the object content is checked instead of its address)"""
    return _stub(h, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log) + b'\x89\x01' + b'\xC2\x04\x00')


def _lookup_stub(h, log, value):
    """logs ECX and the key string's content (the first dword the literal constructor stored)"""
    code = b'\x89\x0D' + _dword(log)
    code += b'\x8B\x44\x24\x08' + b'\x8B\x00' + b'\xA3' + _dword(log + 4)
    code += b'\xB8' + _dword(value) + b'\xC2\x08\x00'
    return _stub(h, code)


def _cdecl_stub(h, log, value, pop, args):
    """logs the stack arguments and returns `value` (no ECX: a cdecl callee's ECX is not an argument)"""
    code = b''
    for i in range(args):
        code += b'\x8B\x54\x24' + bytes([4 + 4 * i]) + b'\x89\x15' + _dword(log + 4 * i)
    code += b'\xB8' + _dword(value) + b'\xC2' + struct.pack('<H', pop)
    return _stub(h, code)


def _sprintf_stub(h, log):
    """logs the four arguments, writes 'OK' to the destination and returns 2"""
    code = b''
    for i in range(4):
        code += b'\x8B\x44\x24' + bytes([4 + 4 * i]) + b'\xA3' + _dword(log + 4 * i)
    code += b'\x8B\x54\x24\x04' + b'\xC7\x02' + b'OK\0\0'
    code += b'\xB8' + _dword(2) + b'\xC2\x00\x00'
    return _stub(h, code)


def _log(h, size=0x10):
    return h.alloc(size, bytes(size))


def test_sound_factory(h):
    """the entry's map object gives the FileName string, which builds the Sound2D; the two values are truncated"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x20, bytes(0x20))
        entry = h.alloc(0x40, bytes(0x40))
        obj = h.alloc(0x80, bytes(0x80))
        new_log = _log(h)
        ctor_log = _log(h)
        lookup_log = _log(h)
        build_log = _log(h)
        _hook(h, OP_NEW, _callee_stub(h, new_log, obj, 0, 1))
        _hook(h, LOOKUP, _lookup_stub(h, lookup_log, 0x0badf00d))
        _hook(h, SOUND2D_CTOR, _callee_stub(h, build_log, 0x1234abcd, 4, 1))
        _hook(h, CONFIG_VALUE, _float_stub(h, 7.9))
        _patch(h, STRING_CTOR, _dword(_literal_stub(h, ctor_log)))
        _patch(h, STRING_DTOR, _dword(_stub(h, b'\xC3')))
        diffs = h.compare(SOUND_FACTORY, args=[entry], regs={UC_X86_REG_ECX: s}, ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(s, bytes(0x20))
        h.call(SOUND_FACTORY, args=[entry], regs={UC_X86_REG_ECX: s})
        problems = []
        if _u32(h, s) != 0x1234abcd:
            problems.append('the Sound2D pointer is %#x' % _u32(h, s))
        if _u32(h, s + 4) != 7 or _u32(h, s + 8) != 7:
            problems.append('the values are %d, %d' % (_u32(h, s + 4), _u32(h, s + 8)))
        if _u32(h, new_log + 4) != 0x44:
            problems.append('operator new got %d bytes' % _u32(h, new_log + 4))
        if _u32(h, lookup_log) != entry:
            problems.append('the lookup object is %#x' % _u32(h, lookup_log))
        if _u32(h, lookup_log + 4) != 0x00608240:                    # "FileName"
            problems.append('the lookup key is %#x' % _u32(h, lookup_log + 4))
        if _u32(h, build_log) != obj or _u32(h, build_log + 4) != 0x0badf00d:
            problems.append('the Sound2D constructor got %#x, %#x' % (_u32(h, build_log), _u32(h, build_log + 4)))
        if _u32(h, ctor_log) != 0x00608218:                          # the last string is "RandomEmitKeyValue"
            problems.append('the last built string is %#x' % _u32(h, ctor_log))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_debug_item(h):
    """the value's item name and the item pointer are formatted into the buffer and recorded under the value"""
    heap0 = h.heap_ptr
    try:
        source = _u32(h, DUMP_SOURCE)
        _patch(h, DUMP_BUFFER, bytes(0x40))
        _patch(h, DUMP_VALUE, _dword(0x5A5A1234))
        item = h.alloc(4, _dword(0xCAFEBABE))
        name_log = _log(h)
        format_log = _log(h, 0x10)
        record_log = _log(h)
        _hook(h, ITEM_NAME, _cdecl_stub(h, name_log, item, 0, 2))
        _hook(h, RECORD, _cdecl_stub(h, record_log, 0, 0, 2))
        _patch(h, SPRINTF, _dword(_sprintf_stub(h, format_log)))
        diffs = h.compare(DEBUG_ITEM, ret='eax')
        if diffs:
            return diffs
        res = h.call(DEBUG_ITEM)
        problems = []
        if res['eax'] != 1:
            problems.append('the result is %#x' % res['eax'])
        if _u32(h, name_log) != source or _u32(h, name_log + 4) != 1:
            problems.append('the item lookup got %#x, %#x' % (_u32(h, name_log), _u32(h, name_log + 4)))
        if (_u32(h, format_log) != DUMP_BUFFER or _u32(h, format_log + 4) != DUMP_FORMAT
                or _u32(h, format_log + 8) != 0x5A5A1234 or _u32(h, format_log + 12) != 0xCAFEBABE):
            problems.append('the format got %r' % struct.unpack('<4I', h.uc.mem_read(format_log, 16)))
        if _u32(h, record_log) != source or _u32(h, record_log + 4) != DUMP_BUFFER:
            problems.append('the record got %#x, %#x' % (_u32(h, record_log), _u32(h, record_log + 4)))
        if bytes(h.uc.mem_read(DUMP_BUFFER, 3)) != b'OK\0':
            problems.append('the buffer holds %r' % bytes(h.uc.mem_read(DUMP_BUFFER, 16)))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_move_back(h):
    """records are copied backwards from [begin, end) to the area that ends at dst"""
    heap0 = h.heap_ptr
    try:
        src = h.alloc(0x30, bytes(0x30))
        dst = h.alloc(0x30, bytes(0x30))
        for i in range(4):
            h.uc.mem_write(src + 12 * i, struct.pack('<3I', 10 * (i + 1), 10 * (i + 1) + 1, 10 * (i + 1) + 2))
        diffs = h.compare(MOVE_BACK, args=[src + 12, src + 48, dst + 36], ret=None)
        if diffs:
            return diffs
        h.call(MOVE_BACK, args=[src + 12, src + 48, dst + 36])
        want = struct.pack('<3I', 20, 21, 22) + struct.pack('<3I', 30, 31, 32) + struct.pack('<3I', 40, 41, 42)
        got = bytes(h.uc.mem_read(dst, 36))
        problems = []
        if got != want:
            problems.append('the destination holds %s' % got.hex())
        if bytes(h.uc.mem_read(dst + 36, 12)) != bytes(12):
            problems.append('the tail was overwritten')
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_empty_move_back(h):
    """begin == end copies nothing"""
    heap0 = h.heap_ptr
    try:
        src = h.alloc(0x20, bytes(0x20))
        dst = h.alloc(0x20, b'\xAA' * 0x20)
        diffs = h.compare(MOVE_BACK, args=[src + 12, src + 12, dst + 12], ret=None)
        if diffs:
            return diffs
        h.call(MOVE_BACK, args=[src + 12, src + 12, dst + 12])
        if bytes(h.uc.mem_read(dst, 0x20)) != b'\xAA' * 0x20:
            return ['the destination changed']
        return None
    finally:
        h.heap_ptr = heap0


def test_pair_set(h):
    """this and the value are stored as a two-dword pair"""
    heap0 = h.heap_ptr
    try:
        s = h.alloc(0x10, bytes(0x10))
        pair = h.alloc(8, b'\xCC' * 8)
        diffs = h.compare(PAIR_SET, args=[pair, 0x11223344], regs={UC_X86_REG_ECX: s}, ret=None)
        if diffs:
            return diffs
        h.call(PAIR_SET, args=[pair, 0x11223344], regs={UC_X86_REG_ECX: s})
        problems = []
        if _u32(h, pair) != s:
            problems.append('the first dword is %#x' % _u32(h, pair))
        if _u32(h, pair + 4) != 0x11223344:
            problems.append('the second dword is %#x' % _u32(h, pair + 4))
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_config_instance(h):
    """the instance is built once and kept at 0x006C884C"""
    heap0 = h.heap_ptr
    try:
        _patch(h, CONFIG_SLOT, bytes(4))
        diffs = h.compare(CONFIG_INSTANCE, ret='eax')
        if diffs:
            return diffs
        h.uc.mem_write(CONFIG_SLOT, bytes(4))
        first = h.call(CONFIG_INSTANCE)['eax']
        if not first:
            return ['the first call gave no instance']
        if _u32(h, CONFIG_SLOT) != first:
            return ['the slot holds %#x' % _u32(h, CONFIG_SLOT)]
        second = h.call(CONFIG_INSTANCE)['eax']
        if second != first:
            return ['the second call gave %#x' % second]
        return None
    finally:
        _restore(h)
        h.heap_ptr = heap0
