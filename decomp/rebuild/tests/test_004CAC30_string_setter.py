"""String setter (0x004CAC30): the by-value std::string argument is assigned into the string at +0x1E8 and the
argument is destroyed afterwards.  The string imports run through the harness's std::string handlers."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004CAC30
FIELD = 0x1E8


def _dword(addr):
    return struct.pack('<I', addr)


def _sso(text):
    buf = text + b'\0' * (16 - len(text))
    return [0] + list(struct.unpack('<4I', buf)) + [len(text), 15, 0]


def _read_string(h, p):
    size = struct.unpack('<I', h.uc.mem_read(p + 20, 4))[0]
    res = struct.unpack('<I', h.uc.mem_read(p + 24, 4))[0]
    data = struct.unpack('<I', h.uc.mem_read(p + 4, 4))[0] if res >= 16 else p + 4
    return bytes(h.uc.mem_read(data, size))


def test_string_setter(h):
    heap0 = h.heap_ptr
    try:
        for text in (b'', b'Hello'):
            o = h.alloc(0x200, bytes(0x200))
            h.uc.mem_write(o + FIELD, _dword(0))                              # allocator
            h.uc.mem_write(o + FIELD + 4, bytes(16))                          # SSO buffer
            h.uc.mem_write(o + FIELD + 20, _dword(0))                         # size 0
            h.uc.mem_write(o + FIELD + 24, _dword(15))                        # capacity 15
            args = _sso(text)
            diffs = h.compare(FN, args=args, regs={UC_X86_REG_ECX: o}, ret=None)
            if diffs:
                return ['%r: %s' % (text, d) for d in diffs]
            res = h.call(FN, args=args, regs={UC_X86_REG_ECX: o})
            if res['fault']:
                return ['%r: replacement faulted: %s' % (text, res['fault'])]
            if _read_string(h, o + FIELD) != text:
                return ['%r: string is now %r' % (text, _read_string(h, o + FIELD))]
    finally:
        h.heap_ptr = heap0
    return None
