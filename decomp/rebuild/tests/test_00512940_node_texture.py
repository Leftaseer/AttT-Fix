"""Node texture setup (0x00512940): the object at +0x3D0 receives the texture at +0x3C4 through 0x42DEE0 and the
value 0x42D9A0 returns (the frame count) is stored at +0x3CC and returned.  Both callees are recording stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00512940
SET_TEXTURE = 0x0042DEE0
FRAME_COUNT = 0x0042D9A0

LOG_SET = 0x00
LOG_SET_THIS = 0x04
LOG_SET_ARG = 0x08
LOG_COUNT = 0x0C
LOG_COUNT_THIS = 0x10
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


def test_node_texture(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, SET_TEXTURE,
               b'\x89\x0D' + _dword(log + LOG_SET_THIS)                    # mov [log+4], ecx
               + b'\x8B\x44\x24\x04'                                       # mov eax, [esp+4]
               + b'\xA3' + _dword(log + LOG_SET_ARG)                       # mov [log+8], eax
               + b'\xFF\x05' + _dword(log + LOG_SET)                       # inc [log]
               + b'\xC2\x04\x00')                                          # ret 4
        _patch(h, FRAME_COUNT,
               b'\x89\x0D' + _dword(log + LOG_COUNT_THIS)                  # mov [log+10], ecx
               + b'\xFF\x05' + _dword(log + LOG_COUNT)                     # inc [log+C]
               + b'\xB8\x07\x00\x00\x00'                                   # mov eax, 7
               + b'\xC3')                                                  # ret
        texture = 0x2000AAAA
        animation = h.alloc(0x40, bytes(0x40))
        obj = h.alloc(0x400, bytes(0x400))
        h.uc.mem_write(obj + 0x3C4, _dword(texture))
        h.uc.mem_write(obj + 0x3CC, _dword(0xFFFFFFFF))
        h.uc.mem_write(obj + 0x3D0, _dword(animation))
        diffs = h.compare(FN, regs={UC_X86_REG_ECX: obj})
        if diffs:
            return diffs
        h.uc.mem_write(log, bytes(LOG_SIZE))
        res = h.call(FN, regs={UC_X86_REG_ECX: obj})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        want = {'set': 1, 'set_this': animation, 'set_arg': texture, 'count': 1, 'count_this': animation}
        got = {name: _u32(h, log + off) for name, off in (
            ('set', LOG_SET), ('set_this', LOG_SET_THIS), ('set_arg', LOG_SET_ARG),
            ('count', LOG_COUNT), ('count_this', LOG_COUNT_THIS))}
        for k, v in want.items():
            if got[k] != v:
                return ['%s is %08X, want %08X' % (k, got[k], v)]
        if _u32(h, obj + 0x3CC) != 7:
            return ['stored %08X, want 7' % _u32(h, obj + 0x3CC)]
        if res['eax'] != 7:
            return ['returned %08X, want 7' % res['eax']]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
