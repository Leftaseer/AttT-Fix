"""0x004644E0 (ECX = the hero interface at +0x1C8, one stack argument -- the destination table --, ret 4): builds
two script tables (0x00435E00, pool 0).  The inner "pos" table gets the hero's x (+0x64 = -0x164), z (+0x6C =
-0x15C) and "roty" (+0x78 = -0x150) as floats (0x0057BC80, keys 0x6098D0 / 0x6098C8 / 0x60C098); the outer table
takes it as "pos" (0x0057BF50, 0x6098E8) and the class "type" (0x68A2C4) as the float of the interface's +0x2E0;
the argument receives the outer table as "HeroPos" (0x60C090).  The temporaries are destroyed in reverse order
(0x004220A0) and the interface is returned.  The constructor, both table writers and the destructor are stubs that
log what they see; the local table addresses are learned from the log."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004644E0
CTOR = 0x00435E00
SETF = 0x0057BC80
SETT = 0x0057BF50
DTOR = 0x004220A0

N_CTOR = 0x00
CTOR_ARR = 0x04            # 2 records of (table, pool)
N_SETF = 0x14
SETF_ARR = 0x18            # 4 records of (table, key, float bits)
N_SETT = 0x48
SETT_ARR = 0x4C            # 2 records of (table, key, value)
N_DTOR = 0x64
DTOR_ARR = 0x68            # 2 records of table
LOG_SIZE = 0x70

KEY_X = 0x006098D0
KEY_Z = 0x006098C8
KEY_ROTY = 0x0060C098
KEY_POS = 0x006098E8
KEY_TYPE = 0x0068A2C4
KEY_HEROPOS = 0x0060C090

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


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
    target = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', target - (address + 5)))


def test_004644E0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, CTOR,
                     b'\xA1' + _dword(log + N_CTOR)                            # eax = count
                     + b'\x89\x0C\xC5' + _dword(log + CTOR_ARR)                      # mov [eax*8+arr], ecx
                     + b'\x8B\x4C\x24\x04'                                     # mov ecx, [esp+4] (pool)
                     + b'\x89\x0C\xC5' + _dword(log + CTOR_ARR + 4)                  # mov [eax*8+arr+4], ecx
                     + b'\xFF\x05' + _dword(log + N_CTOR)                      # inc count
                     + b'\x8B\x04\xC5' + _dword(log + CTOR_ARR)                      # eax = [eax*8+arr] (table)
                     + b'\xC2\x04\x00')                                        # ret 4
        _patch_thunk(h, SETF,
                     b'\xA1' + _dword(log + N_SETF)                            # eax = count
                     + b'\x8D\x15' + _dword(log + SETF_ARR)                          # edx = arr
                     + b'\x8D\x14\xC2'                                         # lea edx, [edx+eax*8]
                     + b'\x8D\x14\x82'                                         # lea edx, [edx+eax*4]
                     + b'\x89\x0A'                                             # [edx] = ecx (table)
                     + b'\x8B\x4C\x24\x04' + b'\x89\x4A\x04'                   # key
                     + b'\x8B\x4C\x24\x08' + b'\x89\x4A\x08'                   # value bits
                     + b'\xFF\x05' + _dword(log + N_SETF)                      # inc count
                     + b'\x8B\x04\xC5' + _dword(log + SETF_ARR)                      # eax = table
                     + b'\xC2\x08\x00')                                        # ret 8
        _patch_thunk(h, SETT,
                     b'\xA1' + _dword(log + N_SETT)
                     + b'\x8D\x15' + _dword(log + SETT_ARR)
                     + b'\x8D\x14\xC2' + b'\x8D\x14\x82'
                     + b'\x89\x0A'
                     + b'\x8B\x4C\x24\x04' + b'\x89\x4A\x04'
                     + b'\x8B\x4C\x24\x08' + b'\x89\x4A\x08'
                     + b'\xFF\x05' + _dword(log + N_SETT)
                     + b'\x8B\x04\xC5' + _dword(log + SETT_ARR)
                     + b'\xC2\x08\x00')
        _patch_thunk(h, DTOR,
                     b'\xA1' + _dword(log + N_DTOR)
                     + b'\x89\x0C\x85' + _dword(log + DTOR_ARR)                      # mov [eax*4+arr], ecx
                     + b'\xFF\x05' + _dword(log + N_DTOR)
                     + b'\x8B\xC1'                                             # eax = ecx
                     + b'\xC3')                                                # ret

        buf = h.alloc(0x800, bytes(0x800))
        self = buf + 0x200
        save = h.alloc(0x40, bytes(0x40))
        heap_base = h.heap_ptr

        for label, fx, fz, froty, typev in (('plain', 1.5, -2.25, 0.75, 42),
                                            ('other', -10.0, 3.5, 179.5, -7)):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(buf, bytes(0x800))
                h.uc.mem_write(self - 0x164, struct.pack('<f', fx))
                h.uc.mem_write(self - 0x15c, struct.pack('<f', fz))
                h.uc.mem_write(self - 0x150, struct.pack('<f', froty))
                h.uc.mem_write(self + 0x2e0, struct.pack('<i', typev))

            h.heap_ptr = heap_base
            setup()
            diffs = h.compare(THIS, args=[save], regs={UC_X86_REG_ECX: self}, ret=None, mem=False)
            if diffs:
                return ['%s: %s' % (label, d) for d in diffs]
            h.heap_ptr = heap_base
            setup()
            res = h.call(THIS, args=[save], regs={UC_X86_REG_ECX: self})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (label, res['fault'])]
            if res['esp'] != 8:
                return ['%s: stack delta %d, not 8' % (label, res['esp'])]
            if _u32(h, log + N_CTOR) != 2 or _u32(h, log + N_SETF) != 4 \
                    or _u32(h, log + N_SETT) != 2 or _u32(h, log + N_DTOR) != 2:
                return ['%s: %d/%d/%d/%d ctor/setf/sett/dtor calls'
                        % (label, _u32(h, log + N_CTOR), _u32(h, log + N_SETF),
                           _u32(h, log + N_SETT), _u32(h, log + N_DTOR))]
            hero = _u32(h, log + CTOR_ARR)
            pos = _u32(h, log + CTOR_ARR + 8)
            if not hero or not pos or hero == pos:
                return ['%s: tables %08X %08X' % (label, hero, pos)]
            if _u32(h, log + CTOR_ARR + 4) != 0 or _u32(h, log + CTOR_ARR + 12) != 0:
                return ['%s: pools %d %d' % (label, _u32(h, log + CTOR_ARR + 4), _u32(h, log + CTOR_ARR + 12))]
            expect = ((pos, KEY_X, fx), (pos, KEY_Z, fz), (pos, KEY_ROTY, froty),
                      (hero, KEY_TYPE, float(typev)))
            for i, (tbl, key, val) in enumerate(expect):
                rec = log + SETF_ARR + i * 12
                got = (_u32(h, rec), _u32(h, rec + 4), _f32(h, rec + 8))
                if got != (tbl, key, val):
                    return ['%s: setf %d saw %08X %08X %g, expected %08X %08X %g'
                            % ((label, i) + got + (tbl, key, val))]
            for i, (tbl, key, val) in enumerate(((hero, KEY_POS, pos), (save, KEY_HEROPOS, hero))):
                rec = log + SETT_ARR + i * 12
                got = (_u32(h, rec), _u32(h, rec + 4), _u32(h, rec + 8))
                if got != (tbl, key, val):
                    return ['%s: sett %d saw %08X %08X %08X, expected %08X %08X %08X'
                            % ((label, i) + got + (tbl, key, val))]
            if _u32(h, log + DTOR_ARR) != pos or _u32(h, log + DTOR_ARR + 4) != hero:
                return ['%s: destroyed %08X %08X, expected %08X %08X'
                        % (label, _u32(h, log + DTOR_ARR), _u32(h, log + DTOR_ARR + 4), pos, hero)]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
