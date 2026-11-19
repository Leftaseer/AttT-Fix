"""0x004CAA00 (ECX = the sprite object, one stack argument -- the D3D device, ret 4): sets FVF 0x144, stores the
device at +8 and clears +0x10, creates a 0xA8-byte vertex buffer through device slot 0x68 and reports the HRESULT
(0x00458940 with ".\\Sprite.cpp" and line 0x11), locks it through slot 0x2C (offset 0, size 0, flags 0), writes the
colour and texture coordinates of six 0x1C-byte vertices, unlocks through slot 0x30, writes the 100 x 100 rectangle
(0x004CA820), and stores the "Movie" lookup from the 0x006C8714 manager at +0x14.  The device, buffer, HRESULT
report, rectangle writer, string functions and lookup are stubs recording a call log; the locked data buffer is
checked byte for byte."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004CAA00
CHECK = 0x00458940
STRING_CTOR_SLOT = 0x00607324
STRING_DTOR_SLOT = 0x00607330
STRING_CTOR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
STRING_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
RECT = 0x004CA820
LOOKUP = 0x00448F10
MANAGER_SLOT = 0x006C8714
MOVIE = 0x00611CCC
SPRITE_FILE = 0x00611CD4
SPRITE_LINE = 0x11
FVF = 0x144
LENGTH = 0xA8
POOL_MANAGED = 1
USAGE_WRITEONLY = 8
LOOKUP_RESULT = 0x12345678

CREATE_OP = 1
CHECK_OP = 2
LOCK_OP = 3
UNLOCK_OP = 4
RECT_OP = 5
STR_CTOR_OP = 6
LOOKUP_OP = 7
STR_DTOR_OP = 8

STRIDE = 0x1C
COLOR = 0xFFFFFFFF
UV = [(0x00000000, 0x00000000), (0x3F800000, 0x00000000), (0x3F800000, 0x3F800000),
      (0x00000000, 0x3F800000), (0x00000000, 0x00000000), (0x3F800000, 0x3F800000)]
RECT_FLOATS = (0x00000000, 0x00000000, 0x42C80000, 0x42C80000)

LOG = 0x00
LOG_SIZE = 0x400
REC = 0x20

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


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _open(base, op):
    return (b'\x8B\x15' + _dword(base)                 # edx = count
            + b'\xC1\xE2\x05'                          # * 32
            + b'\x81\xC2' + _dword(base + 4)           # + first record
            + b'\xC7\x02' + _dword(op))                # record.op


def _field(field, source):
    if source == 'ecx':
        return b'\x89\x4A' + bytes([field])
    return b'\x8B\x44\x24' + bytes([source]) + b'\x89\x42' + bytes([field])


def _close(base):
    return b'\xFF\x05' + _dword(base)


def test_004CAA00(h):
    heap0 = h.heap_ptr
    try:
        base = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        data = h.alloc(0x100, b'\xCC' * 0x100)
        vb = h.alloc(0x20, bytes(0x20))
        device = h.alloc(0x20, bytes(0x20))
        mgr = h.alloc(0x20, bytes(0x20))

        create = _stub(h, _open(base, CREATE_OP) + _field(4, 0x04) + _field(8, 0x08) + _field(12, 0x0C)
                       + _field(16, 0x10) + _field(20, 0x14) + _field(24, 0x18) + _field(28, 0x1C)
                       + _close(base)
                       + b'\x8B\x54\x24\x18'                       # edx = vertex buffer slot
                       + b'\xC7\x02' + _dword(vb)                  # *slot = vb
                       + b'\x31\xC0' + b'\xC2\x1C\x00')
        lock = _stub(h, _open(base, LOCK_OP) + _field(4, 0x04) + _field(8, 0x08) + _field(12, 0x0C)
                     + _field(16, 0x10) + _field(20, 0x14)
                     + _close(base)
                     + b'\x8B\x54\x24\x10'
                     + b'\xC7\x02' + _dword(data)
                     + b'\x31\xC0' + b'\xC2\x14\x00')
        unlock = _stub(h, _open(base, UNLOCK_OP) + _field(4, 0x04) + _close(base) + b'\x31\xC0' + b'\xC2\x04\x00')
        _patch(h, CHECK, _open(base, CHECK_OP) + _field(4, 0x04) + _field(8, 0x08) + _field(12, 0x0C)
               + _close(base) + b'\xC3')
        _patch(h, RECT, _open(base, RECT_OP) + b'\x89\x4A\x04' + _field(8, 0x04) + _field(12, 0x08)
               + _field(16, 0x0C) + _field(20, 0x10)
               + _close(base) + b'\xC2\x10\x00')
        _patch_import(h, STRING_CTOR_SLOT, STRING_CTOR_SYM,
                      _open(base, STR_CTOR_OP) + b'\x89\x4A\x04' + _field(8, 0x04) + _close(base)
                      + b'\x8B\xC1' + b'\xC6\x41\x04\x00' + b'\xC7\x41\x14\x00\x00\x00\x00'
                      + b'\xC7\x41\x18\x0F\x00\x00\x00' + b'\xC2\x04\x00')
        _patch_import(h, STRING_DTOR_SLOT, STRING_DTOR_SYM,
                      _open(base, STR_DTOR_OP) + b'\x89\x4A\x04' + _close(base) + b'\xC3')
        _patch(h, LOOKUP, _open(base, LOOKUP_OP) + b'\x89\x4A\x04' + _field(8, 0x04) + _close(base)
               + b'\xB8' + _dword(LOOKUP_RESULT) + b'\xC2\x04\x00')

        dev_vt = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(dev_vt + 0x68, _dword(create))
        h.uc.mem_write(device, _dword(dev_vt))
        vb_vt = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(vb_vt + 0x2C, _dword(lock))
        h.uc.mem_write(vb_vt + 0x30, _dword(unlock))
        h.uc.mem_write(vb, _dword(vb_vt))

        self = h.alloc(0x40, b'\xA5' * 0x40)
        zeros = bytes(LOG_SIZE)

        def setup():
            h.uc.mem_write(base, zeros)
            h.uc.mem_write(data, b'\xCC' * 0x100)
            h.uc.mem_write(self, b'\xA5' * 0x40)
            h.uc.mem_write(device, _dword(dev_vt))
            h.uc.mem_write(vb, _dword(vb_vt))
            h.uc.mem_write(MANAGER_SLOT, _dword(mgr))

        setup()
        diffs = h.compare(THIS, args=[device], regs={UC_X86_REG_ECX: self}, ret='eax', mem=False)
        if diffs:
            return ['compare: %s' % d for d in diffs]
        setup()
        res = h.call(THIS, args=[device], regs={UC_X86_REG_ECX: self})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['esp'] != 8:
            return ['stack delta %d, not 8' % res['esp']]
        if res['eax'] != self:
            return ['returned %08X, expected %08X' % (res['eax'], self)]

        n = _u32(h, base)
        if n != 8:
            return ['%d calls recorded, not 8' % n]
        recs = []
        for i in range(n):
            r = base + 4 + REC * i
            recs.append([_u32(h, r + 4 * j) for j in range(8)])

        want = [
            [CREATE_OP, device, LENGTH, USAGE_WRITEONLY, FVF, POOL_MANAGED, self + 4, 0],
            [CHECK_OP, 0, SPRITE_FILE, SPRITE_LINE, 0, 0, 0, 0],
            [LOCK_OP, vb, 0, 0, None, 0, 0, 0],
            [UNLOCK_OP, vb, 0, 0, 0, 0, 0, 0],
            [RECT_OP, self, RECT_FLOATS[0], RECT_FLOATS[1], RECT_FLOATS[2], RECT_FLOATS[3], 0, 0],
            [STR_CTOR_OP, None, MOVIE, 0, 0, 0, 0, 0],
            [LOOKUP_OP, mgr, None, 0, 0, 0, 0, 0],
            [STR_DTOR_OP, None, 0, 0, 0, 0, 0, 0],
        ]
        string = recs[5][1]
        if string == 0:
            return ['string constructor got no object']
        want[2][4] = recs[2][4]                              # the locked-data slot is a stack address
        if want[2][4] == 0:
            return ['lock got no data pointer slot']
        want[5][1] = string
        want[6][2] = string
        want[7][1] = string
        for i, (got, exp) in enumerate(zip(recs, want)):
            if got != exp:
                return ['call %d: %s, expected %s' % (i, ['%08X' % v for v in got], ['%08X' % v for v in exp])]

        pattern = bytearray(b'\xCC' * 0x100)
        for i, (u, v) in enumerate(UV):
            p = STRIDE * i
            pattern[p + 0x10:p + 0x14] = _dword(COLOR)
            pattern[p + 0x14:p + 0x18] = _dword(u)
            pattern[p + 0x18:p + 0x1C] = _dword(v)
        got = bytes(h.uc.mem_read(data, 0x100))
        if got != bytes(pattern):
            return ['vertex data %s, expected %s' % (got[:0x50].hex(), bytes(pattern)[:0x50].hex())]

        if _u32(h, self) != FVF:
            return ['FVF %08X' % _u32(h, self)]
        if _u32(h, self + 8) != device:
            return ['device %08X' % _u32(h, self + 8)]
        if h.uc.mem_read(self + 0x10, 1) != b'\x00':
            return ['+0x10 not cleared']
        if _u32(h, self + 0x14) != LOOKUP_RESULT:
            return ['lookup result %08X' % _u32(h, self + 0x14)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
