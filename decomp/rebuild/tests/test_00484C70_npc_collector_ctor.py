"""NPCCollector::NPCCollector (0x00484C70): takes the vftable, builds the member at +4, makes the script table at
+0x2C and fills it from the "WorldNPC" table through a temporary table from pool -10002.  Every helper is replaced
by a recording stub; the pool arguments, the member the table is assigned into and the "WorldNPC" name are checked."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x00484C70
MEMBER_BYTE = 0x00484AA0
TABLE_POOL0 = 0x00435E00
ASSIGN = 0x0057A860
TABLE_POOL1 = 0x0045C7E0
QUERY = 0x0057BF50
DTOR = 0x004220A0

VTABLE = 0x0060F628
TABLE_VTABLE = 0x00607CC4
WORLD_NPC = 0x0060F62C
POOL1 = 0xFFFFD8EE

LOG_BYTE_THIS = 0x00
LOG_BYTE_SAME = 0x04
LOG_BYTE_COUNT = 0x08
LOG_POOL0_ARG = 0x0C
LOG_POOL0_COUNT = 0x10
LOG_ASSIGN_THIS = 0x14
LOG_ASSIGN_COUNT = 0x18
LOG_DTOR_COUNT = 0x1C
LOG_POOL1_ARG = 0x20
LOG_POOL1_COUNT = 0x24
LOG_QUERY_NAME = 0x28
LOG_QUERY_MEMBER = 0x2C
LOG_QUERY_COUNT = 0x30
LOG_SIZE = 0x34


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _mov_eax_arg(index):
    return b'\x8B\x44\x24' + bytes([4 * index])


def _store_eax(addr):
    return b'\xA3' + struct.pack('<I', addr)


def _store_ecx(addr):
    return b'\x89\x0D' + struct.pack('<I', addr)


def _inc(addr):
    return b'\xFF\x05' + struct.pack('<I', addr)


def _ret4():
    return b'\xC2\x04\x00'


def _ret8():
    return b'\xC2\x08\x00'


def _patch(h, address, code, saved):
    if address not in saved:
        saved[address] = bytes(h.uc.mem_read(address, 32))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stubs(h, log):
    _patch(h, MEMBER_BYTE,
           _mov_eax_arg(1) + b'\x8B\x54\x24\x08' + b'\x3B\xC2' + b'\x0F\x94\xC0' + b'\x0F\xB6\xC0'
           + _store_eax(log + LOG_BYTE_SAME)
           + _store_ecx(log + LOG_BYTE_THIS)
           + _inc(log + LOG_BYTE_COUNT)
           + _ret8(), _stubs.saved)
    pool0 = (_mov_eax_arg(1) + _store_eax(log + LOG_POOL0_ARG)
             + b'\x89\xC8' + _inc(log + LOG_POOL0_COUNT) + _ret4())
    _patch(h, TABLE_POOL0, pool0, _stubs.saved)
    _patch(h, TABLE_POOL1,
           _mov_eax_arg(1) + _store_eax(log + LOG_POOL1_ARG)
           + b'\x89\xC8' + _inc(log + LOG_POOL1_COUNT) + _ret4(), _stubs.saved)
    _patch(h, ASSIGN, _store_ecx(log + LOG_ASSIGN_THIS) + _inc(log + LOG_ASSIGN_COUNT) + _ret4(), _stubs.saved)
    _patch(h, QUERY,
           _mov_eax_arg(1) + _store_eax(log + LOG_QUERY_NAME)
           + _mov_eax_arg(2) + _store_eax(log + LOG_QUERY_MEMBER)
           + _inc(log + LOG_QUERY_COUNT)
           + _ret8(), _stubs.saved)
    _patch(h, DTOR, _inc(log + LOG_DTOR_COUNT) + b'\xC3', _stubs.saved)


_stubs.saved = {}


def test_npc_collector_ctor(h):
    _stubs.saved = {}
    heap0 = h.heap_ptr
    try:
        for index in range(2):
            log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
            obj = h.alloc(0x38, bytes(0x38))
            _stubs(h, log)
            diffs = h.compare(CTOR, regs={UC_X86_REG_ECX: obj})
            if diffs:
                return ['case %d: %s' % (index, d) for d in diffs]
            res = h.call(CTOR, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['case %d: replacement faulted: %s' % (index, res['fault'])]
            if _u32(h, obj) != VTABLE:
                return ['case %d: vftable %08X' % (index, _u32(h, obj))]
            if (_u32(h, obj + 0x2C) != TABLE_VTABLE or _u32(h, obj + 0x30) != 0
                    or _u32(h, obj + 0x34) != 0xFFFFFFFF):
                return ['case %d: table member %08X/%d/%d' % (index, _u32(h, obj + 0x2C), _u32(h, obj + 0x30),
                                                              _u32(h, obj + 0x34))]
            if _u32(h, log + LOG_BYTE_COUNT) != 1 or _u32(h, log + LOG_BYTE_THIS) != obj + 4:
                return ['case %d: member built %d times on %08X' % (index, _u32(h, log + LOG_BYTE_COUNT),
                                                                    _u32(h, log + LOG_BYTE_THIS))]
            if not _u32(h, log + LOG_BYTE_SAME):
                return ['case %d: the member build got two different arguments' % (index,)]
            if _u32(h, log + LOG_POOL0_COUNT) != 1 or _u32(h, log + LOG_POOL0_ARG) != 0:
                return ['case %d: temporary table from pool %d called %d times' % (index, _u32(h, log + LOG_POOL0_ARG),
                                                                                  _u32(h, log + LOG_POOL0_COUNT))]
            if _u32(h, log + LOG_ASSIGN_COUNT) != 1 or _u32(h, log + LOG_ASSIGN_THIS) != obj + 0x2C:
                return ['case %d: assigned %d times on %08X' % (index, _u32(h, log + LOG_ASSIGN_COUNT),
                                                                _u32(h, log + LOG_ASSIGN_THIS))]
            if _u32(h, log + LOG_DTOR_COUNT) != 2:
                return ['case %d: temporary table destroyed %d times' % (index, _u32(h, log + LOG_DTOR_COUNT))]
            if _u32(h, log + LOG_POOL1_COUNT) != 1 or _u32(h, log + LOG_POOL1_ARG) != POOL1:
                return ['case %d: query table from pool %08X called %d times' % (index, _u32(h, log + LOG_POOL1_ARG),
                                                                                _u32(h, log + LOG_POOL1_COUNT))]
            if _u32(h, log + LOG_QUERY_COUNT) != 1:
                return ['case %d: queried %d times' % (index, _u32(h, log + LOG_QUERY_COUNT))]
            if _u32(h, log + LOG_QUERY_NAME) != WORLD_NPC or _u32(h, log + LOG_QUERY_MEMBER) != obj + 0x2C:
                return ['case %d: queried %08X into %08X' % (index, _u32(h, log + LOG_QUERY_NAME),
                                                             _u32(h, log + LOG_QUERY_MEMBER))]
            h.heap_ptr = heap0
    finally:
        for address, code in _stubs.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + 32)
        _stubs.saved = {}
        h.heap_ptr = heap0
    return None
