"""0x00436770 (ECX = the camera interface at +0x3C, one stack argument -- the script table, ret 4) exports the
camera as "Camera": 0x00435550 copies the camera record (position / target position / rotation triples, distance,
fov, zNear, zFar, aspect, the two flags and height), a table with x, y, z is stored as "position", reset by
assigning a fresh empty table (0x0057A860), reused for "tgPosition" and "rotation", the scalars are added, and the
argument receives the outer table as "Camera".  Every callee is a stub that appends a (op, table, key, value)
record; table identity is compared relationally because the tables are stack temporaries."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00436770
GETTER = 0x00435550
CTOR = 0x00435E00
SET_FLOAT = 0x0057BC80
SET_TABLE = 0x0057BF50
SET_INT = 0x0057BB20
ASSIGN = 0x0057A860
DTOR = 0x004220A0

X = 0x006098D0
Y = 0x006098CC
Z = 0x006098C8
POSITION = 0x006098BC
TG_POSITION = 0x006098B0
ROTATION = 0x006098A4
DISTANCE = 0x00609898
FOV = 0x00609894
Z_NEAR = 0x0060988C
Z_FAR = 0x00609884
ASPECT = 0x0060987C
ON_GROUND = 0x00609870
HEIGHT = 0x00609868
NEED_TG_HEIGHT = 0x00609858
CAMERA = 0x00609850

CTOR_OP = 1
FLOAT_OP = 2
INT_OP = 3
TABLE_OP = 4
ASSIGN_OP = 5
DTOR_OP = 6

GET_THIS = 0x800
LOG_SIZE = 0x810

ARGS = 0x44
PATTERN = [
    0x3FC00000, 0x40200000, 0x40600000,          # position:   1.5, 2.5, 3.5
    0x40900000, 0x40B00000, 0x40D00000,          # target:     4.5, 5.5, 6.5
    0x40F00000, 0x41080000, 0x41100000,          # rotation:   7.5, 8.5, 9.5
    0x41280000,                                  # distance:  10.5
    0x41380000,                                  # fov:       11.5
    0x41480000,                                  # zNear:     12.5
    0x41580000,                                  # zFar:      13.5
    0x41680000,                                  # aspect:    14.5
    1,                                           # onGround
    0x41780000,                                  # height:    15.5
    2,                                           # needTgHeight
]

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


def _record(base, op):
    return (b'\x8B\x15' + _dword(base)                  # edx = record count
            + b'\xC1\xE2\x04'                           # edx *= 16
            + b'\x81\xC2' + _dword(base + 4)             # edx += first record
            + b'\xC7\x02' + _dword(op)                  # record.op
            + b'\x89\x4A\x04')                          # record.table = ecx


def _arg(offset, field):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\x89\x42' + bytes([field])


def _count(base):
    return b'\xFF\x05' + _dword(base)


def _setter(h, address, base, op):
    _patch(h, address, _record(base, op) + _arg(4, 8) + _arg(8, 12) + _count(base) + b'\xC2\x08\x00')


def test_00436770(h):
    heap0 = h.heap_ptr
    try:
        base = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        get_this = base + GET_THIS
        _patch(h, GETTER, b'\x89\x0D' + _dword(get_this)  # log the camera object
               + b'\x8B\x44\x24\x04'                     # eax = out record
               + b''.join(b'\xC7\x40' + bytes([i * 4]) + _dword(v) for i, v in enumerate(PATTERN))
               + b'\xC2\x04\x00')
        _patch(h, CTOR, _record(base, CTOR_OP) + _count(base) + b'\x89\xC8' + b'\xC2\x04\x00')
        _setter(h, SET_FLOAT, base, FLOAT_OP)
        _setter(h, SET_TABLE, base, TABLE_OP)
        _setter(h, SET_INT, base, INT_OP)
        _patch(h, ASSIGN, _record(base, ASSIGN_OP) + _arg(4, 8) + _count(base) + b'\xC2\x04\x00')
        _patch(h, DTOR, _record(base, DTOR_OP) + _count(base) + b'\xC2\x00\x00')

        self = h.alloc(0x100, b'\xA5' * 0x100)
        save = h.alloc(0x100, b'\x5A' * 0x100)
        zeros = bytes(LOG_SIZE)

        def setup():
            h.uc.mem_write(base, zeros)
            h.uc.mem_write(self, b'\xA5' * 0x100)
            h.uc.mem_write(save, b'\x5A' * 0x100)

        setup()
        diffs = h.compare(THIS, args=[save], regs={UC_X86_REG_ECX: self}, ret=None, mem=False)
        if diffs:
            return ['compare: %s' % d for d in diffs]
        setup()
        res = h.call(THIS, args=[save], regs={UC_X86_REG_ECX: self})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if res['esp'] != 8:
            return ['stack delta %d, not 8' % res['esp']]
        if _u32(h, get_this) != self - 0x3C:
            return ['camera record read from %08X, expected %08X' % (_u32(h, get_this), self - 0x3C)]

        n = _u32(h, base)
        if n != 31:
            return ['%d calls recorded, not 31' % n]

        recs = []
        for i in range(n):
            rec = base + 4 + 16 * i
            recs.append((_u32(h, rec), _u32(h, rec + 4), _u32(h, rec + 8), _u32(h, rec + 12)))
        outer, part, empty1, empty2 = recs[0][1], recs[1][1], recs[6][1], recs[13][1]
        if len({outer, part, save}) != 3 or empty1 in (outer, part) or empty2 in (outer, part):
            return ['unexpected table identity %08X %08X %08X %08X' % (outer, part, empty1, empty2)]

        f = lambda bits: bits
        want = [
            (CTOR_OP, outer, 0, 0),
            (CTOR_OP, part, 0, 0),
            (FLOAT_OP, part, X, PATTERN[0]),
            (FLOAT_OP, part, Y, PATTERN[1]),
            (FLOAT_OP, part, Z, PATTERN[2]),
            (TABLE_OP, outer, POSITION, part),
            (CTOR_OP, empty1, 0, 0),
            (ASSIGN_OP, part, empty1, 0),
            (DTOR_OP, empty1, 0, 0),
            (FLOAT_OP, part, X, PATTERN[3]),
            (FLOAT_OP, part, Y, PATTERN[4]),
            (FLOAT_OP, part, Z, PATTERN[5]),
            (TABLE_OP, outer, TG_POSITION, part),
            (CTOR_OP, empty2, 0, 0),
            (ASSIGN_OP, part, empty2, 0),
            (DTOR_OP, empty2, 0, 0),
            (FLOAT_OP, part, X, PATTERN[6]),
            (FLOAT_OP, part, Y, PATTERN[7]),
            (FLOAT_OP, part, Z, PATTERN[8]),
            (TABLE_OP, outer, ROTATION, part),
            (FLOAT_OP, outer, DISTANCE, PATTERN[9]),
            (FLOAT_OP, outer, FOV, PATTERN[10]),
            (FLOAT_OP, outer, Z_NEAR, PATTERN[11]),
            (FLOAT_OP, outer, Z_FAR, PATTERN[12]),
            (FLOAT_OP, outer, ASPECT, PATTERN[13]),
            (INT_OP, outer, ON_GROUND, PATTERN[14]),
            (FLOAT_OP, outer, HEIGHT, PATTERN[15]),
            (INT_OP, outer, NEED_TG_HEIGHT, PATTERN[16]),
            (TABLE_OP, save, CAMERA, outer),
            (DTOR_OP, part, 0, 0),
            (DTOR_OP, outer, 0, 0),
        ]
        for i, (got, exp) in enumerate(zip(recs, want)):
            if got != exp:
                return ['record %d: %08X %08X %08X %08X, expected %08X %08X %08X %08X'
                        % ((i,) + got + exp)]
        if bytes(h.uc.mem_read(save, 0x100)) != b'\x5A' * 0x100:
            return ['destination table memory modified']
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
