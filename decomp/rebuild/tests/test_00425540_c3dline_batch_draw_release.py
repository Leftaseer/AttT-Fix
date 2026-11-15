"""0x00425540 (ECX = the 3D line, ret 0): the batch draw with the world transform update first (0x004AC890).  The line
effect at 0x006C870C begins its passes (slot 0x18, the pass count handed in and replaced) and for each pass selects it
(slot 0x20), sets the texture factor (+0x1C8) and z test (+0x1CC) through slot 0xE4 of the device at 0x006C8C10,
streams the vertex buffer at +0x1C4 (slot 0x190), draws a one-segment line list (slot 0x144) and ends the pass (slot
0x24); slot 0x1C closes and its value is returned.  Every callee is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00425540
RELEASE = 0x004AC890
FX_GLOBAL = 0x006C870C
DEV_GLOBAL = 0x006C8C10

L_COUNT = 0x00
L_EVENTS = 0x10
L_PASSES_IN = 0x300
L_FX_THIS = 0x304
L_DEV = 0x308
LOG_SIZE = 0x320

EV_BEGIN = 1
EV_SELECT = 2
EV_RS = 3
EV_RSV = 4
EV_SETSS = 5
EV_STRIDE = 6
EV_DRAW = 7
EV_DRAWCOUNT = 8
EV_END = 9
EV_CLOSE = 10
EV_RELEASE = 11

FACTOR = 0x11223344
VB = 0x77665544

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


def _event_head(log, code):
    return (b'\xFF\x05' + _dword(log + L_COUNT)                          # inc [count]
            + b'\xA1' + _dword(log + L_COUNT)                            # mov eax, [count]
            + b'\x48'                                                    # dec eax (event index)
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)                   # lea edx, [eax*8 + events]
            + b'\xC7\x82' + _dword(0) + _dword(code))                    # mov dword [edx], code


def _ev(log, code, load, tail):
    return _event_head(log, code) + load + tail


def _from_stack(n):
    return b'\x8B\x44\x24' + bytes([n]) + b'\x89\x82' + _dword(4)        # eax = [esp+n]; [edx+4] = eax


def _imm(v):
    return b'\xC7\x82' + _dword(4) + _dword(v)                           # mov dword [edx+4], v


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_00425540(h):
    heap0 = h.heap_ptr
    globals0 = bytes(h.uc.mem_read(FX_GLOBAL, 8))
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        release = _stub(h,
                        _event_head(log, EV_RELEASE)
                        + b'\x89\x8A' + _dword(4)                      # ecx -> value
                        + b'\xC3')                                    # ret
        _patch(h, RELEASE, b'\xE9' + struct.pack('<i', release - (RELEASE + 5)))
        fx_self = b'\x89\x0D' + _dword(log + L_FX_THIS)                  # mov [log+94], ecx
        dev_self = b'\x8B\x44\x24\x04\xA3' + _dword(log + L_DEV)         # mov eax, [esp+4]; [log+98] = eax
        begin = _stub(h,
                      fx_self
                      + b'\x8B\x44\x24\x04'                              # eax = passes*
                      + b'\x8B\x15' + _dword(log + L_PASSES_IN)          # edx = the pass count
                      + b'\x89\x10'                                      # *passes = edx
                      + _ev(log, EV_BEGIN, _from_stack(8), b'\xC2\x08\x00'))   # flags
        select = _stub(h, fx_self + _ev(log, EV_SELECT, _from_stack(4), b'\xC2\x04\x00'))
        end = _stub(h, fx_self + _ev(log, EV_END, _imm(0), b'\xC3'))
        close = _stub(h, _ev(log, EV_CLOSE, _imm(0), b'\xB8' + _dword(0x12345678) + b'\xC3'))
        setrs = _stub(h,
                      dev_self
                      + _ev(log, EV_RS, _from_stack(8), b'')             # state
                      + _ev(log, EV_RSV, _from_stack(12), b'\xC2\x0C\x00'))  # value
        setss = _stub(h,
                      dev_self
                      + _ev(log, EV_SETSS, _from_stack(12), b'')         # vertex buffer
                      + _ev(log, EV_STRIDE, _from_stack(20), b'\xC2\x14\x00'))  # stride
        draw = _stub(h,
                     dev_self
                     + _ev(log, EV_DRAW, _from_stack(8), b'')            # primitive type
                     + _ev(log, EV_DRAWCOUNT, _from_stack(16), b'\xC2\x10\x00'))  # count
        ftable = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(ftable + 0x18, _dword(begin))
        h.uc.mem_write(ftable + 0x1C, _dword(close))
        h.uc.mem_write(ftable + 0x20, _dword(select))
        h.uc.mem_write(ftable + 0x24, _dword(end))
        dtable = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(dtable + 0xE4, _dword(setrs))
        h.uc.mem_write(dtable + 0x144, _dword(draw))
        h.uc.mem_write(dtable + 0x190, _dword(setss))
        fx = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(fx, _dword(ftable))
        dev = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(dev, _dword(dtable))
        obj = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(obj + 0x1c4, _dword(VB))
        h.uc.mem_write(obj + 0x1c8, _dword(FACTOR))

        for name, passes, zflag in (('two', 2, 1), ('none', 0, 0)):
            def setup():
                h.uc.mem_write(FX_GLOBAL, _dword(fx))
                h.uc.mem_write(DEV_GLOBAL, _dword(dev))
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + L_PASSES_IN, _dword(passes))
                h.uc.mem_write(obj + 0x1cc, bytes([zflag]))

            expected = [(EV_RELEASE, obj), (EV_BEGIN, 0)]
            for i in range(passes):
                expected += [(EV_SELECT, i), (EV_RS, 0x3c), (EV_RSV, FACTOR), (EV_RS, 7), (EV_RSV, zflag),
                             (EV_SETSS, VB), (EV_STRIDE, 0xc), (EV_DRAW, 2), (EV_DRAWCOUNT, 1), (EV_END, 0)]
            expected.append((EV_CLOSE, 0))

            setup()
            diffs = h.compare(THIS, regs={UC_X86_REG_ECX: obj}, ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(THIS, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            got = _events(h, log)
            if got != expected:
                return ['%s: events %r, expected %r' % (name, got, expected)]
            if _u32(h, log + L_FX_THIS) != fx:
                return ['%s: the effect was called on %08X' % (name, _u32(h, log + L_FX_THIS))]
            if res['eax'] != 0x12345678:
                return ['%s: returned %08X' % (name, res['eax'])]
            if passes and _u32(h, log + L_DEV) != dev:
                return ['%s: the device was called on %08X' % (name, _u32(h, log + L_DEV))]
            h.heap_ptr = heap0
    finally:
        h.uc.mem_write(FX_GLOBAL, globals0)
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
