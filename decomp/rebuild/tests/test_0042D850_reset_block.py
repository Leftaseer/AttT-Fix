"""sub_0042D850 (size 96, cdecl, one argument): resets the 16-float block arg 1 - its corners (floats 0, 5, 10 and
15) take the global distance 0x0068AE40, all other floats 0."""
import struct

VF = 0x0042D850
DIST = 0x0068AE40

saved = {}


def _dword(addr):
    return struct.pack('<I', addr)


def test_0042D850_reset_block(h):
    heap0 = h.heap_ptr
    try:
        block = h.alloc(0x40, b'\xAA' * 0x40)
        saved[DIST] = bytes(h.uc.mem_read(DIST, 4))
        h.uc.mem_write(DIST, _dword(0x3F900000))
        h.uc.mem_write(block, b'\xAA' * 0x40)
        diffs = h.compare(VF, args=[block], ret=None)
        if diffs:
            return diffs
        h.uc.mem_write(block, b'\xAA' * 0x40)
        res = h.call(VF, args=[block])
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        want = []
        for i in range(16):
            want.append(0x3F900000 if i in (0, 5, 10, 15) else 0)
        got = list(struct.unpack('<16I', bytes(h.uc.mem_read(block, 0x40))))
        if got != want:
            return ['the block is %s' % ' '.join('%08X' % w for w in got)]
    finally:
        for address, value in saved.items():
            h.uc.mem_write(address, value)
            h.uc.ctl_remove_cache(address, address + len(value))
        saved.clear()
        h.heap_ptr = heap0
    return None
