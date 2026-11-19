"""0x00465950 (thiscall + ECX, ret 8; the second stack argument is unused): CHero::CHero.  The base constructor
0x004AD180 receives the "WorldUnit" string (built by the msvcp80 import at 0x00607324, destroyed by 0x00607330), the
argument and a zero.  +0x1C4 is given vtable 0x0060B900 before 0x004B40E0 initialises +0x1C8, 0x004B8640(this+0x1D0,
1) follows, 0x004AD9B0(this+0x230) comes next, then the real vtables 0x0060C1AC/0x0060C1A0/0x0060C18C/0x0060C180 and
the cleared fields are written.  +0x4CC and +0x4D8 take the empty lists 0x00464630 / 0x004C2F40 put into +4 (with
+8 cleared), +0x4E8 a default std::string.  A hero already at 0x006C8EF8 raises Hero.cpp:0x39 through 0x00421220
and 0x005E3EC0 (throw info 0x0069916C, message 0x0060C150).  The reader at +0x2C is then released through vtable
+0x14, +0x1D8/+0x22C are cleared, the new hero is published, the timer fields get 1000/100/123 and the object at
[0x006C8C10] fills a capabilities block through vtable +0x1C: its dword +0xA4 (vs. unsigned 2, tested with
0x80000000) becomes the byte +0x1E8.  All callees are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00465950
SINGLETON = 0x006C8EF8
DEV_SLOT = 0x006C8C10
BASE = 0x004AD180
SUB1 = 0x004B40E0
SUB2 = 0x004B8640
SUB3 = 0x004AD9B0
LIST1 = 0x00464630
LIST2 = 0x004C2F40
EXC_CTOR = 0x00421220
THROW = 0x005E3EC0
STR_CTOR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
STR_DEF_SLOT = 0x006071E0

STR_CTOR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
STR_DEF_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'

NAME_LIT = 0x0060C26C               # "WorldUnit"
THROW_LIT = 0x0060C150
FILE_LIT = 0x0060C144               # ".\\Hero.cpp"
THROW_INFO = 0x0069916C
LINE = 0x39

WT_MAIN = 0x0060C1AC
WT_PRE = 0x0060B900
WT_A = 0x0060C1A0
WT_B = 0x0060C18C
WT_C = 0x0060C180
NODE1, NODE2 = 0x00A00010, 0x00A00020
DEF_MARK = 0xDEADBEEF
OBJ_SIZE = 0x500
UNTOUCHED = (0x100, 0x1e0, 0x200, 0x220, 0x4e4)

ORDER = 0xA0               # the call-order array follows the fields
C_CTOR, CTOR_DST, CTOR_SRC = 0x04, 0x08, 0x0C
C_DTOR, DTOR_SRC = 0x10, 0x14
C_BASE, B_SELF, B_NAME, B_LIT, B_A1, B_A2 = 0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C
C_S1, S1_SELF, S1_PREV = 0x30, 0x34, 0x38
C_S2, S2_SELF, S2_ARG = 0x3C, 0x40, 0x44
C_S3, S3_SELF = 0x48, 0x4C
C_L1, L1_SELF = 0x50, 0x54
C_L2, L2_SELF = 0x58, 0x5C
C_DEF, DEF_SELF = 0x60, 0x64
C_EXC, EXC_MSG, EXC_FILE, EXC_LINE = 0x68, 0x6C, 0x70, 0x74
C_THROW, THROW_INFO_ARG = 0x78, 0x7C
C_READ, RD_SELF, RD_ARG = 0x80, 0x84, 0x88
C_DEV, DEV_SELF, DEV_CAPS = 0x8C, 0x90, 0x94
LOG_SIZE = 0xE0

OP_CTOR, OP_BASE, OP_DTOR, OP_S1, OP_S2, OP_S3, OP_L1, OP_L2, OP_DEF, OP_EXC, OP_THROW, OP_READ, OP_DEV = \
    range(1, 14)

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


def _patch_import(h, slot, symbol, code):
    stub = _stub(h, code)
    _patch(h, slot, _dword(stub))
    _patch(h, h.symbols[symbol], _dword(stub))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _tag(log, op):
    return b'\x8B\x15' + _dword(log) + b'\xFF\x05' + _dword(log) + \
        b'\xC7\x04\x95' + _dword(log + ORDER) + _dword(op)


def _arg(offset, address):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(address)


def _inc(address):
    return b'\xFF\x05' + _dword(address)


def _ecx_store(address):
    return b'\x89\x0D' + _dword(address)


def _install(h, log):
    _hook(h, BASE, _tag(log, OP_BASE) + _inc(log + C_BASE) + _ecx_store(log + B_SELF) +
          _arg(4, log + B_NAME) + b'\x8B\x00' + b'\xA3' + _dword(log + B_LIT) +
          _arg(8, log + B_A1) + _arg(0xC, log + B_A2) + b'\x8B\xC1' + b'\xC2\x0C\x00')
    _hook(h, SUB1, _tag(log, OP_S1) + _inc(log + C_S1) + _ecx_store(log + S1_SELF) +
          b'\x8B\x41\xFC' + b'\xA3' + _dword(log + S1_PREV) + b'\xC3')
    _hook(h, SUB2, _tag(log, OP_S2) + _inc(log + C_S2) + _ecx_store(log + S2_SELF) +
          _arg(4, log + S2_ARG) + b'\xC2\x04\x00')
    _hook(h, SUB3, _tag(log, OP_S3) + _inc(log + C_S3) + _ecx_store(log + S3_SELF) + b'\xC3')
    _hook(h, LIST1, _tag(log, OP_L1) + _inc(log + C_L1) + _ecx_store(log + L1_SELF) +
          b'\xB8' + _dword(NODE1) + b'\xC3')
    _hook(h, LIST2, _tag(log, OP_L2) + _inc(log + C_L2) + _ecx_store(log + L2_SELF) +
          b'\xB8' + _dword(NODE2) + b'\xC3')
    _hook(h, EXC_CTOR, _tag(log, OP_EXC) + _inc(log + C_EXC) + _arg(4, log + EXC_MSG) +
          b'\x8B\x00' + b'\xA3' + _dword(log + EXC_MSG) + _arg(8, log + EXC_FILE) +
          _arg(0xC, log + EXC_LINE) + b'\x8B\xC1' + b'\xC2\x0C\x00')
    _hook(h, THROW, _tag(log, OP_THROW) + _inc(log + C_THROW) + _arg(8, log + THROW_INFO_ARG) +
          b'\x31\xC0' + b'\xC2\x08\x00')
    _patch_import(h, STR_CTOR_SLOT, STR_CTOR_SYM,
                  _tag(log, OP_CTOR) + _inc(log + C_CTOR) + _ecx_store(log + CTOR_DST) +
                  _arg(4, log + CTOR_SRC) + b'\x89\x01' + b'\x8B\xC1' + b'\xC2\x04\x00')
    _patch_import(h, STR_DTOR_SLOT, STR_DTOR_SYM,
                  _tag(log, OP_DTOR) + _inc(log + C_DTOR) + b'\x8B\x01' +
                  b'\xA3' + _dword(log + DTOR_SRC) + b'\xC3')
    _patch_import(h, STR_DEF_SLOT, STR_DEF_SYM,
                  _tag(log, OP_DEF) + _inc(log + C_DEF) + _ecx_store(log + DEF_SELF) +
                  b'\xC7\x01' + _dword(DEF_MARK) + b'\xC3')


def _vt_stubs(h, log, caps_value):
    read = _stub(h, _tag(log, OP_READ) + _inc(log + C_READ) + _ecx_store(log + RD_SELF) +
                 _arg(4, log + RD_ARG) + b'\xC2\x04\x00')
    dev = _stub(h, _tag(log, OP_DEV) + _inc(log + C_DEV) + _arg(4, log + DEV_SELF) +
                _arg(8, log + DEV_CAPS) + b'\x8B\x4C\x24\x08' + b'\xB8' + _dword(caps_value) +
                b'\x89\x81\xA4\x00\x00\x00' + b'\xC2\x08\x00')
    return read, dev


def _run(h, log, existing, with_reader, caps_value):
    heap0 = h.heap_ptr
    try:
        _install(h, log)
        self_ = h.alloc(OBJ_SIZE, bytes(OBJ_SIZE))
        reader = h.alloc(8, bytes(8))
        dev = h.alloc(8, bytes(8))
        vt_read = h.alloc(0x20, bytes(0x20))
        vt_dev = h.alloc(0x20, bytes(0x20))
        arg1 = h.alloc(4, bytes(4))
        arg2 = h.alloc(4, bytes(4))
        read_stub, dev_stub = _vt_stubs(h, log, caps_value)

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(self_, b'\xAA' * OBJ_SIZE)
            _patch(h, SINGLETON, _dword(existing))
            _patch(h, DEV_SLOT, _dword(dev))
            h.uc.mem_write(reader, _dword(vt_read))
            h.uc.mem_write(dev, _dword(vt_dev))
            h.uc.mem_write(vt_read + 0x14, _dword(read_stub))
            h.uc.mem_write(vt_dev + 0x1C, _dword(dev_stub))
            h.uc.mem_write(self_ + 0x2c, _dword(reader if with_reader else 0))
            h.uc.mem_write(arg1, _dword(0x1111))
            h.uc.mem_write(arg2, _dword(0x2222))

        setup()
        diffs = h.compare(FN, args=[arg1, arg2], regs={UC_X86_REG_ECX: self_}, ret=None, mem=False)
        if diffs:
            return diffs, None
        setup()
        result = h.call(FN, args=[arg1, arg2], regs={UC_X86_REG_ECX: self_})
        if result['fault']:
            return [result['fault']], None
        cnt = _u32(h, log)
        got = {
            'esp': result['esp'], 'eax': result['eax'], 'self': self_,
            'order': [_u32(h, log + ORDER + 4 * i) for i in range(cnt)],
            'ctor': (_u32(h, log + C_CTOR), _u32(h, log + CTOR_DST), _u32(h, log + CTOR_SRC)),
            'dtor': (_u32(h, log + C_DTOR), _u32(h, log + DTOR_SRC)),
            'base': (_u32(h, log + C_BASE), _u32(h, log + B_SELF), _u32(h, log + B_NAME),
                     _u32(h, log + B_LIT), _u32(h, log + B_A1), _u32(h, log + B_A2)),
            's1': (_u32(h, log + C_S1), _u32(h, log + S1_SELF), _u32(h, log + S1_PREV)),
            's2': (_u32(h, log + C_S2), _u32(h, log + S2_SELF), _u32(h, log + S2_ARG)),
            's3': (_u32(h, log + C_S3), _u32(h, log + S3_SELF)),
            'l1': (_u32(h, log + C_L1), _u32(h, log + L1_SELF)),
            'l2': (_u32(h, log + C_L2), _u32(h, log + L2_SELF)),
            'def': (_u32(h, log + C_DEF), _u32(h, log + DEF_SELF)),
            'exc': (_u32(h, log + C_EXC), _u32(h, log + EXC_MSG), _u32(h, log + EXC_FILE),
                    _u32(h, log + EXC_LINE)),
            'throw': (_u32(h, log + C_THROW), _u32(h, log + THROW_INFO_ARG)),
            'read': (_u32(h, log + C_READ), _u32(h, log + RD_SELF), _u32(h, log + RD_ARG)),
            'dev': (_u32(h, log + C_DEV), _u32(h, log + DEV_SELF), _u32(h, log + DEV_CAPS)),
            'reader': reader, 'dev_obj': dev, 'arg1': arg1, 'arg2': arg2,
            'vt': {off: _u32(h, self_ + off) for off in (0x00, 0x1c4, 0x1c8, 0x1d0)},
            'zeroed': {off: _u32(h, self_ + off) for off in
                       (0x1ec, 0x1f0, 0x1f4, 0x1f8, 0x1fc, 0x204, 0x208, 0x20c, 0x214, 0x218, 0x21c,
                        0x1d8, 0x22c, 0x4a8, 0x4bc)},
            'lists': {off: _u32(h, self_ + off) for off in (0x4d0, 0x4d4, 0x4dc, 0x4e0, 0x4e8)},
            'timers': {off: _u32(h, self_ + off) for off in (0x4a4, 0x4ac, 0x4b0)},
            'reader_field': _u32(h, self_ + 0x2c),
            'byte_1e8': bytes(h.uc.mem_read(self_ + 0x1e8, 1))[0],
            'byte_1eb': bytes(h.uc.mem_read(self_ + 0x1eb, 1))[0],
            'untouched': {off: _u32(h, self_ + off) for off in UNTOUCHED},
            'singleton': _u32(h, SINGLETON),
        }
        return [], got
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _check_common(got, name, problems, caps_value, ctor_count, final_lit):
    self_ = got['self']
    if got['esp'] != 0xC:
        problems.append('%s: stack delta is %#x' % (name, got['esp']))
    if got['eax'] != self_:
        problems.append('%s: returned %#x' % (name, got['eax']))
    c = got['ctor']
    if c[0] != ctor_count or c[1] == 0 or c[2] != final_lit:
        problems.append('%s: last string built %s' % (name, tuple(hex(x) for x in c)))
    if got['dtor'] != (1, NAME_LIT):
        problems.append('%s: name destroyed as %s' % (name, tuple(hex(x) for x in got['dtor'])))
    b = got['base']
    if b != (1, self_, b[2], NAME_LIT, got['arg1'], 0):
        problems.append('%s: base constructor %s' % (name, tuple(hex(x) for x in b)))
    if got['s1'] != (1, self_ + 0x1c8, WT_PRE):
        problems.append('%s: sub1 %s' % (name, tuple(hex(x) for x in got['s1'])))
    if got['s2'] != (1, self_ + 0x1d0, 1):
        problems.append('%s: sub2 %s' % (name, tuple(hex(x) for x in got['s2'])))
    if got['s3'] != (1, self_ + 0x230):
        problems.append('%s: sub3 %s' % (name, tuple(hex(x) for x in got['s3'])))
    if got['l1'] != (1, self_ + 0x4cc) or got['l2'] != (1, self_ + 0x4d8):
        problems.append('%s: lists %s/%s' % (name, got['l1'], got['l2']))
    if got['def'] != (1, self_ + 0x4e8):
        problems.append('%s: default string %s' % (name, tuple(hex(x) for x in got['def'])))
    if got['vt'] != {0x00: WT_MAIN, 0x1c4: WT_A, 0x1c8: WT_B, 0x1d0: WT_C}:
        problems.append('%s: vtables %s' % (name, {hex(k): hex(v) for k, v in got['vt'].items()}))
    if any(got['zeroed'].values()):
        problems.append('%s: fields left %s' % (name, {hex(k): hex(v) for k, v in got['zeroed'].items() if v}))
    if got['lists'] != {0x4d0: NODE1, 0x4d4: 0, 0x4dc: NODE2, 0x4e0: 0, 0x4e8: DEF_MARK}:
        problems.append('%s: list fields %s' % (name, {hex(k): hex(v) for k, v in got['lists'].items()}))
    if got['timers'] != {0x4a4: 1000, 0x4ac: 100, 0x4b0: 123}:
        problems.append('%s: timers %s' % (name, {hex(k): v for k, v in got['timers'].items()}))
    if got['byte_1eb'] != 0:
        problems.append('%s: +0x1EB is %#x' % (name, got['byte_1eb']))
    if got['byte_1e8'] != (1 if (caps_value & 0xFFFFFFFF) >= 2 else 0):
        problems.append('%s: +0x1E8 is %#x for caps %#x' % (name, got['byte_1e8'], caps_value))
    if got['singleton'] != self_:
        problems.append('%s: singleton is %#x' % (name, got['singleton']))
    if set(got['untouched'].values()) != {0xAAAAAAAA}:
        problems.append('%s: untouched fields %s' % (name, {hex(k): hex(v) for k, v in got['untouched'].items()}))
    if got['dev'][0] != 1 or got['dev'][1] != got['dev_obj'] or got['dev'][2] == 0:
        problems.append('%s: device caps call %s' % (name, tuple(hex(x) for x in got['dev'])))


def test_plain(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    problems = []
    diffs, got = _run(h, log, 0, False, 0x80000000)
    if diffs:
        return ['plain: %s' % d for d in diffs]
    _check_common(got, 'plain', problems, 0x80000000, 1, NAME_LIT)
    if got['base'][2] != got['ctor'][1]:
        problems.append('plain: base name is not the built string')
    if got['order'] != [OP_CTOR, OP_BASE, OP_DTOR, OP_S1, OP_S2, OP_S3, OP_L1, OP_L2, OP_DEF, OP_DEV]:
        problems.append('plain: call order %s' % (got['order'],))
    if got['exc'][0] or got['throw'][0] or got['read'][0]:
        problems.append('plain: throw/release ran without a reason')
    if got['reader_field'] != 0:
        problems.append('plain: reader field %#x' % got['reader_field'])
    return problems or None


def test_reader_released(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    problems = []
    diffs, got = _run(h, log, 0, True, 0)
    if diffs:
        return ['reader: %s' % d for d in diffs]
    _check_common(got, 'reader', problems, 0, 1, NAME_LIT)
    if got['base'][2] != got['ctor'][1]:
        problems.append('reader: base name is not the built string')
    if got['order'] != [OP_CTOR, OP_BASE, OP_DTOR, OP_S1, OP_S2, OP_S3, OP_L1, OP_L2, OP_DEF,
                        OP_READ, OP_DEV]:
        problems.append('reader: call order %s' % (got['order'],))
    if got['read'] != (1, got['reader'], got['self']):
        problems.append('reader: release %s' % (tuple(hex(x) for x in got['read']),))
    if got['reader_field'] != 0:
        problems.append('reader: field not cleared')
    return problems or None


def test_singleton_throw(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    problems = []
    existing = 0x00B00000
    diffs, got = _run(h, log, existing, False, 0)
    if diffs:
        return ['throw: %s' % d for d in diffs]
    _check_common(got, 'throw', problems, 0, 2, THROW_LIT)
    if got['order'] != [OP_CTOR, OP_BASE, OP_DTOR, OP_S1, OP_S2, OP_S3, OP_L1, OP_L2, OP_DEF,
                        OP_CTOR, OP_EXC, OP_THROW, OP_DEV]:
        problems.append('throw: call order %s' % (got['order'],))
    if got['ctor'][0] != 2:
        problems.append('throw: string built %d times' % got['ctor'][0])
    if got['exc'] != (1, THROW_LIT, FILE_LIT, LINE):
        problems.append('throw: exception %s' % (tuple(hex(x) for x in got['exc']),))
    if got['throw'] != (1, THROW_INFO):
        problems.append('throw: throw info %s' % (tuple(hex(x) for x in got['throw']),))
    return problems or None
