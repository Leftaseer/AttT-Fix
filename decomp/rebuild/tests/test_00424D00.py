"""CUpdateObject::CUpdateObject (0x00424D00): the name copy, the fixed-update interval (33.33 ms from 0x607D54),
the zeroed state and the parent's third slot called with the new child.  The vtable is 0x607D5C."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x00424D00
VTABLE = 0x00607D5C
INTERVAL_BITS = 0x42055555


def _put_string(h, addr, text=b''):
    h.uc.mem_write(addr, bytes(4))
    if len(text) < 16:
        h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))
    else:
        buffer = h.alloc(len(text) + 1, text + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', buffer))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(text), len(text)))


def _get_string(h, addr):
    size, capacity = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    pointer = addr + 4 if capacity < 16 else struct.unpack('<I', h.uc.mem_read(addr + 4, 4))[0]
    return bytes(h.uc.mem_read(pointer, size))


def _fields(h, obj):
    vftable, link = struct.unpack('<II', h.uc.mem_read(obj, 8))
    interval, accumulator, parent, following = struct.unpack('<IIII', h.uc.mem_read(obj + 0x24, 16))
    attached = h.uc.mem_read(obj + 0x34, 1)[0]
    return vftable, link, _get_string(h, obj + 8), interval, accumulator, parent, following, attached


def _check(h, obj, name, parent):
    vftable, link, got_name, interval, accumulator, got_parent, following, attached = _fields(h, obj)
    want = (VTABLE, 0, name, INTERVAL_BITS, 0, parent, 0, 0)
    if (vftable, link, got_name, interval, accumulator, got_parent, following, attached) != want:
        return ['fields %r, want %r' % ((vftable, link, got_name, interval, accumulator, got_parent,
                                         following, attached), want)]
    return None


def test_update_object_ctor(h):
    obj = h.alloc(0x38, b'\xA5' * 0x38)
    name = h.alloc(28, bytes(28))
    _put_string(h, name, b'console')
    diffs = h.compare(CTOR, args=[name, 0], regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return ['root: %s' % d for d in diffs]
    res = h.call(CTOR, args=[name, 0], regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['root: replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['root: returned %08X, not the object' % res['eax']]
    bad = _check(h, obj, b'console', 0)
    if bad:
        return ['root: %s' % d for d in bad]
    if h.uc.mem_read(obj + 0x35, 3) != b'\xA5\xA5\xA5':
        return ['root: the tail padding was written']

    scratch = h.alloc(8, bytes(8))
    code = (b'\x8b\x44\x24\x04'                  # mov eax, [esp+4]  (the child)
            b'\xa3' + struct.pack('<I', scratch) +
            b'\x89\x0d' + struct.pack('<I', scratch + 4) +   # mov [scratch+4], ecx  (the parent)
            b'\xc2\x04\x00')                     # ret 4
    stub = h.alloc(len(code), code)
    table = h.alloc(12, bytes(12))
    h.uc.mem_write(table + 8, struct.pack('<I', stub))
    parent = h.alloc(0x38, bytes(0x38))
    h.uc.mem_write(parent, struct.pack('<I', table))
    child = h.alloc(0x38, b'\xA5' * 0x38)
    name2 = h.alloc(28, bytes(28))
    _put_string(h, name2, b'effect')

    diffs = h.compare(CTOR, args=[name2, parent], regs={UC_X86_REG_ECX: child}, ret='eax')
    if diffs:
        return ['parent: %s' % d for d in diffs]
    res = h.call(CTOR, args=[name2, parent], regs={UC_X86_REG_ECX: child})
    if res['fault']:
        return ['parent: replacement faulted: %s' % res['fault']]
    if res['eax'] != child:
        return ['parent: returned %08X, not the object' % res['eax']]
    bad = _check(h, child, b'effect', parent)
    if bad:
        return ['parent: %s' % d for d in bad]
    if struct.unpack('<II', h.uc.mem_read(scratch, 8)) != (child, parent):
        return ['parent: slot 2 got %r, want (%08X, %08X)' % (struct.unpack('<II', h.uc.mem_read(scratch, 8)),
                                                              child, parent)]
    return None
