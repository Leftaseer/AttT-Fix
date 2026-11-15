"""CClock vf2_3C (0x0043AE60): a script table is created (0x435E00), every entry of the clock's vector
[0x30..0x34) is asked through slot 8 to add itself to that table, the table is stored under "Time"
(0x609E8C) in the argument object (0x57BF50) and the temporary is destroyed (0x4220A0).  Every callee is a
recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x0043AE60
TABLE_CTOR = 0x00435E00
TABLE_SET = 0x0057BF50
TABLE_DTOR = 0x004220A0
TIME_KEY = 0x00609E8C

LOG_CTOR_ARG = 0x00
LOG_VF = 0x04
LOG_VF_ENTRY = 0x08
LOG_SET = 0x0C
LOG_SET_THIS = 0x10
LOG_SET_NAME = 0x14
LOG_SET_COUNT = 0x18
LOG_DTOR = 0x1C
LOG_DTOR_COUNT = 0x20
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
    _patch(h, TABLE_CTOR,
           b'\xC7\x01\x00\x00\x00\x00'                                   # mov dword [ecx], 0
           + b'\xC7\x41\x04\x00\x00\x00\x00'                             # mov dword [ecx+4], 0
           + b'\xC7\x41\x08\x00\x00\x00\x00'                             # mov dword [ecx+8], 0
           + b'\x8B\x44\x24\x04'                                         # mov eax, [esp+4]
           + b'\xA3' + _dword(log + LOG_CTOR_ARG)                        # mov [log], eax
           + b'\xC2\x04\x00')                                            # ret 4
    _patch(h, TABLE_SET,
           b'\x89\x0D' + _dword(log + LOG_SET_THIS)                      # mov [log+10], ecx
           + b'\x8B\x44\x24\x04'                                         # mov eax, [esp+4]
           + b'\xA3' + _dword(log + LOG_SET_NAME)                        # mov [log+14], eax
           + b'\x8B\x44\x24\x08'                                         # mov eax, [esp+8]
           + b'\x8B\x08'                                                 # mov ecx, [eax]
           + b'\x89\x0D' + _dword(log + LOG_SET_COUNT)                   # mov [log+18], ecx
           + b'\xFF\x05' + _dword(log + LOG_SET)                         # inc [log+C]
           + b'\xC2\x08\x00')                                            # ret 8
    _patch(h, TABLE_DTOR,
           b'\x8B\x01'                                                   # mov eax, [ecx]
           + b'\xA3' + _dword(log + LOG_DTOR_COUNT)                      # mov [log+20], eax
           + b'\xFF\x05' + _dword(log + LOG_DTOR)                        # inc [log+1C]
           + b'\xC3')                                                    # ret


def test_clock_vf2_3c(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _install_stubs(h, log)
        code = (b'\x89\x0D' + _dword(log + LOG_VF_ENTRY)                      # mov [log+8], ecx
                + b'\x8B\x44\x24\x04'                                          # mov eax, [esp+4]
                + b'\xFF\x00'                                                  # inc dword [eax]
                + b'\xFF\x05' + _dword(log + LOG_VF)                           # inc [log+4]
                + b'\xC2\x04\x00')                                             # ret 4
        entry_stub = h.alloc(len(code), code)
        h.uc.ctl_remove_cache(entry_stub, entry_stub + len(code))
        table = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(table + 8, _dword(entry_stub))
        entries = h.alloc(0x40, bytes(0x40))
        elems = []
        for i in range(3):
            e = h.alloc(0x40, bytes(0x40))
            h.uc.mem_write(e, _dword(table))
            h.uc.mem_write(entries + 4 * i, _dword(e))
            elems.append(e)
        obj = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(obj + 0x30, _dword(entries))
        h.uc.mem_write(obj + 0x34, _dword(entries + 12))
        arg = h.alloc(0x40, bytes(0x40))
        diffs = h.compare(VF, args=[arg], regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(VF, args=[arg], regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        want = {'ctor_arg': 0, 'vf': 3, 'vf_entry': elems[2], 'set': 1, 'set_this': arg,
                'set_name': TIME_KEY, 'set_count': 3, 'dtor': 1, 'dtor_count': 3}
        got = {name: _u32(h, log + off) for name, off in (
            ('ctor_arg', LOG_CTOR_ARG), ('vf', LOG_VF), ('vf_entry', LOG_VF_ENTRY),
            ('set', LOG_SET), ('set_this', LOG_SET_THIS), ('set_name', LOG_SET_NAME),
            ('set_count', LOG_SET_COUNT), ('dtor', LOG_DTOR), ('dtor_count', LOG_DTOR_COUNT))}
        for k, v in want.items():
            if got[k] != v:
                return ['%s is %08X, want %08X' % (k, got[k], v)]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
