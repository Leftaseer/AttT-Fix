"""CReadInterfaceDat ctor/dtor (0x004A7160 / 0x004A70C0): the record map and the two vtables."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX

from difftest import STACK, STACK_SIZE

VFT_CLASS = 0x00610088
VFT_SINGLETON = 0x00610080


def _zero_stack(h):
    """The original hands the map ctor an uninitialised stack byte (the allocator, never read); the runs must
    read the same stale value for their maps to compare equal."""
    h.uc.mem_write(STACK + STACK_SIZE - 0x8000, bytes(0x8000))


def _fill_empty(h, obj):
    h.uc.mem_write(obj, struct.pack('<I', VFT_CLASS))
    alloc = h.alloc(1, b'\0')
    h.call(0x004A7040, args=[alloc, alloc], regs={UC_X86_REG_ECX: obj + 0x04})


def test_interfacedat_ctor(h):
    obj = h.alloc(0x2C, bytes(0x2C))
    diffs = h.compare(0x004A7160, regs={UC_X86_REG_ECX: obj}, setup=_zero_stack, ret='eax')
    if diffs:
        return diffs
    res = h.call(0x004A7160, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if res['eax'] != obj:
        return ['ctor returned %#x, not this' % res['eax']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_CLASS:
        return ['the class vtable is not at +0']
    sentinel, size = struct.unpack('<II', h.uc.mem_read(obj + 0x0C, 8))
    mask, count = struct.unpack('<II', h.uc.mem_read(obj + 0x24, 8))
    if sentinel == 0 or size != 0:
        return ['map: sentinel %#x size %d' % (sentinel, size)]
    if mask != 1 or count != 1:
        return ['map: mask %d count %d' % (mask, count)]
    return []


def test_interfacedat_dtor(h):
    obj = h.alloc(0x2C, bytes(0x2C))

    def setup(h):
        _zero_stack(h)
        _fill_empty(h, obj)

    diffs = h.compare(0x004A70C0, regs={UC_X86_REG_ECX: obj}, setup=setup, ret=None)
    if diffs:
        return diffs
    res = h.call(0x004A70C0, regs={UC_X86_REG_ECX: obj})
    if res['fault']:
        return ['replacement faulted: %s' % res['fault']]
    if struct.unpack('<I', h.uc.mem_read(obj, 4))[0] != VFT_SINGLETON:
        return ['the singleton vtable is not at +0 after the dtor']
    for off in (0x0C, 0x18):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['+0x%X is not cleared' % off]
    for off in (0x1C, 0x20):
        if struct.unpack('<I', h.uc.mem_read(obj + off, 4))[0] != 0:
            return ['map end/limit +0x%X is not cleared' % off]
    return []
