"""sub_0043E2D0 (size 112, ECX thiscall, ret 4): appends a copy of the 8-byte record arg 1 to the vector (+4 begin,
+8 end, +0xC limit).  While the vector has spare capacity the inline append (0x004BA1F0, whose EAX argument and
element-limit dword are this rounded down to 256, the record passed twice) copies the record and the end advances by
8; otherwise the growing append (0x0050A740) is handed the same record and the vector is left alone."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x0043E2D0
FAST = 0x004BA1F0
SLOW = 0x0050A740

F_COUNT = 0x00
F_DST = 0x04
F_N = 0x08
F_VAL = 0x0C
F_ALLOC = 0x10
F_VAL2 = 0x14
F_TAG = 0x18
F_EAX = 0x1C
S_COUNT = 0x20
S_THIS = 0x24
S_WHERE = 0x28
S_N = 0x2C
S_VAL = 0x30
LOG_SIZE = 0x40

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def test_0043E2D0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        src = h.alloc(8, bytes(bytearray((0x40 + i * 7) & 0xff for i in range(8))))
        fast = _stub(h, b'\xFF\x05' + _dword(log + F_COUNT)                          # inc [fast calls]
                      + b'\xA3' + _dword(log + F_EAX)                                # eax (arg 0) -> log
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + F_DST)                # [esp+4] -> dst
                      + b'\x8B\x44\x24\x08\xA3' + _dword(log + F_N)                  # [esp+8] -> n
                      + b'\x8B\x44\x24\x0C\xA3' + _dword(log + F_VAL)                # [esp+C] -> val
                      + b'\x8B\x44\x24\x10\xA3' + _dword(log + F_ALLOC)              # [esp+10] -> alloc
                      + b'\x8B\x44\x24\x14\xA3' + _dword(log + F_VAL2)               # [esp+14] -> val2
                      + b'\x8B\x44\x24\x18\xA3' + _dword(log + F_TAG)                # [esp+18] -> tag
                      + b'\x8B\x54\x24\x0C'                                          # edx = val
                      + b'\x8B\x0A\x8B\x52\x04'                                      # ecx = [edx]; edx = [edx+4]
                      + b'\x8B\x44\x24\x04'                                          # eax = dst
                      + b'\x89\x08\x89\x50\x04'                                      # [eax], [eax+4] = record
                      + b'\xC3')
        slow = _stub(h, b'\xFF\x05' + _dword(log + S_COUNT)                          # inc [slow calls]
                      + b'\x89\x0D' + _dword(log + S_THIS)                           # ecx -> log
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + S_WHERE)              # [esp+4] -> where
                      + b'\x8B\x44\x24\x08\xA3' + _dword(log + S_N)                  # [esp+8] -> n
                      + b'\x8B\x44\x24\x0C\xA3' + _dword(log + S_VAL)                # [esp+C] -> val
                      + b'\xC2\x0C\x00')                                             # ret C
        _patch(h, FAST, b'\xE9' + struct.pack('<i', fast - (FAST + 5)))
        _patch(h, SLOW, b'\xE9' + struct.pack('<i', slow - (SLOW + 5)))
        buf = h.alloc(0x40, bytes(bytearray((0x80 + i * 3) & 0xff for i in range(0x40))))
        this = h.alloc(0x10, bytes(0x10))
        tag = this & 0xffffff00
        cases = [('fast-one', buf, buf + 8, buf + 0x10),
                 ('fast-many', buf, buf + 0x18, buf + 0x20),
                 ('empty', 0, 0, 0),
                 ('full', buf, buf + 0x10, buf + 0x10)]

        def setup(start, end, limit):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(buf, bytes(bytearray((0x80 + i * 3) & 0xff for i in range(0x40))))
            h.uc.mem_write(this, _dword(0) + _dword(start) + _dword(end) + _dword(limit))

        for name, start, end, limit in cases:
            growing = not start or end - start >= limit - start
            setup(start, end, limit)
            diffs = h.compare(VF, args=[src], regs={UC_X86_REG_ECX: this})
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup(start, end, limit)
            res = h.call(VF, args=[src], regs={UC_X86_REG_ECX: this})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            want_f, want_s = (0, 1) if growing else (1, 0)
            if _u32(h, log + F_COUNT) != want_f or _u32(h, log + S_COUNT) != want_s:
                return ['%s: inline/growing appends called %d/%d times' % (name, _u32(h, log + F_COUNT),
                                                                         _u32(h, log + S_COUNT))]
            if growing:
                if _u32(h, log + S_THIS) != this or _u32(h, log + S_WHERE) != end or \
                        _u32(h, log + S_N) != 1 or _u32(h, log + S_VAL) != src:
                    return ['%s: growing append got this %08X where %08X n %d val %08X'
                            % (name, _u32(h, log + S_THIS), _u32(h, log + S_WHERE), _u32(h, log + S_N),
                               _u32(h, log + S_VAL))]
                if _u32(h, this + 8) != end:
                    return ['%s: the end moved to %08X without the growing append' % (name, _u32(h, this + 8))]
                continue
            if _u32(h, log + F_DST) != end or _u32(h, log + F_N) != 1:
                return ['%s: inline append got dst %08X n %d' % (name, _u32(h, log + F_DST), _u32(h, log + F_N))]
            for off, want in ((F_VAL, src), (F_ALLOC, this), (F_VAL2, src), (F_TAG, tag), (F_EAX, tag)):
                if _u32(h, log + off) != want:
                    return ['%s: inline arg at log+%02X is %08X, want %08X' % (name, off, _u32(h, log + off), want)]
            if _u32(h, this + 8) != end + 8:
                return ['%s: the end is %08X, want %08X' % (name, _u32(h, this + 8), end + 8)]
            if bytes(h.uc.mem_read(end, 8)) != bytes(h.uc.mem_read(src, 8)):
                return ['%s: the record was not copied to the end' % name]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
