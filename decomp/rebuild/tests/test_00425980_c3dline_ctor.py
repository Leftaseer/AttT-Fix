"""0x00425980 (ECX = the new C3DLine, 7 dwords, ret 0x1C): the constructor.  An empty name string is built, handed to
the CRenderObject3D base constructor (0x004AD180, null arguments) and destroyed; the vtable 0x00607DB4 goes to +0,
the z test (+0x1CC) turns on.  The shared line effect (count 0x006C8710) is created on first use - a string from
0x00607E84 names 0x00448F10's result into 0x006C870C - and the count grows either way.  A 0x18-byte vertex buffer
(FVF 2, usage 8, managed pool) is created through slot 0x68 of the device at 0x006C8C10, its result checked by
0x00458940 (line 0x27); the six values go into the buffer through its lock slot 0x2C and unlock slot 0x30, and the
shader value lands at +0x1C8.  A failing lock writes neither.  Returns this.  All callees are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425980
BASE_CTOR = 0x004AD180
EFFECT_FACTORY = 0x00448F10
CHECK_HR = 0x00458940
STR_CTOR_SLOT = 0x00607324
STR_DTOR_SLOT = 0x00607330
NAME_LITERAL = 0x0060FA8B
EFFECT_LITERAL = 0x00607E84
FILE_LITERAL = 0x00607E74
LINE = 0x27
FIELD_VB = 0x006C870C
FIELD_COUNT = 0x006C8710
FIELD_REGISTRY = 0x006C8714
FIELD_DEVICE = 0x006C8C10

STR_CTOR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'

VTABLE = 0x00607DB4

L_COUNT = 0x00
L_EVENTS = 0x10
L_LINE = 0x300
L_USAGE = 0x304
L_FMT = 0x308
L_POOL = 0x30C
L_VB = 0x310
L_VERTICES = 0x314
L_LOCK_HR = 0x318
L_EFFECT_RESULT = 0x31C
LOG_SIZE = 0x340

EV_STR_CTOR = 1
EV_BASE = 2
EV_STR_DTOR = 3
EV_EFFECT = 4
EV_CREATE = 5
EV_CHECK = 6
EV_LOCK = 7
EV_UNLOCK = 8

VALUES = (0x11111111, 0x22222222, 0x33333333, 0x44444444, 0x55555555, 0x66666666, 0x77777777)

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _event_head(log, code):
    return (b'\xFF\x05' + _dword(log + L_COUNT)                          # inc [count]
            + b'\xA1' + _dword(log + L_COUNT)                            # mov eax, [count]
            + b'\x48'                                                    # dec eax (event index)
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)                   # lea edx, [eax*8 + events]
            + b'\xC7\x82' + _dword(0) + _dword(code))                    # mov dword [edx], code


def _event_stub(log, code, value, tail=b'\xC3'):
    return _event_head(log, code) + value + tail


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_00425980(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, STR_CTOR_SLOT, STR_CTOR_SYM,
                      _event_stub(log, EV_STR_CTOR,
                                  b'\x8B\x44\x24\x04\x89\x82' + _dword(4),   # literal -> value
                                  b'\x8B\xC1\xC2\x04\x00'))                  # eax = this; ret 4
        _patch_import(h, STR_DTOR_SLOT, STR_DTOR_SYM,
                      _event_stub(log, EV_STR_DTOR, b'\xC7\x82' + _dword(4) + _dword(0)))
        _patch_thunk(h, BASE_CTOR, _event_stub(log, EV_BASE, b'\x89\x8A' + _dword(4), b'\xC2\x0C\x00'))
        _patch_thunk(h, EFFECT_FACTORY,
                     _event_stub(log, EV_EFFECT,
                                 b'\x89\x8A' + _dword(4)                     # ecx (registry) -> value
                                 + b'\xA1' + _dword(log + L_EFFECT_RESULT),   # eax = result
                                 b'\xC2\x04\x00'))
        _patch_thunk(h, CHECK_HR,
                     _event_stub(log, EV_CHECK,
                                 b'\x8B\x44\x24\x04\x89\x82' + _dword(4)     # hr -> value
                                 + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_LINE),
                                 b'\xC3'))                                   # cdecl
        create = _stub(h,
                       _event_head(log, EV_CREATE)
                       + b'\x8B\x44\x24\x08\x89\x82' + _dword(4)            # length -> value
                       + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_USAGE)    # usage
                       + b'\x8B\x44\x24\x10\xA3' + _dword(log + L_FMT)      # fvf
                       + b'\x8B\x44\x24\x14\xA3' + _dword(log + L_POOL)     # pool
                       + b'\x8B\x44\x24\x18'                                # eax = &vertex buffer
                       + b'\x8B\x15' + _dword(log + L_VB)                   # edx = the buffer
                       + b'\x89\x10'                                        # *field = buffer
                       + b'\x31\xC0'                                        # S_OK
                       + b'\xC2\x1C\x00')                                   # ret 28
        lock = _stub(h,
                     _event_head(log, EV_LOCK)
                     + b'\x8B\x44\x24\x0C\x89\x82' + _dword(4)              # size -> value
                     + b'\x8B\x44\x24\x10'                                  # eax = &data
                     + b'\x8B\x15' + _dword(log + L_VERTICES)               # edx = the vertices
                     + b'\x89\x10'                                          # *out = vertices
                     + b'\xA1' + _dword(log + L_LOCK_HR)                    # eax = hr
                     + b'\xC2\x14\x00')                                     # ret 20
        unlock = _stub(h,
                       _event_head(log, EV_UNLOCK)
                       + b'\xC7\x82' + _dword(4) + _dword(0)
                       + b'\x31\xC0'
                       + b'\xC2\x04\x00')                                   # ret 4
        vtable = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(vtable + 0x2C, _dword(lock))
        h.uc.mem_write(vtable + 0x30, _dword(unlock))
        vb = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(vb, _dword(vtable))
        vertices = h.alloc(0x40, b'\xCC' * 0x40)
        dtable = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(dtable + 0x68, _dword(create))
        dev = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(dev, _dword(dtable))
        registry = h.alloc(0x40, bytes(0x40))
        effect = h.alloc(0x40, b'\x99' * 0x40)
        obj = h.alloc(0x200, b'\xEE' * 0x200)

        for name, refcount, lock_hr in (('first', 0, 0), ('next', 2, -1)):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + L_VB, _dword(vb))
                h.uc.mem_write(log + L_VERTICES, _dword(vertices))
                h.uc.mem_write(log + L_LOCK_HR, _dword(lock_hr & 0xFFFFFFFF))
                h.uc.mem_write(log + L_EFFECT_RESULT, _dword(effect))
                h.uc.mem_write(FIELD_COUNT, _dword(refcount))
                h.uc.mem_write(FIELD_VB, _dword(0))
                h.uc.mem_write(FIELD_REGISTRY, _dword(registry))
                h.uc.mem_write(FIELD_DEVICE, _dword(dev))
                h.uc.mem_write(obj, b'\xEE' * 0x200)
                h.uc.mem_write(vertices, b'\xCC' * 0x40)

            expected = [(EV_STR_CTOR, NAME_LITERAL), (EV_BASE, obj), (EV_STR_DTOR, 0)]
            if not refcount:
                expected += [(EV_STR_CTOR, EFFECT_LITERAL), (EV_EFFECT, registry), (EV_STR_DTOR, 0)]
            expected += [(EV_CREATE, 0x18), (EV_CHECK, 0), (EV_LOCK, 0x18)]
            if lock_hr >= 0:
                expected.append((EV_UNLOCK, 0))

            setup()
            diffs = h.compare(THIS, args=list(VALUES), regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(THIS, args=list(VALUES), regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != obj:
                return ['%s: returned %08X, expected %08X' % (name, res['eax'], obj)]
            got = _events(h, log)
            if got != expected:
                return ['%s: events %r, expected %r' % (name, got, expected)]
            want = [(0x00, VTABLE), (0x1C4, vb)]
            if lock_hr >= 0:
                want += [(0x1C8, VALUES[6])]
            for field, value in want:
                if _u32(h, obj + field) != value:
                    return ['%s: +%02X is %08X, expected %08X' % (name, field, _u32(h, obj + field), value)]
            if h.uc.mem_read(obj + 0x1CC, 1) != b'\x01':
                return ['%s: the z test byte is %02X' % (name, h.uc.mem_read(obj + 0x1CC, 1)[0])]
            if lock_hr < 0 and _u32(h, obj + 0x1C8) != 0xEEEEEEEE:
                return ['%s: the shader value was stored on a failed lock' % name]
            if _u32(h, FIELD_COUNT) != refcount + 1:
                return ['%s: the effect count is %d' % (name, _u32(h, FIELD_COUNT))]
            if not refcount and _u32(h, FIELD_VB) != effect:
                return ['%s: the effect is %08X' % (name, _u32(h, FIELD_VB))]
            if (_u32(h, log + L_USAGE) != 8 or _u32(h, log + L_FMT) != 2
                    or _u32(h, log + L_POOL) != 1 or _u32(h, log + L_LINE) != LINE):
                return ['%s: created with %d/%d/%d, checked at line %d'
                        % (name, _u32(h, log + L_USAGE), _u32(h, log + L_FMT),
                           _u32(h, log + L_POOL), _u32(h, log + L_LINE))]
            if lock_hr >= 0:
                got6 = struct.unpack('<6I', h.uc.mem_read(vertices, 24))
                if got6 != VALUES[:6]:
                    return ['%s: the vertices are %r' % (name, got6)]
            elif h.uc.mem_read(vertices, 4) != b'\xCC' * 4:
                return ['%s: the vertices were written on a failed lock' % name]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
