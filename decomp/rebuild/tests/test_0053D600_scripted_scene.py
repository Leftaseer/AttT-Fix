"""0x53D600 / 0x53D840 scripted battle scene start: two identical bodies, the first with an unused stack argument.

The global "Unit" table lookups, table helpers, string imports and the scene vtable slot are stubs that log
their arguments; the test checks the whole call sequence, the values that travel between the calls and the
state fields, then compares both functions against the original.
"""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN_ARG = 0x0053D600
FN_PLAIN = 0x0053D840
OPERATOR_NEW = 0x005E3EAE
CHILD_CTOR = 0x00582FA0
TABLE_CTOR = 0x00435E00
NAMED_TABLE = 0x004323E0
TABLE_GET = 0x0057B4E0
TABLE_SET = 0x0057BF50
STRING_SET = 0x0057BDF0
FLOAT_GET = 0x0057AD40
FLOAT_SET = 0x0057BC80
TABLE_DTOR = 0x004220A0
UPDATE_STATE = 0x0046CF30
STR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
LIT_HERO = 0x0060C080
LIT_UNIT = 0x0060C088
LIT_BATTLE = 0x00613978
LIT_MAGIC = 0x00614054
LIT_SCENE = 0x00613FD8
LIT_INTELLIGENCE = 0x00613960
LIT_CUR_INT = 0x0061403C
LIT_UNIT_NAME = 0x00614030
LIT_SPELL_BOOK = 0x00611AA0
SCENE_FUNCS = 0x0061ADFC
FLOAT_VALUE = 1.5
OLD_SCENE = 0x00C0DE01
OLD_FIELD = 0x00C0DE02
REFCOUNT = 0x00111111

ORDER = 0x04
NEW_SIZE, NEW_COUNT = 0x74, 0x78
SCENE_SELF, SCENE_FLAG, SCENE_COUNT = 0x7C, 0x80, 0x84
TCTOR_SELF, TCTOR_ARG, TCTOR_COUNT = 0x88, 0x8C, 0x90
NAMED_SELF, NAMED_NAME, NAMED_COUNT = 0x94, 0x9C, 0xA4
GET_SELF, GET_OUT, GET_KEY, GET_COUNT = 0xA8, 0xBC, 0xD0, 0xE4
SET_SELF, SET_KEY, SET_VALUE, SET_COUNT = 0xE8, 0xEC, 0xF0, 0xF4
DTOR_SELF, DTOR_COUNT = 0xF8, 0x118
SSTR_SELF, SSTR_KEY, SSTR_VALUE, SSTR_COUNT = 0x11C, 0x124, 0x12C, 0x134
FGET_SELF, FGET_KEY, FGET_COUNT = 0x138, 0x13C, 0x140
FSET_SELF, FSET_KEY, FSET_VALUE, FSET_COUNT = 0x144, 0x148, 0x14C, 0x150
SCTOR_SELF, SCTOR_LITERAL, SCTOR_COUNT = 0x154, 0x158, 0x15C
CONF_SELF, CONF_NAME, CONF_TABLE, CONF_FLAG, CONF_COUNT = 0x160, 0x164, 0x168, 0x16C, 0x170
SDTOR_SELF, SDTOR_COUNT = 0x174, 0x178
UPD_SELF, UPD_COUNT = 0x17C, 0x180
EXTRA_COUNT = 0x184
LOG_SIZE = 0x190

NEW_OP, SCENE_OP, TCTOR_OP, NAMED_OP, GET_OP, SET_OP, DTOR_OP = range(1, 8)
SSTR_OP, FGET_OP, FSET_OP, SCTOR_OP, CONF_OP, SDTOR_OP, UPD_OP = range(8, 15)
WANT_ORDER = [NEW_OP, SCENE_OP, TCTOR_OP, NAMED_OP, GET_OP, GET_OP, GET_OP, SET_OP,
              DTOR_OP, DTOR_OP, DTOR_OP, DTOR_OP, SSTR_OP, NAMED_OP, GET_OP, GET_OP, FGET_OP,
              FSET_OP, DTOR_OP, DTOR_OP, DTOR_OP, SSTR_OP, SCTOR_OP, CONF_OP, SDTOR_OP,
              UPD_OP, DTOR_OP]
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


def _count_edx(log, offset):
    return b'\x8B\x15' + _dword(log + offset)


def _indexed_eax(log, offset):
    return b'\x89\x04\x95' + _dword(log + offset)


def _indexed_ecx(log, offset):
    return b'\x89\x0C\x95' + _dword(log + offset)


def _run(h, fn, args):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        self_ = h.alloc(0x200, bytes(0x200))
        scene = h.alloc(0x194, bytes(0x194))
        scene_vt = h.alloc(0x40, bytes(0x40))
        game = h.alloc(0x100, bytes(0x100))
        update = h.alloc(0x40, bytes(0x40))
        old = h.alloc(0x40, bytes(0x40))
        old_vt = h.alloc(0x10, bytes(0x10))
        fval = h.alloc(4, struct.pack('<f', FLOAT_VALUE))
        h.uc.mem_write(self_ + 0x38, _dword(game))
        h.uc.mem_write(self_ + 0x110, _dword(OLD_SCENE))
        h.uc.mem_write(self_ + 0x114, _dword(OLD_FIELD))
        h.uc.mem_write(game + 0x80, _dword(update))
        h.uc.mem_write(scene + 8, _dword(REFCOUNT))
        h.uc.mem_write(scene, _dword(scene_vt))
        h.uc.mem_write(old + 4, _dword(old_vt))

        _hook(h, OPERATOR_NEW, _tag(log, NEW_OP) + _arg(4, log + NEW_SIZE) +
              _inc(log, NEW_COUNT) + b'\xB8' + _dword(scene) + b'\xC3')
        _hook(h, CHILD_CTOR, _tag(log, SCENE_OP) + _store_ecx(log, SCENE_SELF) +
              _arg(4, log + SCENE_FLAG) + _inc(log, SCENE_COUNT) + b'\x8B\xC1\xC2\x04\x00')
        _hook(h, TABLE_CTOR, _tag(log, TCTOR_OP) + _store_ecx(log, TCTOR_SELF) +
              _arg(4, log + TCTOR_ARG) + _inc(log, TCTOR_COUNT) + b'\xC2\x04\x00')
        _hook(h, NAMED_TABLE, _tag(log, NAMED_OP) + _count_edx(log, NAMED_COUNT) +
              b'\x8B\x44\x24\x04' + _indexed_eax(log, NAMED_NAME) + _indexed_ecx(log, NAMED_SELF) +
              _inc(log, NAMED_COUNT) + b'\x8B\xC1\xC2\x04\x00')
        _hook(h, TABLE_GET, _tag(log, GET_OP) + _count_edx(log, GET_COUNT) +
              _indexed_ecx(log, GET_SELF) +
              b'\x8B\x44\x24\x04' + _indexed_eax(log, GET_OUT) +
              b'\x8B\x44\x24\x08' + _indexed_eax(log, GET_KEY) +
              _inc(log, GET_COUNT) + b'\x8B\x44\x24\x04\xC2\x08\x00')
        _hook(h, TABLE_SET, _tag(log, SET_OP) + _count_edx(log, SET_COUNT) +
              _indexed_ecx(log, SET_SELF) +
              b'\x8B\x44\x24\x04' + _indexed_eax(log, SET_KEY) +
              b'\x8B\x44\x24\x08' + _indexed_eax(log, SET_VALUE) +
              _inc(log, SET_COUNT) + b'\xC2\x08\x00')
        _hook(h, TABLE_DTOR, _tag(log, DTOR_OP) + _count_edx(log, DTOR_COUNT) +
              _indexed_ecx(log, DTOR_SELF) + _inc(log, DTOR_COUNT) + b'\xC3')
        _hook(h, STRING_SET, _tag(log, SSTR_OP) + _count_edx(log, SSTR_COUNT) +
              _indexed_ecx(log, SSTR_SELF) +
              b'\x8B\x44\x24\x04' + _indexed_eax(log, SSTR_KEY) +
              b'\x8B\x44\x24\x08' + _indexed_eax(log, SSTR_VALUE) +
              _inc(log, SSTR_COUNT) + b'\xC2\x08\x00')
        _hook(h, FLOAT_GET, _tag(log, FGET_OP) + _store_ecx(log, FGET_SELF) +
              _arg(4, log + FGET_KEY) + _inc(log, FGET_COUNT) +
              b'\xD9\x05' + _dword(fval) + b'\xC2\x04\x00')
        _hook(h, FLOAT_SET, _tag(log, FSET_OP) + _store_ecx(log, FSET_SELF) +
              _arg(4, log + FSET_KEY) + _arg(8, log + FSET_VALUE) + _inc(log, FSET_COUNT) +
              b'\xC2\x08\x00')
        _import(h, STR_SLOT, STR_SYM, _tag(log, SCTOR_OP) + _store_ecx(log, SCTOR_SELF) +
                _arg(4, log + SCTOR_LITERAL) + _inc(log, SCTOR_COUNT) + b'\x8B\xC1\xC2\x04\x00')
        _import(h, STR_DTOR_SLOT, STR_DTOR_SYM, _tag(log, SDTOR_OP) +
                _store_ecx(log, SDTOR_SELF) + _inc(log, SDTOR_COUNT) + b'\xC3')
        _hook(h, UPDATE_STATE, _tag(log, UPD_OP) + _store_ecx(log, UPD_SELF) +
              _inc(log, UPD_COUNT) + b'\xC3')
        configure = _stub(h, _tag(log, CONF_OP) + _store_ecx(log, CONF_SELF) +
                          _arg(4, log + CONF_NAME) + _arg(8, log + CONF_TABLE) +
                          _arg(0xC, log + CONF_FLAG) + _inc(log, CONF_COUNT) + b'\xC2\x0C\x00')
        h.uc.mem_write(scene_vt + 0x3c, _dword(configure))
        release = _stub(h, b'\xFF\x05' + _dword(log + EXTRA_COUNT) + b'\xC2\x04\x00')
        h.uc.mem_write(old_vt, _dword(release))

        diffs = h.compare(fn, args=args, regs={UC_X86_REG_ECX: self_}, ret=None, mem=False)
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        result = h.call(fn, args=args, regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']]
        problems = []
        if _u32(h, self_ + 0x110) != scene or _u32(h, self_ + 0x114) != OLD_FIELD:
            problems.append('scene fields are wrong')
        if _u32(h, self_ + 0x118) != 2:
            problems.append('state +0x118 is not 2')
        if _u32(h, scene + 8) != REFCOUNT:
            problems.append('scene reference count changed')
        if _u32(h, game + 0xac) != 5:
            problems.append('game state is not 5')
        if _u32(h, log + EXTRA_COUNT):
            problems.append('the old scene was released')
        got_order = [_u32(h, log + ORDER + 4 * i) for i in range(len(WANT_ORDER))]
        if got_order != WANT_ORDER:
            problems.append('call order is %s, want %s' % (got_order, WANT_ORDER))
        if _u32(h, log + ORDER + 4 * len(WANT_ORDER)):
            problems.append('unexpected extra call')
        gets = [_u32(h, log + GET_OUT + 4 * i) for i in range(5)]
        if len(set(gets[:3])) != 3 or len(set(gets[3:])) != 2:
            problems.append('lookup outputs are not distinct: %s' % (gets,))
        named = [_u32(h, log + NAMED_SELF + 4 * i) for i in range(2)]
        expected = ((NEW_SIZE, 0x194, 'allocation size'), (NEW_COUNT, 1, 'allocation calls'),
                    (SCENE_SELF, scene, 'scene constructor self'), (SCENE_FLAG, 1, 'scene constructor flag'),
                    (SCENE_COUNT, 1, 'scene constructor calls'),
                    (TCTOR_ARG, 0, 'table constructor flag'), (TCTOR_COUNT, 1, 'table constructor calls'),
                    (NAMED_COUNT, 2, 'named table calls'),
                    (GET_COUNT, 5, 'lookup calls'),
                    (GET_SELF, named[0], 'first lookup self'),
                    (GET_SELF + 4, gets[0], 'second lookup self'),
                    (GET_SELF + 8, gets[1], 'third lookup self'),
                    (GET_SELF + 0xC, named[1], 'fourth lookup self'),
                    (GET_SELF + 0x10, gets[3], 'fifth lookup self'),
                    (GET_KEY, LIT_HERO, 'first lookup key'),
                    (GET_KEY + 4, LIT_BATTLE, 'second lookup key'),
                    (GET_KEY + 8, LIT_MAGIC, 'third lookup key'),
                    (GET_KEY + 0xC, LIT_HERO, 'fourth lookup key'),
                    (GET_KEY + 0x10, LIT_BATTLE, 'fifth lookup key'),
                    (SET_COUNT, 1, 'table setter calls'),
                    (SET_KEY, LIT_MAGIC, 'setter key'), (SET_VALUE, gets[2], 'setter value'),
                    (DTOR_COUNT, 8, 'table destructor calls'),
                    (SSTR_COUNT, 2, 'string setter calls'),
                    (SSTR_KEY, LIT_SCENE, 'scene string key'), (SSTR_VALUE, SCENE_FUNCS, 'scene string value'),
                    (FGET_SELF, gets[4], 'float lookup self'), (FGET_KEY, LIT_INTELLIGENCE, 'float lookup key'),
                    (FGET_COUNT, 1, 'float lookup calls'),
                    (FSET_KEY, LIT_CUR_INT, 'float setter key'), (FSET_COUNT, 1, 'float setter calls'),
                    (SCTOR_LITERAL, LIT_SPELL_BOOK, 'spell book literal'), (SCTOR_COUNT, 1, 'string construction calls'),
                    (CONF_SELF, scene, 'virtual self'), (CONF_NAME, _u32(h, log + SCTOR_SELF), 'virtual string'),
                    (CONF_TABLE, _u32(h, log + TCTOR_SELF), 'virtual table'),
                    (CONF_FLAG, 1, 'virtual flag'), (CONF_COUNT, 1, 'virtual calls'),
                    (SDTOR_SELF, _u32(h, log + SCTOR_SELF), 'string destructor self'),
                    (SDTOR_COUNT, 1, 'string destructor calls'),
                    (UPD_SELF, update, 'state update self'), (UPD_COUNT, 1, 'state update calls'))
        for offset, want, label in expected:
            got = _u32(h, log + offset)
            if got != want:
                problems.append('%s is %#x, want %#x' % (label, got, want))
        setters = [_u32(h, log + SET_SELF + 4 * i) for i in range(1)]
        if setters != [_u32(h, log + TCTOR_SELF)]:
            problems.append('setter receivers are %s' % (setters,))
        fsetters = [_u32(h, log + FSET_SELF + 4 * i) for i in range(1)]
        if fsetters != [_u32(h, log + TCTOR_SELF)]:
            problems.append('float setter receivers are %s' % (fsetters,))
        strings = [(_u32(h, log + SSTR_KEY + 4 * i), _u32(h, log + SSTR_VALUE + 4 * i)) for i in range(2)]
        if strings != [(LIT_SCENE, SCENE_FUNCS), (LIT_UNIT_NAME, LIT_HERO)]:
            problems.append('string pairs are %s' % (strings,))
        if [_u32(h, log + NAMED_NAME + 4 * i) for i in range(2)] != [LIT_UNIT, LIT_UNIT]:
            problems.append('named table names are wrong')
        receivers = [_u32(h, log + DTOR_SELF + 4 * i) for i in range(8)]
        if receivers != [gets[2], gets[1], gets[0], named[0], gets[4], gets[3], named[1],
                         _u32(h, log + TCTOR_SELF)]:
            problems.append('table destructor receivers are %s' % (receivers,))
        if _u32(h, log + FSET_VALUE) != 0x3FC00000:
            problems.append('float value is %#x, want 0x3FC00000' % _u32(h, log + FSET_VALUE))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_scripted_scene_with_argument(h):
    return _run(h, FN_ARG, [0xBEEF1234])


def test_scripted_scene_without_argument(h):
    return _run(h, FN_PLAIN, [])
