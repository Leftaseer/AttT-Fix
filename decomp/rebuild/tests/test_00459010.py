"""CGameFile::Close (0x00459010): the data buffer is released, the file object is destroyed through its vtable
slot 0 with flags 1, and the fields are cleared.  The file object is a stub whose deleting dtor only pops its
flag."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX


def _stub(h, body):
    return h.alloc(len(body), body)


def _make_file(h, size):
    slot = _stub(h, b'\xc2\x04\x00')          # slot 0: ret 4 (the deleting dtor flag)
    vtable = h.alloc(4, struct.pack('<I', slot))
    return h.alloc(0xC, struct.pack('<III', vtable, 0, size))


def _case(h, data, file_, opened):
    obj = h.alloc(0x30, bytes(0x30))
    if data:
        h.uc.mem_write(obj + 0x28, struct.pack('<I', data))
    if file_:
        h.uc.mem_write(obj + 0x24, struct.pack('<I', file_))
    h.uc.mem_write(obj + 0x2C, bytes([opened]))
    diffs = h.compare(0x00459010, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return diffs
    res = h.call(0x00459010, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    for off in (0x24, 0x28):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['+0x%X is not cleared' % off]
    if h.uc.mem_read(obj + 0x2C, 1) != b'\0':
        return ['the opened flag is not cleared']
    return []


def test_cgamefile_close(h):
    buf = h.alloc(16, b'x' * 16)
    for data, file_, opened in ((0, 0, 0), (buf, 0, 1), (0, _make_file(h, 5), 1),
                                (buf, _make_file(h, 5), 1)):
        diffs = _case(h, data, file_, opened)
        if diffs:
            return diffs
    return []
