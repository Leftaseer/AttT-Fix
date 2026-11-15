"""0x004257F0 (ECX = C3DLine, six floats on the stack, ret 0x18): the vertex write.  The mesh at +0x1C4 holds the
vertex buffer in its first field; the buffer's slot 0x2C is asked to lock 0x18 bytes (this = the buffer, the mesh,
0, 0x18, &vertices and 0 on the stack).  When it does not fail, the six arguments are stored as two 3D points and
the buffer's slot 0x30 unlocks with the mesh on the stack.  A failing lock writes nothing.  Both slot calls are
stubs that log what they see; the lock hands back the vertex buffer through the out pointer it is given."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004257F0

L_COUNT = 0x00
L_EVENTS = 0x10
L_MESH = 0x80
L_OFFSET = 0x84
L_SIZE = 0x88
L_HAS_DATA = 0x8C
L_FLAGS = 0x90
L_HR = 0x94
LOG_SIZE = 0xA0

EV_LOCK = 1
EV_UNLOCK = 2

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
            + b'\xC7\x82' + _dword(0) + _dword(code))                    # mov dword [edx], code


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def test_004257F0(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        vertices = h.alloc(0x40, b'\xCC' * 0x40)
        lock = _stub(h,
                     _event_head(log, EV_LOCK)
                     + b'\x89\x8A' + _dword(4)                            # this (the buffer) -> value
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_MESH)     # mesh -> [log]
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_OFFSET)   # offset -> [log]
                     + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_SIZE)     # size -> [log]
                     + b'\x8B\x44\x24\x14\xA3' + _dword(log + L_FLAGS)    # flags -> [log]
                     + b'\x8B\x54\x24\x10'                                # edx = the out pointer
                     + b'\x31\xC0\x85\xD2\x0F\x95\xC0\xA3' + _dword(log + L_HAS_DATA)  # [log] = out != 0
                     + b'\x85\xD2'                                        # test edx, edx
                     + b'\x74\x07'                                        # jz past the store
                     + b'\xB8' + _dword(vertices)                         # eax = the vertex buffer
                     + b'\x89\x02'                                        # *out = eax
                     + b'\xA1' + _dword(log + L_HR)                       # eax = hr
                     + b'\xC2\x14\x00')                                   # ret 20
        unlock = _stub(h,
                       _event_head(log, EV_UNLOCK)
                       + b'\x8B\x44\x24\x04\x89\x82' + _dword(4)          # mesh -> value
                       + b'\x31\xC0'                                      # xor eax, eax
                       + b'\xC2\x04\x00')                                 # ret 4
        buffer = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(buffer + 0x2C, _dword(lock))
        h.uc.mem_write(buffer + 0x30, _dword(unlock))
        mesh = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(mesh, _dword(buffer))
        obj = h.alloc(0x200, bytes(0x200))
        h.uc.mem_write(obj + 0x1c4, _dword(mesh))

        values = (1.5, -2.25, 3.0, 4.5, -5.75, 6.25)
        bits = [struct.unpack('<I', struct.pack('<f', v))[0] for v in values]

        for hr in (0, -1):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + L_HR, _dword(hr & 0xFFFFFFFF))
                h.uc.mem_write(vertices, b'\xCC' * 0x40)

            setup()
            diffs = h.compare(THIS, args=bits, regs={UC_X86_REG_ECX: obj}, ret=None)
            if diffs:
                return ['hr %d: %s' % (hr, d) for d in diffs]
            setup()
            res = h.call(THIS, args=bits, regs={UC_X86_REG_ECX: obj})
            if res['fault']:
                return ['hr %d: replacement faulted: %s' % (hr, res['fault'])]
            expected = [(EV_LOCK, buffer)]
            if hr >= 0:
                expected.append((EV_UNLOCK, mesh))
            got = _events(h, log)
            if got != expected:
                return ['hr %d: events %r, expected %r' % (hr, got, expected)]
            if (_u32(h, log + L_MESH) != mesh or _u32(h, log + L_OFFSET) != 0
                    or _u32(h, log + L_SIZE) != 0x18 or _u32(h, log + L_FLAGS) != 0
                    or _u32(h, log + L_HAS_DATA) != 1):
                return ['hr %d: the lock saw %08X %08X %08X %08X %08X'
                        % (hr, _u32(h, log + L_MESH), _u32(h, log + L_OFFSET),
                           _u32(h, log + L_SIZE), _u32(h, log + L_FLAGS),
                           _u32(h, log + L_HAS_DATA))]
            if hr >= 0:
                got_vertices = struct.unpack('<6f', h.uc.mem_read(vertices, 24))
                if got_vertices != values:
                    return ['hr %d: vertices %r' % (hr, got_vertices)]
            elif h.uc.mem_read(vertices, 4) != b'\xCC' * 4:
                return ['hr %d: the vertices were written' % hr]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
