"""CMeshObject2DRes ctor with a resource name (0x0047A120): initializes the base, sets the vftable 0x60EC94,
finishes with 0x479F50, sets the resource with 0x4AB810(name, 0) and returns this.  All three callees are recording
stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x0047A120
BASE = 0x004AC0F0
FINISH = 0x00479F50
SET = 0x004AB810

VFTABLE = 0x0060EC94

LOG_BASE_THIS = 0x00
LOG_BASE_COUNT = 0x04
LOG_FIN_THIS = 0x08
LOG_FIN_VFT = 0x0C
LOG_FIN_COUNT = 0x10
LOG_SET_THIS = 0x14
LOG_SET_NAME = 0x18
LOG_SET_SHARED = 0x1C
LOG_SET_COUNT = 0x20

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def test_cmesh2dres_ctor_named(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x30, bytes(0x30))
        _patch(h, BASE, b'\x89\x0D' + struct.pack('<I', log + LOG_BASE_THIS)
               + b'\xFF\x05' + struct.pack('<I', log + LOG_BASE_COUNT) + b'\xC3')
        _patch(h, FINISH, b'\x89\x0D' + struct.pack('<I', log + LOG_FIN_THIS)
               + b'\x8B\x01' + b'\xA3' + struct.pack('<I', log + LOG_FIN_VFT)
               + b'\xFF\x05' + struct.pack('<I', log + LOG_FIN_COUNT) + b'\xC3')
        _patch(h, SET, b'\x89\x0D' + struct.pack('<I', log + LOG_SET_THIS)
               + b'\x8B\x44\x24\x04' + b'\xA3' + struct.pack('<I', log + LOG_SET_NAME)   # mov eax, [esp+4]
               + b'\x8A\x4C\x24\x08' + b'\x88\x0D' + struct.pack('<I', log + LOG_SET_SHARED)
               + b'\xFF\x05' + struct.pack('<I', log + LOG_SET_COUNT)
               + b'\x33\xC0' + b'\xC2\x08\x00')
        name = h.alloc(0x10, b'Resource.mesh\0')
        for arg in (name, 0x1000):
            h.uc.mem_write(log, bytes(0x30))
            obj = h.alloc(0x100, bytes(0x100))
            diffs = h.compare(CTOR, args=[arg], regs={UC_X86_REG_ECX: obj})
            if diffs:
                return ['name %08X: %s' % (arg, d) for d in diffs]
            h.uc.mem_write(log, bytes(0x30))
            res = h.call(CTOR, args=[arg], regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['name %08X: replacement faulted: %s' % (arg, res['fault'])]
            if _u32(h, log + LOG_BASE_COUNT) != 1 or _u32(h, log + LOG_BASE_THIS) != obj:
                return ['name %08X: base initialized %d times on %08X'
                        % (arg, _u32(h, log + LOG_BASE_COUNT), _u32(h, log + LOG_BASE_THIS))]
            if _u32(h, log + LOG_FIN_COUNT) != 1 or _u32(h, log + LOG_FIN_VFT) != VFTABLE:
                return ['name %08X: finisher called %d times, saw vftable %08X'
                        % (arg, _u32(h, log + LOG_FIN_COUNT), _u32(h, log + LOG_FIN_VFT))]
            if _u32(h, log + LOG_SET_COUNT) != 1 or _u32(h, log + LOG_SET_THIS) != obj:
                return ['name %08X: setter called %d times on %08X'
                        % (arg, _u32(h, log + LOG_SET_COUNT), _u32(h, log + LOG_SET_THIS))]
            if _u32(h, log + LOG_SET_NAME) != arg:
                return ['name %08X: setter got name %08X' % (arg, _u32(h, log + LOG_SET_NAME))]
            if h.uc.mem_read(log + LOG_SET_SHARED, 1)[0] != 0:
                return ['name %08X: setter got shared %d' % (arg, h.uc.mem_read(log + LOG_SET_SHARED, 1)[0])]
            if _u32(h, obj) != VFTABLE:
                return ['name %08X: vftable %08X' % (arg, _u32(h, obj))]
            if res['eax'] != obj:
                return ['name %08X: returned %08X, want this %08X' % (arg, res['eax'], obj)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
