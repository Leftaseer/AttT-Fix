"""CBaseMeshObject3D vf48 (0x00430570): with +0x49 set, 0x4AC890 runs, slot 0x18 of the object at +0x3C counts
the sub-objects, slot 0x20 selects each one, the mesh at +0x1C4 is drawn with the argument, slot 0x24 finishes
it and slot 0x1C closes the pass and returns its value; with +0x49 clear the input EAX passes through and
nothing else runs.  Every callee is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX

VF = 0x00430570
RELEASE = 0x004AC890
DRAW = 0x00477610

LOG_RELEASE = 0x00
LOG_RELEASE_THIS = 0x04
LOG_BEGIN = 0x08
LOG_BEGIN_ARG2 = 0x0C
LOG_ONE = 0x10
LOG_ONE_INDEX = 0x14
LOG_DRAW = 0x18
LOG_DRAW_THIS = 0x1C
LOG_DRAW_P1 = 0x20
LOG_DRAW_P2 = 0x24
LOG_END24 = 0x28
LOG_END1C = 0x2C
LOG_SIZE = 0x40

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _dword(addr):
    return struct.pack('<I', addr)


def _install_stubs(h, log):
    _patch(h, RELEASE,
           b'\x89\x0D' + _dword(log + LOG_RELEASE_THIS)                 # mov [log+4], ecx
           + b'\xFF\x05' + _dword(log + LOG_RELEASE)                     # inc [log]
           + b'\xC3')                                                    # ret
    _patch(h, DRAW,
           b'\x89\x0D' + _dword(log + LOG_DRAW_THIS)                    # mov [log+1C], ecx
           + b'\x8B\x44\x24\x04'                                         # mov eax, [esp+4]
           + b'\xA3' + _dword(log + LOG_DRAW_P1)                         # mov [log+20], eax
           + b'\x8B\x44\x24\x08'                                         # mov eax, [esp+8]
           + b'\xA3' + _dword(log + LOG_DRAW_P2)                         # mov [log+24], eax
           + b'\xFF\x05' + _dword(log + LOG_DRAW)                        # inc [log+18]
           + b'\xC2\x08\x00')                                            # ret 8


def _slot_stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def test_mesh_vf48(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _install_stubs(h, log)
        begin = _slot_stub(h, b'\x8B\x44\x24\x04'                                     # mov eax, [esp+4]
                              + b'\xC7\x00\x02\x00\x00\x00'                             # mov dword [eax], 2
                              + b'\x8B\x44\x24\x08'                                     # mov eax, [esp+8]
                              + b'\xA3' + _dword(log + LOG_BEGIN_ARG2)                  # mov [log+C], eax
                              + b'\xFF\x05' + _dword(log + LOG_BEGIN)                   # inc [log+8]
                              + b'\xC2\x08\x00')                                        # ret 8
        one = _slot_stub(h, b'\x8B\x44\x24\x04'                                       # mov eax, [esp+4]
                            + b'\xA3' + _dword(log + LOG_ONE_INDEX)                     # mov [log+14], eax
                            + b'\xFF\x05' + _dword(log + LOG_ONE)                       # inc [log+10]
                            + b'\xC2\x04\x00')                                          # ret 4
        end24 = _slot_stub(h, b'\xFF\x05' + _dword(log + LOG_END24) + b'\xC3')        # inc [log+28]; ret
        end1c = _slot_stub(h, b'\xFF\x05' + _dword(log + LOG_END1C)                   # inc [log+2C]
                              + b'\xB8\x78\x56\x34\x12'                                 # mov eax, 12345678h
                              + b'\xC3')                                                # ret
        table = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(table + 0x18, _dword(begin))
        h.uc.mem_write(table + 0x1C, _dword(end1c))
        h.uc.mem_write(table + 0x20, _dword(one))
        h.uc.mem_write(table + 0x24, _dword(end24))
        arg = 0x3F800000
        for flag in (0, 1):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            inner = h.alloc(0x40, bytes(0x40))
            h.uc.mem_write(inner, _dword(table))
            renderer = h.alloc(0x40, bytes(0x40))
            obj = h.alloc(0x200, bytes(0x200))
            h.uc.mem_write(obj + 0x49, bytes([flag]))
            h.uc.mem_write(obj + 0x3C, _dword(inner))
            h.uc.mem_write(obj + 0x1C4, _dword(renderer))
            h.uc.mem_write(obj + 0x1D8, _dword(0x2000))
            in_eax = 0xFEEDFACE
            diffs = h.compare(VF, args=[arg], regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
            if diffs:
                return ['flag %d: %s' % (flag, d) for d in diffs]
            h.uc.mem_write(log, bytes(LOG_SIZE))
            res = h.call(VF, args=[arg], regs={UC_X86_REG_ECX: obj, UC_X86_REG_EAX: in_eax})
            if res['fault']:
                return ['flag %d: replacement faulted: %s' % (flag, res['fault'])]
            got = {name: _u32(h, log + off) for name, off in (
                ('release', LOG_RELEASE), ('begin', LOG_BEGIN), ('begin_arg2', LOG_BEGIN_ARG2),
                ('one', LOG_ONE), ('one_index', LOG_ONE_INDEX), ('draw', LOG_DRAW),
                ('draw_this', LOG_DRAW_THIS), ('draw_p1', LOG_DRAW_P1), ('draw_p2', LOG_DRAW_P2),
                ('end24', LOG_END24), ('end1c', LOG_END1C))}
            if not flag:
                if any(got[k] for k in ('release', 'begin', 'one', 'draw', 'end24', 'end1c')):
                    return ['flag 0: slot ran: %r' % (got,)]
                if res['eax'] != in_eax:
                    return ['flag 0: returned %08X, want %08X' % (res['eax'], in_eax)]
                continue
            want = {'release': 1, 'begin': 1, 'begin_arg2': 0, 'one': 2, 'one_index': 1,
                    'draw': 2, 'draw_this': renderer, 'draw_p1': 0x2000, 'draw_p2': arg,
                    'end24': 2, 'end1c': 1}
            for k, v in want.items():
                if got[k] != v:
                    return ['flag 1: %s is %08X, want %08X' % (k, got[k], v)]
            if _u32(h, log + LOG_RELEASE_THIS) != obj:
                return ['flag 1: release called on %08X' % _u32(h, log + LOG_RELEASE_THIS)]
            if res['eax'] != 0x12345678:
                return ['flag 1: returned %08X' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
