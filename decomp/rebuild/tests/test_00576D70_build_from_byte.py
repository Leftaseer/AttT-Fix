"""0x00576D70: builds the object at this and returns it.  The original hands 0x576C20 the address of the top byte of
its saved ECX (an alias into its own frame) twice; that byte is the high byte of the this pointer.  The builder is
replaced by a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

BUILD = 0x00576D70
INIT = 0x00576C20

LOG_THIS = 0x00
LOG_ARG_REGION = 0x04
LOG_BYTE = 0x08
LOG_COUNT = 0x0C

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _stub(h, log):
    # the argument pointer itself differs between the two runs (their frames sit at different depths), so record
    # its region byte rather than the address
    code = (b'\x89\x0D' + struct.pack('<I', log + LOG_THIS)      # mov [this], ecx
            + b'\x8B\x44\x24\x04'                                # mov eax, [esp+4]
            + b'\x89\xC2'                                        # mov edx, eax
            + b'\xC1\xEA\x18'                                    # shr edx, 24
            + b'\x89\x15' + struct.pack('<I', log + LOG_ARG_REGION)  # mov [region], edx
            + b'\x8A\x08'                                        # mov cl, [eax]
            + b'\x88\x0D' + struct.pack('<I', log + LOG_BYTE)    # mov [byte], cl
            + b'\xFF\x05' + struct.pack('<I', log + LOG_COUNT)   # inc [count]
            + b'\x33\xC0'                                        # xor eax, eax
            + b'\xC2\x08\x00')                                   # ret 8
    saved.setdefault(INIT, bytes(h.uc.mem_read(INIT, len(code) + 4)))
    h.uc.mem_write(INIT, code)
    h.uc.ctl_remove_cache(INIT, INIT + len(code))


def test_build_from_byte(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(0x20, bytes(0x20))
        for _ in range(3):
            h.uc.mem_write(log, bytes(0x20))
            _stub(h, log)
            obj = h.alloc(0x40, bytes(0x40))
            diffs = h.compare(BUILD, regs={UC_X86_REG_ECX: obj})
            if diffs:
                return diffs
            h.uc.mem_write(log, bytes(0x20))
            res = h.call(BUILD, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['replacement faulted: %s' % res['fault']]
            if _u32(h, log + LOG_COUNT) != 1:
                return ['init called %d times' % _u32(h, log + LOG_COUNT)]
            if _u32(h, log + LOG_THIS) != obj:
                return ['init called on %08X, want %08X' % (_u32(h, log + LOG_THIS), obj)]
            want_byte = (obj >> 24) & 0xFF
            got = h.uc.mem_read(log + LOG_BYTE, 1)[0]
            if got != want_byte:
                return ['init read byte %02X for this %08X, want %02X' % (got, obj, want_byte)]
            if _u32(h, log + LOG_ARG_REGION) != 0x30:
                return ['init got argument %08X..., want the stack region 30'
                        % _u32(h, log + LOG_ARG_REGION)]
            if res['eax'] != obj:
                return ['returned %08X, want this %08X' % (res['eax'], obj)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
