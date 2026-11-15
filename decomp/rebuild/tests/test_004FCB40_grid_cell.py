"""sub_004FCB40 (size 112, ECX thiscall, ret 8): the flat cell index of the point (x at pos[0], y at pos[1]) of the
board: the cell this points at (+0), y rows of 0x006CA8C4 cells back, plus x.  While the 16-byte board entry
(0x006CA8C8) of the base cell has its +8 byte clear, an odd x lies one row further back (y counts one more).
Only *out is written."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x004FCB40
WIDTH = 0x006CA8C4
BOARD = 0x006CA8C8

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def test_004FCB40_grid_cell(h):
    heap0 = h.heap_ptr
    try:
        board = h.alloc(0x100, bytes(0x100))
        this = h.alloc(4, _dword(41))
        out = h.alloc(0x10, b'\x5A' * 0x10)
        pos = h.alloc(8, bytes(8))
        saved[WIDTH] = bytes(h.uc.mem_read(WIDTH, 4))
        saved[BOARD] = bytes(h.uc.mem_read(BOARD, 4))
        h.uc.mem_write(WIDTH, _dword(48))
        h.uc.mem_write(BOARD, _dword(board))

        def setup(flagged, x, y):
            h.uc.mem_write(board, bytes(0x100))
            h.uc.mem_write(board + 41 * 16 + 8, bytes([1 if flagged else 0]))
            h.uc.mem_write(pos, _dword(x & 0xffffffff) + _dword(y & 0xffffffff))
            h.uc.mem_write(out, b'\x5A' * 0x10)

        cases = [('flagged-even', 1, 6, 3), ('flagged-odd', 1, 7, 3), ('flagged-neg', 1, -4, -3),
                 ('staggered-even', 0, 6, 3), ('staggered-odd', 0, 7, 3), ('staggered-neg', 0, -3, -5)]
        for name, flagged, x, y in cases:
            setup(flagged, x, y)
            diffs = h.compare(VF, args=[out, pos], regs={UC_X86_REG_ECX: this}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(flagged, x, y)
            res = h.call(VF, args=[out, pos], regs={UC_X86_REG_ECX: this})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            ry = y + (1 if (not flagged and x & 1) else 0)
            want = (41 + x - ry * 48) & 0xffffffff
            if _u32(h, out) != want:
                return ['%s: the cell is %08X, want %08X' % (name, _u32(h, out), want)]
            if bytes(h.uc.mem_read(out + 4, 0x0C)) != b'\x5A' * 0x0C:
                return ['%s: the out byte range was written past four bytes' % name]
            if bytes(h.uc.mem_read(pos, 8)) != _dword(x & 0xffffffff) + _dword(y & 0xffffffff):
                return ['%s: the point was changed' % name]
    finally:
        for address, value in saved.items():
            h.uc.mem_write(address, value)
            h.uc.ctl_remove_cache(address, address + len(value))
        saved.clear()
        h.heap_ptr = heap0
    return None
