"""0x004CA820 (ECX = the rectangle writer, four floats on the stack, ret 0x10): locks the vertex buffer at +4
through its slot 0x2C (offset 0, size 0, into a pointer that starts as 0, flags 0; the result is ignored), writes
six 0x1C-byte vertices at (x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y) and (x + w, y + h) -- the two
triangles of the rectangle -- with 0.01 and 1 in their third and fourth floats and the rest of each record left
alone, then unlocks through slot 0x30.  Both slot calls are stubs that log what they see; the lock hands back the
vertex buffer through the out pointer it is given."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004CA820

L_COUNT = 0x00
L_EVENTS = 0x10
L_BUF = 0x80
L_OFFSET = 0x84
L_SIZE = 0x88
L_HAS_DATA = 0x8C
L_FLAGS = 0x90
L_HR = 0x94
LOG_SIZE = 0xA0

EV_LOCK = 1
EV_UNLOCK = 2

F_001 = 0x3C23D70A                                                   # 0.01
F_ONE = 0x3F800000                                                   # 1.0

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


def _event_head(log, code):
    return (b'\xFF\x05' + _dword(log + L_COUNT)                          # inc [count]
            + b'\xA1' + _dword(log + L_COUNT)                            # mov eax, [count]
            + b'\x48'                                                    # dec eax (event index)
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)                   # lea edx, [eax*8 + events]
            + b'\xC7\x82' + _dword(0) + _dword(code)                     # mov dword [edx], code
            + b'\x8B\x44\x24\x04'                                        # mov eax, [esp+4] (this)
            + b'\x89\x42\x04')                                           # mov [edx+4], eax


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def _f32u(v):
    return struct.unpack('<I', struct.pack('<f', v))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


def test_004CA820(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        data = h.alloc(0xB0, b'\xCC' * 0xB0)
        lock = _stub(h,
                     _event_head(log, EV_LOCK)
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_OFFSET)   # offset -> [log]
                     + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_SIZE)     # size -> [log]
                     + b'\x8B\x44\x24\x14\xA3' + _dword(log + L_FLAGS)    # flags -> [log]
                     + b'\x8B\x54\x24\x10'                                # edx = the out pointer
                     + b'\x31\xC0\x85\xD2\x0F\x95\xC0\xA3' + _dword(log + L_HAS_DATA)  # [log] = out != 0
                     + b'\x85\xD2'                                        # test edx, edx
                     + b'\x74\x07'                                        # jz past the store
                     + b'\xB8' + _dword(data)                             # eax = the vertex buffer
                     + b'\x89\x02'                                        # *out = eax
                     + b'\xA1' + _dword(log + L_HR)                       # eax = hr
                     + b'\xC2\x14\x00')                                   # ret 20
        unlock = _stub(h,
                       _event_head(log, EV_UNLOCK)
                       + b'\x31\xC0'                                      # xor eax, eax
                       + b'\xC2\x04\x00')                                 # ret 4
        vtable = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(vtable + 0x2C, _dword(lock))
        h.uc.mem_write(vtable + 0x30, _dword(unlock))
        buf = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(buf, _dword(vtable))
        obj = h.alloc(0x20, bytes(0x20))
        h.uc.mem_write(obj + 4, _dword(buf))

        cases = ((1.5, -2.25, 3.0, 4.5), (-1.5, 0.25, 8.0, 0.5))
        for x, y, w, hgt in cases:
            bits = [_f32u(v) for v in (x, y, w, hgt)]
            right = struct.unpack('<f', struct.pack('<f', x + w))[0]
            bottom = struct.unpack('<f', struct.pack('<f', y + hgt))[0]

            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + L_HR, _dword(0x80004005))
                h.uc.mem_write(data, b'\xCC' * 0xB0)

            setup()
            diffs = h.compare(THIS, args=bits, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['(%r, %r, %r, %r): %s' % (x, y, w, hgt, d) for d in diffs]
            setup()
            res = h.call(THIS, args=bits, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['(%r, %r, %r, %r): replacement faulted: %s' % (x, y, w, hgt, res['fault'])]
            if res['esp'] != 20:
                return ['(%r, %r, %r, %r): stack delta %d, not 20' % (x, y, w, hgt, res['esp'])]
            got = _events(h, log)
            expected = [(EV_LOCK, buf), (EV_UNLOCK, buf)]
            if got != expected:
                return ['(%r, %r, %r, %r): events %r, expected %r' % (x, y, w, hgt, got, expected)]
            if (_u32(h, log + L_OFFSET) != 0 or _u32(h, log + L_SIZE) != 0
                    or _u32(h, log + L_FLAGS) != 0 or _u32(h, log + L_HAS_DATA) != 1):
                return ['(%r, %r, %r, %r): the lock saw %08X %08X %08X %08X'
                        % (x, y, w, hgt, _u32(h, log + L_OFFSET), _u32(h, log + L_SIZE),
                           _u32(h, log + L_FLAGS), _u32(h, log + L_HAS_DATA))]
            want = ((x, y), (right, y), (right, bottom), (x, bottom), (x, y), (right, bottom))
            for i, (ex, ey) in enumerate(want):
                base = data + i * 0x1C
                gotx, goty, gotz, gotw = struct.unpack('<4I', h.uc.mem_read(base, 16))
                if (gotx, goty) != (_f32u(ex), _f32u(ey)) or gotz != F_001 or gotw != F_ONE:
                    return ['(%r, %r, %r, %r): vertex %d %08X %08X %08X %08X'
                            % (x, y, w, hgt, i, gotx, goty, gotz, gotw)]
                if h.uc.mem_read(base + 16, 12) != b'\xCC' * 12:
                    return ['(%r, %r, %r, %r): vertex %d padding was written' % (x, y, w, hgt, i)]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
