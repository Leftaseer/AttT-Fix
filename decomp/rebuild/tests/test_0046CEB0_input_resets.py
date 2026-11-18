"""CInput mouse and key reset functions (0x46CEB0 and 0x46CEF0)."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

RESET_MOUSE = 0x0046CEB0
RESET_KEYS = 0x0046CEF0


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _check_mouse(h, count):
    obj = h.alloc(0x7d0, bytes(0x7d0))
    buttons = h.alloc(max(4, count * 4), b'\xA5' * max(4, count * 4))
    h.uc.mem_write(obj + 0x66c, _dword(buttons))
    h.uc.mem_write(obj + 0x670, _dword(count))
    h.uc.mem_write(obj + 0x7c4, b'\x01\x02\x03')

    diffs = h.compare(RESET_MOUSE, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return ['mouse count %d: %s' % (count, d) for d in diffs]
    result = h.call(RESET_MOUSE, regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['mouse count %d: %s' % (count, result['fault'])]
    problems = []
    for index in range(count):
        if _u32(h, buttons + index * 4) != 6:
            problems.append('mouse count %d: button %d was not released' % (count, index))
    if bytes(h.uc.mem_read(obj + 0x7c4, 3)) != bytes(3):
        problems.append('mouse count %d: click flags were not cleared' % count)
    return problems


def _check_keys(h, count):
    obj = h.alloc(0x680, bytes(0x680))
    keys = h.alloc(max(2, count * 2), b'\xCC\x55' * max(1, count))
    h.uc.mem_write(obj + 0x48, b'\x7E' * 0x100)
    h.uc.mem_write(obj + 0x660, _dword(keys))
    h.uc.mem_write(obj + 0x664, _dword(count))

    diffs = h.compare(RESET_KEYS, regs={UC_X86_REG_ECX: obj}, ret=None)
    if diffs:
        return ['key count %d: %s' % (count, d) for d in diffs]
    result = h.call(RESET_KEYS, regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['key count %d: %s' % (count, result['fault'])]
    problems = []
    if bytes(h.uc.mem_read(obj + 0x48, 0x100)) != bytes(0x100):
        problems.append('key count %d: key state was not cleared' % count)
    for index in range(count):
        if bytes(h.uc.mem_read(keys + index * 2, 2)) != b'\x00\x55':
            problems.append('key count %d: key %d was not cleared' % (count, index))
    return problems


def test_reset_mouse(h):
    heap0 = h.heap_ptr
    try:
        problems = []
        for count in (0, 1, 3):
            problems += _check_mouse(h, count)
        return problems or None
    finally:
        h.heap_ptr = heap0


def test_reset_keys(h):
    heap0 = h.heap_ptr
    try:
        problems = []
        for count in (0, 1, 3):
            problems += _check_keys(h, count)
        return problems or None
    finally:
        h.heap_ptr = heap0
