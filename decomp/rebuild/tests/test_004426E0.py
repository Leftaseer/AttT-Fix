"""CConsole::CConsole (0x004426E0): the updater base at +4, the console vtables, the empty strings and the 200-entry
line history, with the tail padding left alone.  The object is 0x1658 bytes."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

CTOR = 0x004426E0
SIZE = 0x1658
CONSOLE_VTABLE = 0x0060A2C0
UPDATER_VTABLE = 0x0060A2C8
INTERVAL_BITS = 0x42055555


def _empty_string(h, addr):
    size, capacity = struct.unpack('<II', h.uc.mem_read(addr + 0x14, 8))
    if size != 0:
        return 'size %d' % size
    if capacity != 15:
        return 'capacity %d' % capacity
    if h.uc.mem_read(addr + 4, 1) != b'\0':
        return 'the buffer is not empty'
    return None


def _check(h, obj):
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != CONSOLE_VTABLE:
        return ['the CConsole vtable is not at +0']
    if struct.unpack('<I', h.uc.mem_read(obj + 4, 4))[0] != UPDATER_VTABLE:
        return ['the updater vtable is not at +4']
    link = struct.unpack('<I', h.uc.mem_read(obj + 8, 4))[0]
    interval, accumulator, parent, following = struct.unpack('<IIII', h.uc.mem_read(obj + 0x28, 16))
    want = (0, INTERVAL_BITS, 0, 0, 0)
    if (link, interval, accumulator, parent, following) != want:
        return ['updater (link, interval, accumulator, parent, next) %r, want %r'
                % ((link, interval, accumulator, parent, following), want)]
    if h.uc.mem_read(obj + 0x38, 1) != b'\0':
        return ['the updater is marked attached']
    bad = _empty_string(h, obj + 0x0C)
    if bad:
        return ['updater name: %s' % bad]
    bad = _empty_string(h, obj + 0x3C)
    if bad:
        return ['string +0x3C: %s' % bad]
    for index, offset in ((0, 0x58), (199, 0x161C)):
        bad = _empty_string(h, obj + offset)
        if bad:
            return ['line %d: %s' % (index, bad)]
    bad = _empty_string(h, obj + 0x1638)
    if bad:
        return ['game folder: %s' % bad]
    return None


def test_console_ctor(h):
    obj = h.alloc(SIZE, b'\xA5' * SIZE)
    diffs = h.compare(CTOR, regs={UC_X86_REG_ECX: obj}, ret='eax')
    if diffs:
        return diffs
    res = h.call(CTOR, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['ctor returned %08X, not this' % res['eax']]
    bad = _check(h, obj)
    if bad:
        return bad
    if h.uc.mem_read(obj + 0x1654, 4) != b'\xA5' * 4:
        return ['the tail padding was written']
    return None
