"""Ring traversal (0x00569530): every node of the ring at [this+8] hands its object (node+8) to 0x533700
together with the argument, and the function always returns 0.  0x533700 is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00569530
ELEMENT = 0x00533700

LOG_COUNT = 0x00
LOG_ITEMS = 0x04
LOG_SIZE = 0x20

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _dword(addr):
    return struct.pack('<I', addr)


def test_ring_traversal(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, ELEMENT,
               b'\x8B\x05' + _dword(log + LOG_COUNT)                       # mov eax, [count]
               + b'\x89\x0C\x85' + _dword(log + LOG_ITEMS)                 # mov [eax*4+items], ecx
               + b'\xFF\x05' + _dword(log + LOG_COUNT)                     # inc [count]
               + b'\xC2\x04\x00')                                          # ret 4
        head = h.alloc(0x10, bytes(0x10))
        ring = []
        for i in range(3):
            node = h.alloc(0x10, bytes(0x10))
            h.uc.mem_write(node + 8, _dword(0x3000 + 0x100 * i))
            ring.append(node)
        h.uc.mem_write(head, _dword(ring[0]))
        nodes = ring + [head]
        for i, node in enumerate(ring):
            h.uc.mem_write(node, _dword(nodes[i + 1]))
        obj = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(obj + 8, _dword(head))
        arg = 0xCAFEBABE
        diffs = h.compare(FN, args=[arg], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(FN, args=[arg], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if _u32(h, log + LOG_COUNT) != 3:
            return ['called %d times, want 3' % _u32(h, log + LOG_COUNT)]
        for i in range(3):
            if _u32(h, log + LOG_ITEMS + 4 * i) != 0x3000 + 0x100 * i:
                return ['item %d is %08X' % (i, _u32(h, log + LOG_ITEMS + 4 * i))]
        if res['eax'] != 0:
            return ['returned %08X, want 0' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
