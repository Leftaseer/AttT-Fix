"""Town::~Town (0x005360F0): sets the vftable, removes the town from the world's list when the world (+0x40) has one,
closes the object at +0x1F8, releases the banner at +0x1F4 and destroys the base object.  The list removal and the
base destructor are replaced by recording stubs; the two virtual calls go to small stubs allocated in the heap."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

DTOR = 0x005360F0
REMOVE = 0x005ADCD0
BASE = 0x005B4050

WORLD = 0x006C88D8
VTABLE = 0x00615A3C

LOG_REMOVE_THIS = 0x00
LOG_REMOVE_ARG = 0x04
LOG_REMOVE_VFT = 0x08
LOG_REMOVE_COUNT = 0x0C
LOG_BASE_THIS = 0x10
LOG_BASE_COUNT = 0x14
LOG_VF6C_THIS = 0x18
LOG_VF6C_COUNT = 0x1C
LOG_RELEASE_THIS = 0x20
LOG_RELEASE_ARG = 0x24
LOG_RELEASE_COUNT = 0x28


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _mov_eax_arg(index):
    return b'\x8B\x44\x24' + bytes([4 * index])


def _store_eax(addr):
    return b'\xA3' + struct.pack('<I', addr)


def _store_ecx(addr):
    return b'\x89\x0D' + struct.pack('<I', addr)


def _store_edx(addr):
    return b'\x89\x15' + struct.pack('<I', addr)


def _inc(addr):
    return b'\xFF\x05' + struct.pack('<I', addr)


def _ret4():
    return b'\xC2\x04\x00'


def _patch(h, address, code, saved):
    if address not in saved:
        saved[address] = bytes(h.uc.mem_read(address, 32))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _object(h, vtable, refs):
    o = h.alloc(0x10, bytes(0x10))
    h.uc.mem_write(o, struct.pack('<II', vtable, refs))
    return o


def _stubs(h, log):
    _patch(h, REMOVE,
           _store_ecx(log + LOG_REMOVE_THIS)
           + _mov_eax_arg(1) + _store_eax(log + LOG_REMOVE_ARG)
           + b'\x8B\x10' + _store_edx(log + LOG_REMOVE_VFT)       # the vftable is already the new one
           + _inc(log + LOG_REMOVE_COUNT)
           + _ret4(), _stubs.saved)
    _patch(h, BASE, _store_ecx(log + LOG_BASE_THIS) + _inc(log + LOG_BASE_COUNT) + b'\xC3', _stubs.saved)
    vf6c = h.alloc(32, _store_ecx(log + LOG_VF6C_THIS) + _inc(log + LOG_VF6C_COUNT) + b'\xC3')
    release = h.alloc(32, _store_ecx(log + LOG_RELEASE_THIS) + _mov_eax_arg(1) + _store_eax(log + LOG_RELEASE_ARG)
                      + _inc(log + LOG_RELEASE_COUNT) + _ret4())
    return vf6c, release


_stubs.saved = {}


def _case(h, flag, with_obj, banner_refs):
    log = h.alloc(0x30, bytes(0x30))
    vf6c, release = _stubs(h, log)
    obj = 0
    if with_obj:
        vtable = h.alloc(0xF0, bytes(0xF0))
        h.uc.mem_write(vtable + 0x6C, struct.pack('<I', vf6c))
        obj = _object(h, vtable, 1)
    banner = 0
    if banner_refs is not None:
        vtable = h.alloc(0xF0, bytes(0xF0))
        h.uc.mem_write(vtable, struct.pack('<I', release))
        banner = _object(h, vtable, banner_refs)
    world = h.alloc(0x60, bytes(0x60))
    h.uc.mem_write(world + 0x40, bytes([flag]))
    town = h.alloc(0x200, bytes(0x200))
    h.uc.mem_write(town + 0x1F4, struct.pack('<I', banner))
    h.uc.mem_write(town + 0x1F8, struct.pack('<I', obj))
    h.uc.mem_write(WORLD, struct.pack('<I', world))
    return {'log': log, 'world': world, 'town': town, 'obj': obj, 'banner': banner}


def test_town_dtor(h):
    saved_world = bytes(h.uc.mem_read(WORLD, 4))
    _stubs.saved = {}
    heap0 = h.heap_ptr
    try:
        for flag, with_obj, banner_refs in ((1, True, 2), (0, False, 1), (0, False, None)):
            s = _case(h, flag, with_obj, banner_refs)
            diffs = h.compare(DTOR, regs={UC_X86_REG_ECX: s['town']}, ret=None)
            if diffs:
                return ['flag %d: %s' % (flag, d) for d in diffs]
            res = h.call(DTOR, regs={UC_X86_REG_ECX: s['town']})
            if res['fault']:
                return ['flag %d: replacement faulted: %s' % (flag, res['fault'])]
            log, town = s['log'], s['town']
            if _u32(h, town) != VTABLE:
                return ['flag %d: vftable %08X' % (flag, _u32(h, town))]
            if _u32(h, log + LOG_REMOVE_COUNT) != flag:
                return ['flag %d: remove called %d times' % (flag, _u32(h, log + LOG_REMOVE_COUNT))]
            if flag:
                if _u32(h, log + LOG_REMOVE_THIS) != s['world'] or _u32(h, log + LOG_REMOVE_ARG) != town:
                    return ['flag %d: remove called with %08X/%08X' % (flag, _u32(h, log + LOG_REMOVE_THIS),
                                                                       _u32(h, log + LOG_REMOVE_ARG))]
                if _u32(h, log + LOG_REMOVE_VFT) != VTABLE:
                    return ['flag %d: remove saw vftable %08X' % (flag, _u32(h, log + LOG_REMOVE_VFT))]
            if _u32(h, log + LOG_VF6C_COUNT) != int(with_obj):
                return ['flag %d: vf6C called %d times' % (flag, _u32(h, log + LOG_VF6C_COUNT))]
            if with_obj and _u32(h, log + LOG_VF6C_THIS) != s['obj']:
                return ['flag %d: vf6C called on %08X' % (flag, _u32(h, log + LOG_VF6C_THIS))]
            if banner_refs is None:
                if _u32(h, log + LOG_RELEASE_COUNT) != 0:
                    return ['flag %d: released a null banner' % (flag,)]
            elif banner_refs > 1:
                if _u32(h, log + LOG_RELEASE_COUNT) != 0 or _u32(h, s['banner'] + 4) != banner_refs - 1:
                    return ['flag %d: banner %d refs %d/%d' % (flag, banner_refs, _u32(h, log + LOG_RELEASE_COUNT),
                                                               _u32(h, s['banner'] + 4))]
            else:
                if _u32(h, log + LOG_RELEASE_COUNT) != 1 or _u32(h, log + LOG_RELEASE_THIS) != s['banner']:
                    return ['flag %d: release called %d times on %08X' % (flag, _u32(h, log + LOG_RELEASE_COUNT),
                                                                          _u32(h, log + LOG_RELEASE_THIS))]
                if _u32(h, log + LOG_RELEASE_ARG) != 1 or _u32(h, s['banner'] + 4) != 0:
                    return ['flag %d: released with %d, refs %d' % (flag, _u32(h, log + LOG_RELEASE_ARG),
                                                                    _u32(h, s['banner'] + 4))]
            if _u32(h, log + LOG_BASE_COUNT) != 1 or _u32(h, log + LOG_BASE_THIS) != town:
                return ['flag %d: base destroyed %d times on %08X' % (flag, _u32(h, log + LOG_BASE_COUNT),
                                                                      _u32(h, log + LOG_BASE_THIS))]
            h.heap_ptr = heap0
    finally:
        h.uc.mem_write(WORLD, saved_world)
        for address, code in _stubs.saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + 32)
        _stubs.saved = {}
        h.heap_ptr = heap0
    return None
