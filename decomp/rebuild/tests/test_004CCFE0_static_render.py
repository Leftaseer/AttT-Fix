"""StaticObjectManager::Render (0x004CCFE0): renders through 0x4CCEE0, called on the manager at +0x38 with the this
pointer's low byte cleared, and returns its result.  The renderer is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

RENDER = 0x004CCFE0
RENDERER = 0x004CCEE0

LOG_THIS = 0x00
LOG_ARG = 0x04
LOG_COUNT = 0x08

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _stub(h, log):
    code = (b'\x89\x0D' + struct.pack('<I', log + LOG_THIS)         # mov [this], ecx
            + b'\x8B\x44\x24\x04'                                   # mov eax, [esp+4]
            + b'\xA3' + struct.pack('<I', log + LOG_ARG)            # mov [arg], eax
            + b'\xFF\x05' + struct.pack('<I', log + LOG_COUNT)      # inc [count]
            + b'\xB8\x34\x12\x00\x00'                               # mov eax, 0x1234
            + b'\xC2\x04\x00')                                      # ret 4
    saved.setdefault(RENDERER, bytes(h.uc.mem_read(RENDERER, len(code))))
    h.uc.mem_write(RENDERER, code)
    h.uc.ctl_remove_cache(RENDERER, RENDERER + len(code))


def test_static_object_manager_render(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x10, bytes(0x10))
        _stub(h, log)
        obj = h.alloc(0x100, bytes(0x100))
        diffs = h.compare(RENDER, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(0x10))
        res = h.call(RENDER, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_COUNT) != 1:
            return ['renderer called %d times' % _u32(h, log + LOG_COUNT)]
        if _u32(h, log + LOG_THIS) != obj + 0x38:
            return ['renderer called on %08X, want %08X' % (_u32(h, log + LOG_THIS), obj + 0x38)]
        if _u32(h, log + LOG_ARG) != (obj & 0xFFFFFF00):
            return ['renderer got argument %08X, want %08X' % (_u32(h, log + LOG_ARG), obj & 0xFFFFFF00)]
        if res['eax'] != 0x1234:
            return ['returned %08X, want the renderer result 1234' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
