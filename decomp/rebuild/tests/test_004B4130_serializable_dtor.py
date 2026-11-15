"""Serializable::~Serializable (0x004B4130): takes the Serializable vftable, unregisters the object from the global
serializator and destroys the _Object base.  Both calls are replaced by recording stubs; the serializator global
(0x006CA34C) is pointed at a heap object so the forwarding can be checked."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

DTOR = 0x004B4130
REMOVE = 0x004B5700
BASE = 0x00422000

SERIALIZATOR = 0x006CA34C
VTABLE = 0x00610D00

LOG_REMOVE_THIS = 0x00
LOG_REMOVE_ARG = 0x04
LOG_REMOVE_COUNT = 0x08
LOG_BASE_THIS = 0x0C
LOG_BASE_COUNT = 0x10


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _mov_eax(value):
    return b'\xB8' + struct.pack('<I', value)


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


def _patch(h, address, code, saved):
    if address not in saved:
        saved[address] = bytes(h.uc.mem_read(address, 32))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stubs(h, log):
    _patch(h, REMOVE,
           _store_ecx(log + LOG_REMOVE_THIS)
           + _mov_eax_arg(1) + _store_eax(log + LOG_REMOVE_ARG)
           + _inc(log + LOG_REMOVE_COUNT)
           + _ret4(), _stubs.saved)
    _patch(h, BASE,
           _store_ecx(log + LOG_BASE_THIS)
           + _inc(log + LOG_BASE_COUNT)
           + _mov_eax(0x55AA55AA)
           + b'\xC3', _stubs.saved)


_stubs.saved = {}


def test_serializable_dtor(h):
    saved = bytes(h.uc.mem_read(SERIALIZATOR, 4))
    _stubs.saved = {}
    heap0 = h.heap_ptr
    try:
        for index in range(2):
            serializator = h.alloc(0x20, bytes(0x20))
            log = h.alloc(0x20, bytes(0x20))
            obj = h.alloc(0x20, bytes(0x20))
            h.uc.mem_write(SERIALIZATOR, struct.pack('<I', serializator))
            _stubs(h, log)
            diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: obj})
            if diffs:
                return ['case %d: %s' % (index, d) for d in diffs]
            res = h.call(DTOR, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['case %d: replacement faulted: %s' % (index, res['fault'])]
            if _u32(h, obj) != VTABLE:
                return ['case %d: vftable %08X' % (index, _u32(h, obj))]
            if _u32(h, log + LOG_REMOVE_COUNT) != 1:
                return ['case %d: unregistered %d times' % (index, _u32(h, log + LOG_REMOVE_COUNT))]
            if _u32(h, log + LOG_REMOVE_THIS) != serializator or _u32(h, log + LOG_REMOVE_ARG) != obj:
                return ['case %d: unregistered through %08X with %08X' % (index, _u32(h, log + LOG_REMOVE_THIS),
                                                                          _u32(h, log + LOG_REMOVE_ARG))]
            if _u32(h, log + LOG_BASE_COUNT) != 1 or _u32(h, log + LOG_BASE_THIS) != obj:
                return ['case %d: base destroyed %d times on %08X' % (index, _u32(h, log + LOG_BASE_COUNT),
                                                                      _u32(h, log + LOG_BASE_THIS))]
            h.heap_ptr = heap0
    finally:
        h.uc.mem_write(SERIALIZATOR, saved)
        for address, code in _stubs.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + 32)
        _stubs.saved = {}
        h.heap_ptr = heap0
    return None
