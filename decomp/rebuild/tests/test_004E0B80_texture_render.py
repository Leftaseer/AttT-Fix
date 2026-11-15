"""CTextureNode::Render (0x004E0B80): renders through 0x4E0A80 while the flag at +0x65 is set, through 0x4E0750 while
the node at +0x7C is null, and otherwise does nothing (returning the value already in EAX).  The two render paths are
replaced by recording stubs with distinct results."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EAX

RENDER = 0x004E0B80
RENDER_A = 0x004E0A80
RENDER_B = 0x004E0750

LOG_A_THIS = 0x00
LOG_A_COUNT = 0x04
LOG_B_THIS = 0x08
LOG_B_COUNT = 0x0C

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _stub(h, address, this_slot, count_slot, result):
    code = (b'\x89\x0D' + struct.pack('<I', this_slot)           # mov [this], ecx
            + b'\xFF\x05' + struct.pack('<I', count_slot)        # inc [count]
            + b'\xB8' + struct.pack('<I', result)                # mov eax, result
            + b'\xC3')                                           # ret
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def test_texture_node_render(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(16, bytes(16))
        for flag, node, want_a, want_b in ((1, None, 1, 0), (1, 0x1000, 1, 0),
                                           (0, None, 0, 1), (0, 0x1000, 0, 0)):
            h.uc.mem_write(log, bytes(16))
            _stub(h, RENDER_A, log + LOG_A_THIS, log + LOG_A_COUNT, 0xAAAA0001)
            _stub(h, RENDER_B, log + LOG_B_THIS, log + LOG_B_COUNT, 0xBBBB0002)
            obj = h.alloc(0x100, bytes(0x100))
            h.uc.mem_write(obj + 0x65, bytes([flag]))
            h.uc.mem_write(obj + 0x7c, struct.pack('<I', node or 0))
            in_eax = 0xFEEDFACE
            diffs = h.compare(RENDER, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
            if diffs:
                return ['flag %d node %r: %s' % (flag, node, d) for d in diffs]
            h.uc.mem_write(log, bytes(16))
            res = h.call(RENDER, regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
            if res['fault']:
                return ['flag %d node %r: replacement faulted: %s' % (flag, node, res['fault'])]
            if _u32(h, log + LOG_A_COUNT) != want_a:
                return ['flag %d node %r: 4E0A80 called %d times, want %d'
                        % (flag, node, _u32(h, log + LOG_A_COUNT), want_a)]
            if _u32(h, log + LOG_B_COUNT) != want_b:
                return ['flag %d node %r: 4E0750 called %d times, want %d'
                        % (flag, node, _u32(h, log + LOG_B_COUNT), want_b)]
            if want_a and _u32(h, log + LOG_A_THIS) != obj:
                return ['flag %d node %r: 4E0A80 got %08X' % (flag, node, _u32(h, log + LOG_A_THIS))]
            if want_b and _u32(h, log + LOG_B_THIS) != obj:
                return ['flag %d node %r: 4E0750 got %08X' % (flag, node, _u32(h, log + LOG_B_THIS))]
            want_eax = 0xAAAA0001 if want_a else 0xBBBB0002 if want_b else in_eax
            if res['eax'] != want_eax:
                return ['flag %d node %r: returned %08X, want %08X'
                        % (flag, node, res['eax'], want_eax)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
