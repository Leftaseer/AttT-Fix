"""sub_00511B30 (size 112, ECX thiscall, ret 4): moves the creature to board slot arg 1 of the board behind this+0x3B0
(+0x68): the slot it leaves (this+0x2BC, in the global board 0x006CA8C8) is released only while it still names the
creature - owner cleared and the free byte (+9) set; the new slot gets the creature as owner with the free byte
cleared, and its point (x at +0, y at +4) goes to 0x004AC940 with the creature."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00511B30
MOVE = 0x004AC940
GLOBAL = 0x006CA8C8

L_COUNT = 0x00
L_THIS = 0x04
L_X = 0x08
L_Y = 0x0C
LOG_SIZE = 0x10

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _slot(h, board, i, x, y, kind, freed, owner):
    h.uc.mem_write(board + i * 16, struct.pack('<ffBBH', x, y, kind, freed, 0) + _dword(owner))


def _read(h, board, i, size):
    return bytes(h.uc.mem_read(board + i * 16, size))


def test_00511B30(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        code = (b'\xFF\x05' + _dword(log + L_COUNT)                        # inc [calls]
                + b'\x89\x0D' + _dword(log + L_THIS)                       # ecx (the creature)
                + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_X)              # [esp+4] -> x
                + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_Y)              # [esp+8] -> y
                + b'\xC2\x08\x00')                                         # ret 8
        stub = h.alloc(len(code), code)
        _patch(h, MOVE, b'\xE9' + struct.pack('<i', stub - (MOVE + 5)))
        board = h.alloc(0x100, bytes(0x100))
        aux = h.alloc(0x80, bytes(0x80))
        path = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(aux + 0x68, _dword(path))
        this = h.alloc(0x400, bytes(0x400))
        h.uc.mem_write(GLOBAL, _dword(board))
        X = 1.5
        Y = -2.25

        def setup(old_owner, freed, old_idx, slot):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(aux, bytes(0x80))
            h.uc.mem_write(aux + 0x68, _dword(path))
            h.uc.mem_write(path, bytes(0x100))
            h.uc.mem_write(board, bytes(0x100))
            _slot(h, board, old_idx, 7.0, 8.0, 3, freed, old_owner)
            _slot(h, path, slot, X, Y, 1, 1, 0x33333333)
            h.uc.mem_write(this, bytes(0x400))
            h.uc.mem_write(this + 0x2bc, _dword(old_idx))
            h.uc.mem_write(this + 0x3b0, _dword(aux))

        cases = [('released', this, 0, 5, 3), ('other-owner', 0x12340000, 0, 5, 3),
                 ('same-slot', this, 0, 3, 3)]
        for name, old_owner, freed, old_idx, slot in cases:
            setup(old_owner, freed, old_idx, slot)
            diffs = h.compare(VF, args=[slot], regs={UC_X86_REG_ECX: this}, ret=None)
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(old_owner, freed, old_idx, slot)
            res = h.call(VF, args=[slot], regs={UC_X86_REG_ECX: this})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            tag = name
            if _u32(h, log + L_COUNT) != 1:
                return ['%s: the point was sent %d times' % (tag, _u32(h, log + L_COUNT))]
            if _u32(h, log + L_THIS) != this:
                return ['%s: the point was sent for %08X' % (tag, _u32(h, log + L_THIS))]
            if _u32(h, log + L_X) != struct.unpack('<I', struct.pack('<f', X))[0] or \
                    _u32(h, log + L_Y) != struct.unpack('<I', struct.pack('<f', Y))[0]:
                return ['%s: the point is (%08X, %08X)' % (tag, _u32(h, log + L_X), _u32(h, log + L_Y))]
            if _u32(h, this + 0x2bc) != slot:
                return ['%s: the slot index is %d' % (tag, _u32(h, this + 0x2bc))]
            want_old_owner = 0 if old_owner == this else old_owner
            if _u32(h, board + old_idx * 16 + 0xC) != want_old_owner:
                return ['%s: the left slot owner is %08X' % (tag, _u32(h, board + old_idx * 16 + 0xC))]
            if h.uc.mem_read(board + old_idx * 16 + 9, 1) != bytes([1 if old_owner == this else freed]):
                return ['%s: the left slot free byte is %02X' % (tag, h.uc.mem_read(board + old_idx * 16 + 9, 1)[0])]
            if _u32(h, path + slot * 16 + 0xC) != this:
                return ['%s: the taken slot owner is %08X' % (tag, _u32(h, path + slot * 16 + 0xC))]
            if _read(h, path, slot, 10)[9] != 0:
                return ['%s: the taken slot is still free' % tag]
            if _read(h, path, slot, 8) != struct.pack('<ff', X, Y):
                return ['%s: the taken slot point changed' % tag]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
