"""CDatFile::LoadSource (0x00445AB0): a file read earlier is reused by name; the read path itself needs the
ifstream imports, which the verifier does not emulate, so only the cache hits are compared."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

OBJ_SIZE = 0xBFC
TOKEN_TEXT = 0x8
SOURCES = 0x24
SOURCE_STRIDE = 0x3C
SOURCE_COUNT = 0x27C
CURRENT_SOURCE = 0x280
SOURCE_POS = 0x294


def _set_string(h, addr, data):
    if len(data) < 16:
        h.uc.mem_write(addr + 4, data + b'\0' * (16 - len(data)))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(data), 15))
    else:
        p = h.alloc(len(data) + 1, data + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', p))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(data), len(data)))


def _get_string(h, addr):
    size, cap = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    data = (addr + 4) if cap < 16 else struct.unpack('<I', h.uc.mem_read(addr + 4, 4))[0]
    return bytes(h.uc.mem_read(data, size))


def _datfile(h):
    obj = h.alloc(OBJ_SIZE, bytes(OBJ_SIZE))
    h.call(0x00444D50, regs={UC_X86_REG_ECX: obj})
    return obj


def _case(h, names, current_source, file):
    obj = _datfile(h)
    for i, name in enumerate(names):
        _set_string(h, obj + SOURCES + i * SOURCE_STRIDE, name)
        _set_string(h, obj + SOURCES + i * SOURCE_STRIDE + 0x1C, b'text of ' + name)
    h.uc.mem_write(obj + SOURCE_COUNT, struct.pack('<I', len(names)))
    h.uc.mem_write(obj + CURRENT_SOURCE, struct.pack('<I', 5))
    h.uc.mem_write(obj + SOURCE_POS, struct.pack('<I', 7))
    _set_string(h, obj + TOKEN_TEXT, b'junk')
    arg = h.alloc(28, bytes(28))
    _set_string(h, arg, file)
    diffs = h.compare(0x00445AB0, args=[arg], regs={UC_X86_REG_ECX: obj}, ret='al')
    if diffs:
        return diffs
    res = h.call(0x00445AB0, args=[arg], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if not (res['eax'] & 0xFF):
        return ['%r was not found among %r' % (file, names)]
    got = struct.unpack('<I', h.uc.mem_read(obj + CURRENT_SOURCE, 4))[0]
    if got != current_source:
        return ['%r: current source %d, want %d' % (file, got, current_source)]
    pos = struct.unpack('<I', h.uc.mem_read(obj + SOURCE_POS, 4))[0]
    if pos:
        return ['%r: the position is %d, not reset' % (file, pos)]
    if _get_string(h, obj + TOKEN_TEXT):
        return ['%r: the token text %r is not cleared' % (file, _get_string(h, obj + TOKEN_TEXT))]
    count = struct.unpack('<I', h.uc.mem_read(obj + SOURCE_COUNT, 4))[0]
    if count != len(names):
        return ['%r: the source count changed to %d' % (file, count)]
    return None


def test_load_source_cached(h):
    for names, current, file in (( [b'cfg.dat'], 0, b'cfg.dat' ),
                                 ( [b'a.dat', b'b.dat'], 1, b'b.dat' ),
                                 ( [b''], 0, b'' )):
        diffs = _case(h, names, current, file)
        if diffs:
            return diffs
    return None
