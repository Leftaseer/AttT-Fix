"""0x519B10 battle scene start; allocation, strings and configuration calls are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00519B10
SCAN = 0x00508770
OPERATOR_NEW = 0x005E3EAE
CHILD_CTOR = 0x00582FA0
TABLE_CTOR = 0x00435E00
TABLE_GET = 0x0057B4E0
TABLE_SET = 0x0057BF50
STRING_SET = 0x0057BDF0
FLOAT_GET = 0x0057AD40
FLOAT_SET = 0x0057BC80
TABLE_DTOR = 0x004220A0
UPDATE_STATE = 0x0046CF30
STR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
CSTR_SLOT = 0x0060732C
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
CSTR_SYM = '__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ'
LIT_MAGIC = 0x00614054
LIT_SCENE = 0x00613FD8
LIT_TACTIC = 0x0061404C
LIT_INTELLIGENCE = 0x00613960
LIT_CUR_INT = 0x0061403C
LIT_UNIT_NAME = 0x00614030
LIT_SPELL_BOOK = 0x00611AA0
STR_DATA = 0x00614FFF
FLOAT_VALUE = 42.5

ORDER = 0x04
SCAN_SELF, SCAN_OUT, SCAN_COUNT = 0x50, 0x54, 0x58
NEW_SIZE, NEW_COUNT = 0x5C, 0x60
SCENE_SELF, SCENE_FLAG, SCENE_COUNT = 0x64, 0x68, 0x6C
OLD_SELF, OLD_ARG, OLD_COUNT = 0x70, 0x74, 0x78
T_SELF, T_ARGS, T_COUNT = 0x7C, 0x80, 0x84
GET_SELF, GET_OUT, GET_KEY, GET_COUNT = 0x88, 0x8C, 0x90, 0x94
SET_SELF, SET_KEY, SET_VALUE, SET_COUNT = 0x98, 0x9C, 0xA0, 0xA4
DTOR_COUNT, DTOR_SELF = 0xA8, 0xAC
STR_COUNT, STR_PAIRS = 0xB8, 0xBC
FGET_SELF, FGET_KEY, FGET_COUNT = 0xCC, 0xD0, 0xD4
FSET_SELF, FSET_KEY, FSET_VALUE, FSET_COUNT = 0xD8, 0xDC, 0xE0, 0xE4
CSTR_SELF, CSTR_COUNT = 0xE8, 0xEC
CTOR_SELF, CTOR_LITERAL, CTOR_COUNT = 0xF0, 0xF4, 0xF8
CONF_SELF, CONF_NAME, CONF_TABLE, CONF_FLAG, CONF_COUNT = 0xFC, 0x100, 0x104, 0x108, 0x10C
DTOR2_SELF, DTOR2_COUNT = 0x110, 0x114
UPDATE_SELF, UPDATE_COUNT = 0x118, 0x11C
LOG_SIZE = 0x130
DELTA = 4

SCAN_OP, NEW_OP, SCENE_OP, OLD_OP, TCTOR_OP, GET_OP, SET_OP, DTOR_OP = range(1, 9)
SSTR_OP, FGET_OP, FSET_OP, CSTR_OP, SCTOR_OP, CONF_OP, SDTOR_OP, UPD_OP = range(9, 17)
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


def test_battle_scene_start(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        self_ = h.alloc(0x300, bytes(0x300))
        scene = h.alloc(0x194, bytes(0x194))
        game = h.alloc(0x100, bytes(0x100))
        update = h.alloc(0x40, bytes(0x40))
        level = h.alloc(0x80, bytes(0x80))
        holder = h.alloc(0x80, bytes(0x80))
        slot = h.alloc(0x10, bytes(0x10))
        unit = h.alloc(0x40, bytes(0x40))
        name = h.alloc(0x10, bytes(0x10))
        fval = h.alloc(4, struct.pack('<f', FLOAT_VALUE))
        old = h.alloc(0x40, bytes(0x40))
        old_vt = h.alloc(0x10, bytes(0x10))
        scene_vt = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(self_ + 0xbc, _dword(level))
        h.uc.mem_write(level + 0x64, _dword(holder))
        h.uc.mem_write(holder + 0x58, _dword(slot))
        h.uc.mem_write(slot, _dword(unit))
        h.uc.mem_write(unit + 8, _dword(name))
        h.uc.mem_write(self_ + 0x38, _dword(game))
        h.uc.mem_write(game + 0x80, _dword(update))
        h.uc.mem_write(self_ + 0x114, _dword(old))
        h.uc.mem_write(old + 4, _dword(old_vt))
        h.uc.mem_write(old + 8, _dword(1))
        h.uc.mem_write(scene, _dword(scene_vt))

        _hook(h, SCAN, _tag(log, SCAN_OP) + _store_ecx(log, SCAN_SELF) +
              _arg(4, log + SCAN_OUT) + _inc(log, SCAN_COUNT) + b'\xC2\x04\x00')
        _hook(h, OPERATOR_NEW, _tag(log, NEW_OP) + _arg(4, log + NEW_SIZE) +
              _inc(log, NEW_COUNT) + b'\xB8' + _dword(scene) + b'\xC3')
        _hook(h, CHILD_CTOR, _tag(log, SCENE_OP) + _store_ecx(log, SCENE_SELF) +
              _arg(4, log + SCENE_FLAG) + _inc(log, SCENE_COUNT) + b'\x8B\xC1\xC2\x04\x00')
        release = _stub(h, _tag(log, OLD_OP) + _store_ecx(log, OLD_SELF) +
                        _arg(4, log + OLD_ARG) + _inc(log, OLD_COUNT) + b'\xC2\x04\x00')
        h.uc.mem_write(old_vt, _dword(release))
        _hook(h, TABLE_CTOR, _tag(log, TCTOR_OP) + _store_ecx(log, T_SELF) +
              _arg(4, log + T_ARGS) + _inc(log, T_COUNT) + b'\xC2\x04\x00')
        _hook(h, TABLE_GET, _tag(log, GET_OP) + _store_ecx(log, GET_SELF) +
              _arg(4, log + GET_OUT) + _arg(8, log + GET_KEY) + _inc(log, GET_COUNT) +
              b'\x8B\x44\x24\x04\xC2\x08\x00')
        _hook(h, TABLE_SET, _tag(log, SET_OP) + _store_ecx(log, SET_SELF) +
              _arg(4, log + SET_KEY) + _arg(8, log + SET_VALUE) + _inc(log, SET_COUNT) +
              b'\xC2\x08\x00')
        _hook(h, TABLE_DTOR, _tag(log, DTOR_OP) +
              b'\x8B\x15' + _dword(log + DTOR_COUNT) +
              b'\x89\x0C\x95' + _dword(log + DTOR_SELF) + _inc(log, DTOR_COUNT) + b'\xC3')
        _hook(h, STRING_SET, _tag(log, SSTR_OP) +
              b'\x8B\x15' + _dword(log + STR_COUNT) +
              b'\x8B\x44\x24\x04' + b'\x89\x04\xD5' + _dword(log + STR_PAIRS) +
              b'\x8B\x44\x24\x08' + b'\x89\x04\xD5' + _dword(log + STR_PAIRS + 4) +
              _inc(log, STR_COUNT) + b'\xC2\x08\x00')
        _hook(h, FLOAT_GET, _tag(log, FGET_OP) + _store_ecx(log, FGET_SELF) +
              _arg(4, log + FGET_KEY) + _inc(log, FGET_COUNT) +
              b'\xD9\x05' + _dword(fval) + b'\xC2\x04\x00')
        _hook(h, FLOAT_SET, _tag(log, FSET_OP) + _store_ecx(log, FSET_SELF) +
              _arg(4, log + FSET_KEY) + _arg(8, log + FSET_VALUE) + _inc(log, FSET_COUNT) +
              b'\xC2\x08\x00')
        _import(h, CSTR_SLOT, CSTR_SYM, _tag(log, CSTR_OP) + _store_ecx(log, CSTR_SELF) +
                _inc(log, CSTR_COUNT) + b'\xB8' + _dword(STR_DATA) + b'\xC3')
        _import(h, STR_SLOT, STR_SYM, _tag(log, SCTOR_OP) + _store_ecx(log, CTOR_SELF) +
                _arg(4, log + CTOR_LITERAL) + _inc(log, CTOR_COUNT) +
                b'\x8B\xC1\xC2\x04\x00')
        _hook(h, UPDATE_STATE, _tag(log, UPD_OP) + _store_ecx(log, UPDATE_SELF) +
              _inc(log, UPDATE_COUNT) + b'\xC3')
        _import(h, STR_DTOR_SLOT, STR_DTOR_SYM, _tag(log, SDTOR_OP) +
                _store_ecx(log, DTOR2_SELF) + _inc(log, DTOR2_COUNT) + b'\xC3')
        configure = _stub(h, _tag(log, CONF_OP) + _store_ecx(log, CONF_SELF) +
                          _arg(4, log + CONF_NAME) + _arg(8, log + CONF_TABLE) +
                          _arg(0xC, log + CONF_FLAG) + _inc(log, CONF_COUNT) +
                          b'\xC2\x0C\x00')
        h.uc.mem_write(scene_vt + 0x3c, _dword(configure))

        diffs = h.compare(FN, regs={UC_X86_REG_ECX: self_}, ret=None, mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        result = h.call(FN, regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']]
        problems = []
        if _u32(h, self_ + 0x110) != 1 or _u32(h, self_ + 0x114) != scene:
            problems.append('level scene fields are wrong')
        if _u32(h, scene + 8) != 1 or _u32(h, old + 8) != 0:
            problems.append('scene reference counts are wrong')
        if _u32(h, game + 0xac) != 5:
            problems.append('game state is not 5')
        want_order = [SCAN_OP, NEW_OP, SCENE_OP, OLD_OP, TCTOR_OP, GET_OP, SET_OP, DTOR_OP,
                      SSTR_OP, FGET_OP, FSET_OP, CSTR_OP, SSTR_OP, SCTOR_OP, CONF_OP, SDTOR_OP,
                      UPD_OP, DTOR_OP, DTOR_OP]
        got_order = [_u32(h, log + ORDER + 4 * i) for i in range(len(want_order))]
        if got_order != want_order:
            problems.append('call order is %s, want %s' % (got_order, want_order))
        expected = ((SCAN_SELF, unit, 'scan self'), (SCAN_COUNT, 1, 'scan calls'),
                    (NEW_SIZE, 0x194, 'allocation size'), (NEW_COUNT, 1, 'allocation calls'),
                    (SCENE_SELF, scene, 'scene constructor self'), (SCENE_FLAG, 1, 'scene constructor flag'),
                    (SCENE_COUNT, 1, 'scene constructor calls'),
                    (OLD_SELF, old + 4, 'old scene object'), (OLD_ARG, 1, 'old scene delete flag'),
                    (OLD_COUNT, 1, 'old scene releases'),
                    (T_SELF, _u32(h, log + CONF_TABLE), 'table self'),
                    (T_ARGS, 0, 'table constructor flag'), (T_COUNT, 1, 'table constructor calls'),
                    (GET_SELF, _u32(h, log + SCAN_OUT), 'lookup self'),
                    (GET_OUT, _u32(h, log + SET_VALUE), 'lookup output'), (GET_KEY, LIT_MAGIC, 'lookup key'),
                    (GET_COUNT, 1, 'lookup calls'),
                    (SET_SELF, _u32(h, log + CONF_TABLE), 'setter self'), (SET_KEY, LIT_MAGIC, 'setter key'),
                    (SET_COUNT, 1, 'setter calls'),
                    (DTOR_COUNT, 3, 'table destructor calls'),
                    (STR_COUNT, 2, 'string setter calls'),
                    (FGET_SELF, _u32(h, log + SCAN_OUT), 'float lookup self'),
                    (FGET_KEY, LIT_INTELLIGENCE, 'float lookup key'), (FGET_COUNT, 1, 'float lookup calls'),
                    (FSET_SELF, _u32(h, log + CONF_TABLE), 'float setter self'),
                    (FSET_KEY, LIT_CUR_INT, 'float setter key'), (FSET_COUNT, 1, 'float setter calls'),
                    (CSTR_SELF, unit + 8, 'name string self'), (CSTR_COUNT, 1, 'name string calls'),
                    (CTOR_SELF, _u32(h, log + CONF_NAME), 'spell book string self'),
                    (CTOR_LITERAL, LIT_SPELL_BOOK, 'spell book literal'), (CTOR_COUNT, 1, 'spell book string calls'),
                    (CONF_SELF, scene, 'virtual self'), (CONF_FLAG, 1, 'virtual flag'), (CONF_COUNT, 1, 'virtual calls'),
                    (DTOR2_SELF, _u32(h, log + CONF_NAME), 'string destructor self'),
                    (DTOR2_COUNT, 1, 'string destructor calls'),
                    (UPDATE_SELF, update, 'state update self'), (UPDATE_COUNT, 1, 'state update calls'))
        for offset, want, label in expected:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (label, got, want))
        if _u32(h, log + FSET_VALUE) != 0x422A0000:
            problems.append('float value is %#x, want 0x422A0000' % _u32(h, log + FSET_VALUE))
        pairs = [(_u32(h, log + STR_PAIRS + 8 * i), _u32(h, log + STR_PAIRS + 8 * i + 4)) for i in range(2)]
        if pairs != [(LIT_SCENE, LIT_TACTIC), (LIT_UNIT_NAME, STR_DATA)]:
            problems.append('string pairs are %s' % (pairs,))
        receivers = [_u32(h, log + DTOR_SELF + 4 * i) for i in range(3)]
        if receivers != [_u32(h, log + GET_OUT), _u32(h, log + CONF_TABLE), _u32(h, log + SCAN_OUT)]:
            problems.append('table destructor receivers are %s' % (receivers,))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
