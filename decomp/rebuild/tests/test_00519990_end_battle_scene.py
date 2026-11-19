"""0x00519990 (ECX = the level, one stack argument -- an std::string, ret 4): the "TacticLevel" table is asked for
"EndBattle", the value is called with no arguments and the value, the call result and the table are destroyed.
The status byte +0x118 is cleared, a 0x194-byte GUIScene is allocated and constructed with 1 and stored at +0x21C.
A fresh table takes the argument string (c_str) as "bgnd" and the scene's vf3C is given a "Defeat" string and that
table (flag 1) before the string dies.  The level state +0x110 becomes 2, the game (+0x38) has the object stored at
+0x80 reset and its state +0xAC set to 5, and the table is destroyed last.  All helpers are stubs; the EAX/EDX/ECX
result is not compared (the original's is just its last destructor's scratch)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00519990
TABLE_CTOR = 0x004323E0
TABLE_GET = 0x0057B770
VALUE_CALL = 0x0057A180
GET_DTOR = 0x00427820
VALUE_DTOR = 0x004378D0
TABLE_DTOR = 0x004220A0
OPERATOR_NEW = 0x005E3EAE
SCENE_CTOR = 0x00582FA0
MAKE_TABLE = 0x00435E00
SET_STRING = 0x0057BDF0
UPDATE = 0x0046CF30
STR_CTOR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
CSTR_SLOT = 0x0060732C
STR_CTOR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
CSTR_SYM = '__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ'

LEVEL_LITERAL = 0x0060AB58
FUNCTION_LITERAL = 0x00614024
KEY_LITERAL = 0x0061401C
TEXT_LITERAL = 0x00614014
SCENE_SIZE = 0x194
STR_DATA = 0x0060F900

COUNT = 0x00
ORDER = 0x04
NEW_SIZE = 0x48
NEW_COUNT = 0x4C
SCENE_SELF = 0x50
SCENE_FLAG = 0x54
SCENE_COUNT = 0x58
T1_SELF = 0x5C
T1_NAME = 0x60
GET_SELF = 0x64
GET_OUT = 0x68
GET_KEY = 0x6C
GET_COUNT = 0x70
CALL_SELF = 0x74
CALL_OUT = 0x78
CALL_FLAG = 0x7C
CALL_COUNT = 0x80
RES_DTOR_SELF = 0x84
FN_DTOR_SELF = 0x88
TABLE_DTOR_SELF = 0x8C
TABLE_DTOR_COUNT = 0x9C
T2_SELF = 0xA0
T2_ARGS = 0xA4
SET_SELF = 0xA8
SET_KEY = 0xAC
SET_VALUE = 0xB0
CSTR_SELF = 0xB4
CSTR_COUNT = 0xB8
STR_SELF = 0xBC
STR_LITERAL = 0xC0
CONF_SELF = 0xC4
CONF_NAME = 0xC8
CONF_TABLE = 0xCC
CONF_FLAG = 0xD0
CONF_COUNT = 0xD4
STRDTOR_SELF = 0xD8
UPDATE_SELF = 0xDC
UPDATE_COUNT = 0xE0
LOG_SIZE = 0xE8

T1_CTOR_OP, GET_OP, CALL_OP, RESDTOR_OP, FNDTOR_OP, TABLE_DTOR_OP = 1, 2, 3, 4, 5, 6
NEW_OP, SCENE_OP, T2_OP, CSTR_OP, SET_OP, STR_OP = 7, 8, 9, 10, 11, 12
CONF_OP, STRDTOR_OP, UPDATE_OP = 13, 14, 15
EXPECTED_ORDER = [T1_CTOR_OP, GET_OP, CALL_OP, RESDTOR_OP, FNDTOR_OP, TABLE_DTOR_OP, NEW_OP, SCENE_OP,
                  T2_OP, CSTR_OP, SET_OP, STR_OP, CONF_OP, STRDTOR_OP, UPDATE_OP, TABLE_DTOR_OP]

DELTA = 8

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


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


def _tag(log, op):
    return (b'\x8B\x15' + _dword(log)                                    # edx = count
            + b'\xFF\x05' + _dword(log)                                  # count++
            + b'\xC7\x04\x95' + _dword(log + ORDER) + _dword(op))        # order[edx] = op


def _ecx(slot):
    return b'\x89\x0D' + _dword(slot)


def _arg(offset, slot):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(slot)


def _bump(slot):
    return b'\xFF\x05' + _dword(slot)


def _eax(value):
    return b'\xB8' + _dword(value)


def test_00519990(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        scene = h.alloc(SCENE_SIZE, bytes(SCENE_SIZE))
        update = h.alloc(0x40, bytes(0x40))
        game = h.alloc(0x100, bytes(0x100))
        self = h.alloc(0x300, bytes(0x300))
        name = h.alloc(0x20, b'EndBattleLevel\0' + bytes(0x20 - 15))
        vtable = h.alloc(0x40, bytes(0x40))

        configure = _stub(h, _tag(log, CONF_OP) + _ecx(log + CONF_SELF) + _arg(4, log + CONF_NAME)
                          + _arg(8, log + CONF_TABLE) + _arg(12, log + CONF_FLAG)
                          + _bump(log + CONF_COUNT) + b'\xC2\x0C\x00')
        h.uc.mem_write(vtable + 0x3C, _dword(configure))

        _hook(h, TABLE_CTOR, _tag(log, T1_CTOR_OP) + _ecx(log + T1_SELF) + _arg(4, log + T1_NAME)
              + b'\x8B\xC1\xC2\x04\x00')
        _hook(h, TABLE_GET, _tag(log, GET_OP) + _ecx(log + GET_SELF) + _arg(4, log + GET_OUT)
              + _arg(8, log + GET_KEY) + _bump(log + GET_COUNT)
              + b'\x8B\x44\x24\x04\xC2\x08\x00')
        _hook(h, VALUE_CALL, _tag(log, CALL_OP) + _ecx(log + CALL_SELF) + _arg(4, log + CALL_OUT)
              + _arg(8, log + CALL_FLAG) + _bump(log + CALL_COUNT)
              + b'\x8B\x44\x24\x04\xC2\x08\x00')
        _hook(h, GET_DTOR, _tag(log, RESDTOR_OP) + _ecx(log + RES_DTOR_SELF) + b'\xC3')
        _hook(h, VALUE_DTOR, _tag(log, FNDTOR_OP) + _ecx(log + FN_DTOR_SELF) + b'\xC3')
        # the table destructor runs twice: tag each call and keep both receivers
        _patch(h, TABLE_DTOR, _tag(log, TABLE_DTOR_OP)
               + b'\x8B\x15' + _dword(log + TABLE_DTOR_COUNT)
               + b'\x89\x0C\x95' + _dword(log + TABLE_DTOR_SELF)
               + b'\xFF\x05' + _dword(log + TABLE_DTOR_COUNT) + b'\xC3')
        _hook(h, OPERATOR_NEW, _tag(log, NEW_OP) + _arg(4, log + NEW_SIZE) + _bump(log + NEW_COUNT)
              + _eax(scene) + b'\xC3')
        _hook(h, SCENE_CTOR, _tag(log, SCENE_OP) + _ecx(log + SCENE_SELF) + _arg(4, log + SCENE_FLAG)
              + _bump(log + SCENE_COUNT) + b'\x8B\xC1\xC2\x04\x00')
        _hook(h, MAKE_TABLE, _tag(log, T2_OP) + _ecx(log + T2_SELF) + _arg(4, log + T2_ARGS)
              + b'\x8B\xC1\xC2\x04\x00')
        _hook(h, SET_STRING, _tag(log, SET_OP) + _ecx(log + SET_SELF) + _arg(4, log + SET_KEY)
              + _arg(8, log + SET_VALUE) + b'\xC2\x08\x00')
        _hook(h, UPDATE, _tag(log, UPDATE_OP) + _ecx(log + UPDATE_SELF) + _bump(log + UPDATE_COUNT) + b'\xC3')
        _import(h, STR_CTOR_SLOT, STR_CTOR_SYM, _tag(log, STR_OP) + _ecx(log + STR_SELF)
                + _arg(4, log + STR_LITERAL) + b'\x8B\xC1\xC2\x04\x00')
        _import(h, STR_DTOR_SLOT, STR_DTOR_SYM, _tag(log, STRDTOR_OP) + _ecx(log + STRDTOR_SELF) + b'\xC3')
        _import(h, CSTR_SLOT, CSTR_SYM, _tag(log, CSTR_OP) + _ecx(log + CSTR_SELF)
                + _bump(log + CSTR_COUNT) + _eax(STR_DATA) + b'\xC3')

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(scene, bytes(SCENE_SIZE))
            h.uc.mem_write(scene, _dword(vtable))
            h.uc.mem_write(update, b'\xA5' * 0x40)
            h.uc.mem_write(game, b'\xA5' * 0x100)
            h.uc.mem_write(game + 0x80, _dword(update))
            h.uc.mem_write(self, b'\xA5' * 0x300)
            h.uc.mem_write(self + 0x38, _dword(game))

        setup()
        diffs = h.compare(THIS, args=[name], regs={UC_X86_REG_ECX: self}, ret=None, mem=False)
        if diffs:
            return diffs

        setup()
        res = h.call(THIS, args=[name], regs={UC_X86_REG_ECX: self})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['esp'] != DELTA:
            return ['stack delta %d, not %d' % (res['esp'], DELTA)]

        problems = []
        count = _u32(h, log + COUNT)
        order = [_u32(h, log + ORDER + 4 * i) for i in range(count)]
        if order != EXPECTED_ORDER:
            problems.append('call order %s' % order)

        t1, t2 = _u32(h, log + T1_SELF), _u32(h, log + T2_SELF)
        fn, called = _u32(h, log + GET_OUT), _u32(h, log + CALL_OUT)
        if _u32(h, log + NEW_SIZE) != SCENE_SIZE or _u32(h, log + NEW_COUNT) != 1:
            problems.append('allocation %X x%d' % (_u32(h, log + NEW_SIZE), _u32(h, log + NEW_COUNT)))
        if _u32(h, log + SCENE_SELF) != scene or _u32(h, log + SCENE_FLAG) != 1 \
                or _u32(h, log + SCENE_COUNT) != 1:
            problems.append('scene constructor %08X(%d) x%d'
                            % (_u32(h, log + SCENE_SELF), _u32(h, log + SCENE_FLAG),
                               _u32(h, log + SCENE_COUNT)))
        if _u32(h, log + T1_NAME) != LEVEL_LITERAL:
            problems.append('table literal %08X' % _u32(h, log + T1_NAME))
        if _u32(h, log + GET_SELF) != t1 or _u32(h, log + GET_KEY) != FUNCTION_LITERAL \
                or _u32(h, log + GET_COUNT) != 1:
            problems.append('function lookup %08X/%08X x%d'
                            % (_u32(h, log + GET_SELF), _u32(h, log + GET_KEY), _u32(h, log + GET_COUNT)))
        if _u32(h, log + CALL_SELF) != fn or _u32(h, log + CALL_FLAG) != 0 \
                or _u32(h, log + CALL_COUNT) != 1:
            problems.append('function call %08X(%d) x%d'
                            % (_u32(h, log + CALL_SELF), _u32(h, log + CALL_FLAG), _u32(h, log + CALL_COUNT)))
        if _u32(h, log + RES_DTOR_SELF) != called or _u32(h, log + FN_DTOR_SELF) != fn:
            problems.append('result/value destructors %08X/%08X'
                            % (_u32(h, log + RES_DTOR_SELF), _u32(h, log + FN_DTOR_SELF)))
        if _u32(h, log + TABLE_DTOR_COUNT) != 2 \
                or _u32(h, log + TABLE_DTOR_SELF) != t1 or _u32(h, log + TABLE_DTOR_SELF + 4) != t2:
            problems.append('table destructors %d: %08X, %08X'
                            % (_u32(h, log + TABLE_DTOR_COUNT), _u32(h, log + TABLE_DTOR_SELF),
                               _u32(h, log + TABLE_DTOR_SELF + 4)))
        if _u32(h, log + T2_ARGS) != 0:
            problems.append('fresh table allocator %08X' % _u32(h, log + T2_ARGS))
        if _u32(h, log + SET_SELF) != t2 or _u32(h, log + SET_KEY) != KEY_LITERAL \
                or _u32(h, log + SET_VALUE) != STR_DATA:
            problems.append('string setter %08X %08X <- %08X'
                            % (_u32(h, log + SET_SELF), _u32(h, log + SET_KEY), _u32(h, log + SET_VALUE)))
        if _u32(h, log + CSTR_SELF) != name or _u32(h, log + CSTR_COUNT) != 1:
            problems.append('c_str %08X x%d' % (_u32(h, log + CSTR_SELF), _u32(h, log + CSTR_COUNT)))
        text = _u32(h, log + STR_SELF)
        if _u32(h, log + STR_LITERAL) != TEXT_LITERAL:
            problems.append('text literal %08X' % _u32(h, log + STR_LITERAL))
        if _u32(h, log + CONF_SELF) != scene or _u32(h, log + CONF_NAME) != text \
                or _u32(h, log + CONF_TABLE) != t2 or _u32(h, log + CONF_FLAG) != 1 \
                or _u32(h, log + CONF_COUNT) != 1:
            problems.append('scene configure %08X(%08X, %08X, %d) x%d'
                            % (_u32(h, log + CONF_SELF), _u32(h, log + CONF_NAME),
                               _u32(h, log + CONF_TABLE), _u32(h, log + CONF_FLAG),
                               _u32(h, log + CONF_COUNT)))
        if _u32(h, log + STRDTOR_SELF) != text:
            problems.append('text destructor %08X, text at %08X' % (_u32(h, log + STRDTOR_SELF), text))
        if _u32(h, log + UPDATE_SELF) != update or _u32(h, log + UPDATE_COUNT) != 1:
            problems.append('update %08X x%d' % (_u32(h, log + UPDATE_SELF), _u32(h, log + UPDATE_COUNT)))
        if (h.uc.mem_read(self + 0x118, 1)[0] != 0 or _u32(h, self + 0x21c) != scene
                or _u32(h, self + 0x110) != 2 or _u32(h, game + 0xac) != 5):
            problems.append('level fields %d %08X %d game %d'
                            % (h.uc.mem_read(self + 0x118, 1)[0], _u32(h, self + 0x21c),
                               _u32(h, self + 0x110), _u32(h, game + 0xac)))
        return problems or None
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
