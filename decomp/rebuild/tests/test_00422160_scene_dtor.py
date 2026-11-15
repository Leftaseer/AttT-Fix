"""sub_00422160 (size 224, ECX thiscall, ret 0): the 2D scene's destructor.  The vtables 0x00607C44 (+0) and
0x00607C24 (+4) go in first and 0x004212B0 releases the collector state on this+4; the objects at +0x84 and +0x88
are deleted through the first vtable slot with flag 1; the arrays at +0xAC and +0x98 are freed with 0x005E3EBA after
the vtables 0x00607B74 and 0x00607B6C are stored at +0xA8 and +0x94; the base destructor 0x004B2010 closes."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

VF = 0x00422160
RELEASE = 0x004212B0
DELETE = 0x005E3EBA
BASE = 0x004B2010

VT0 = 0x00607C44
VT1 = 0x00607C24
VT_A8 = 0x00607B74
VT_94 = 0x00607B6C

L_VT0 = 0x00
L_VT1 = 0x04
L_R_THIS = 0x08
L_R_STEP = 0x0C
L_R_COUNT = 0x10
L_DT_THIS = 0x14
L_DT_FLAG = 0x1C
L_DT_STEP = 0x20
L_DT_COUNT = 0x28
L_DEL_BLOCK = 0x2C
L_DEL_STEP = 0x34
L_DEL_A8 = 0x3C
L_DEL_94 = 0x44
L_DEL_COUNT = 0x4C
L_BASE_THIS = 0x50
L_BASE_STEP = 0x54
L_BASE_COUNT = 0x58
L_SELF = 0x5C
L_STEP = 0x60
LOG_SIZE = 0x70

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, code):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(code))))
    h.uc.mem_write(address, code)
    h.uc.ctl_remove_cache(address, address + len(code))


def _stub(h, code):
    return h.alloc(len(code), code)


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _patch_callee(h, address, code):
    _patch_thunk(h, address, code)
    target = h.symbols.get('_sub_%08X' % address)
    if target is not None and target != address:
        _patch_thunk(h, target, code)


def _release_body(log):
    return (b'\x89\x0D' + _dword(log + L_R_THIS)                          # mov [this], ecx
            + b'\xA1' + _dword(log + L_STEP)                               # mov eax, [step]
            + b'\xA3' + _dword(log + L_R_STEP)                             # mov [rstep], eax
            + b'\x8B\x41\xFC'                                              # mov eax, [ecx-4]
            + b'\xA3' + _dword(log + L_VT0)
            + b'\x8B\x01'                                                  # mov eax, [ecx]
            + b'\xA3' + _dword(log + L_VT1)
            + b'\xFF\x05' + _dword(log + L_R_COUNT)
            + b'\xFF\x05' + _dword(log + L_STEP)
            + b'\xC3')


def _release_ecx_stub(log):
    return _release_body(log)


def _release_args_stub(log):
    return b'\x8B\x4C\x24\x04' + _release_body(log)                        # mov ecx, [esp+4]


def _dtor_stub(log):
    return (b'\xFF\x05' + _dword(log + L_DT_COUNT)                         # inc [count]
            + b'\xA1' + _dword(log + L_DT_COUNT)
            + b'\x48'                                                      # dec eax (the call index)
            + b'\x89\x0C\x85' + _dword(log + L_DT_THIS)                    # this[index]
            + b'\x8B\x15' + _dword(log + L_STEP)                           # mov edx, [step]
            + b'\x89\x14\x85' + _dword(log + L_DT_STEP)                    # step[index]
            + b'\x8B\x54\x24\x04'                                          # mov edx, [esp+4] (flag)
            + b'\x09\x15' + _dword(log + L_DT_FLAG)                        # or [flag], edx
            + b'\xFF\x05' + _dword(log + L_STEP)
            + b'\xC2\x04\x00')


def _delete_stub(log):
    return (b'\xFF\x05' + _dword(log + L_DEL_COUNT)
            + b'\xA1' + _dword(log + L_DEL_COUNT)
            + b'\x48'                                                      # dec eax (the call index)
            + b'\x89\xC2'                                                  # mov edx, eax (the index)
            + b'\x8B\x44\x24\x04'                                          # mov eax, [esp+4] (block)
            + b'\x89\x04\x95' + _dword(log + L_DEL_BLOCK)                  # block[index]
            + b'\xA1' + _dword(log + L_STEP)
            + b'\x89\x04\x95' + _dword(log + L_DEL_STEP)                   # step[index]
            + b'\x8B\x0D' + _dword(log + L_SELF)                           # mov ecx, [self]
            + b'\x8B\x81' + _dword(0xA8)                                   # mov eax, [ecx+0xA8]
            + b'\x89\x04\x95' + _dword(log + L_DEL_A8)
            + b'\x8B\x81' + _dword(0x94)                                   # mov eax, [ecx+0x94]
            + b'\x89\x04\x95' + _dword(log + L_DEL_94)
            + b'\xFF\x05' + _dword(log + L_STEP)
            + b'\xC3')


def _base_stub(log):
    return (b'\x89\x0D' + _dword(log + L_BASE_THIS)
            + b'\xA1' + _dword(log + L_STEP)
            + b'\xA3' + _dword(log + L_BASE_STEP)
            + b'\xFF\x05' + _dword(log + L_BASE_COUNT)
            + b'\xFF\x05' + _dword(log + L_STEP)
            + b'\xC3')


def test_00422160(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch(h, RELEASE, _release_ecx_stub(log))
        glue = h.symbols.get('_sub_%08X' % RELEASE)
        if glue is not None and glue != RELEASE:
            _patch_thunk(h, glue, _release_args_stub(log))
        _patch_callee(h, DELETE, _delete_stub(log))
        _patch_callee(h, BASE, _base_stub(log))
        dtor = _stub(h, _dtor_stub(log))
        table = h.alloc(8, _dword(dtor) + bytes(4))
        obj84 = h.alloc(0x10, _dword(table) + bytes(0xC))
        obj88 = h.alloc(0x10, _dword(table) + bytes(0xC))
        block_ac = h.alloc(0x10, bytes(0x10))
        block_98 = h.alloc(0x10, bytes(0x10))
        self = h.alloc(0xC0, bytes(0xC0))
        for full in (True, False):
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(log + L_SELF, _dword(self))
                h.uc.mem_write(self, b'\x99' * 0xC0)
                if full:
                    h.uc.mem_write(self + 0x84, _dword(obj84))
                    h.uc.mem_write(self + 0x88, _dword(obj88))
                    h.uc.mem_write(self + 0xAC, _dword(block_ac))
                    h.uc.mem_write(self + 0x98, _dword(block_98))
                else:
                    h.uc.mem_write(self + 0x84, bytes(0x10))
                    h.uc.mem_write(self + 0x98, bytes(4))
                    h.uc.mem_write(self + 0xAC, bytes(4))
            diffs = h.compare(VF, regs={UC_X86_REG_ECX: self}, setup=lambda hh: setup(), ret=None)
            if diffs:
                return ['%s: %s' % ('full' if full else 'empty', d) for d in diffs]
            setup()
            res = h.call(VF, regs={UC_X86_REG_ECX: self})
            if res['fault']:
                return ['%s: replacement faulted: %s' % ('full' if full else 'empty', res['fault'])]
            tag = 'full' if full else 'empty'
            if _u32(h, log + L_R_COUNT) != 1:
                return ['%s: the collector release ran %d times' % (tag, _u32(h, log + L_R_COUNT))]
            if _u32(h, log + L_R_THIS) != self + 4:
                return ['%s: the collector release got %08X, not this+4' % (tag, _u32(h, log + L_R_THIS))]
            if _u32(h, log + L_VT0) != VT0 or _u32(h, log + L_VT1) != VT1:
                return ['%s: the release saw vtables %08X/%08X'
                        % (tag, _u32(h, log + L_VT0), _u32(h, log + L_VT1))]
            want_dtors = 2 if full else 0
            if _u32(h, log + L_DT_COUNT) != want_dtors:
                return ['%s: %d objects deleted through their vtable' % (tag, _u32(h, log + L_DT_COUNT))]
            want_deletes = 2 if full else 0
            if _u32(h, log + L_DEL_COUNT) != want_deletes:
                return ['%s: the operator delete ran %d times' % (tag, _u32(h, log + L_DEL_COUNT))]
            if _u32(h, log + L_BASE_COUNT) != 1 or _u32(h, log + L_BASE_THIS) != self:
                return ['%s: the base destructor ran %d times on %08X'
                        % (tag, _u32(h, log + L_BASE_COUNT), _u32(h, log + L_BASE_THIS))]
            if full:
                if (_u32(h, log + L_DT_THIS) != obj84 or _u32(h, log + L_DT_THIS + 4) != obj88
                        or _u32(h, log + L_DT_FLAG) != 1):
                    return ['%s: the deleted objects are %08X/%08X with flags %X'
                            % (tag, _u32(h, log + L_DT_THIS), _u32(h, log + L_DT_THIS + 4),
                               _u32(h, log + L_DT_FLAG))]
                if (_u32(h, log + L_DEL_BLOCK) != block_ac or _u32(h, log + L_DEL_BLOCK + 4) != block_98):
                    return ['%s: the blocks freed are %08X/%08X'
                            % (tag, _u32(h, log + L_DEL_BLOCK), _u32(h, log + L_DEL_BLOCK + 4))]
                if _u32(h, log + L_DEL_A8) != VT_A8 or _u32(h, log + L_DEL_A8 + 4) != VT_A8:
                    return ['%s: +0xA8 held %08X/%08X at the delete calls'
                            % (tag, _u32(h, log + L_DEL_A8), _u32(h, log + L_DEL_A8 + 4))]
                if _u32(h, log + L_DEL_94) != 0x99999999 or _u32(h, log + L_DEL_94 + 4) != VT_94:
                    return ['%s: +0x94 held %08X/%08X at the delete calls'
                            % (tag, _u32(h, log + L_DEL_94), _u32(h, log + L_DEL_94 + 4))]
                steps = [_u32(h, log + L_R_STEP), _u32(h, log + L_DT_STEP), _u32(h, log + L_DT_STEP + 4),
                         _u32(h, log + L_DEL_STEP), _u32(h, log + L_DEL_STEP + 4), _u32(h, log + L_BASE_STEP)]
                if steps != sorted(steps) or len(set(steps)) != len(steps):
                    return ['%s: the order is %r' % (tag, steps)]
                if _u32(h, self + 0x84) or _u32(h, self + 0x88) or _u32(h, self + 0xAC) or _u32(h, self + 0x98):
                    return ['%s: a released pointer is still set' % tag]
            else:
                if _u32(h, self + 0x84) or _u32(h, self + 0x88) or _u32(h, self + 0xAC) or _u32(h, self + 0x98):
                    return ['%s: a field changed that held null' % tag]
            if _u32(h, self) != VT0 or _u32(h, self + 4) != VT1:
                return ['%s: the scene ends with vtables %08X/%08X' % (tag, _u32(h, self), _u32(h, self + 4))]
            if _u32(h, self + 0xA8) != VT_A8 or _u32(h, self + 0x94) != VT_94:
                return ['%s: the arrays end with vtables %08X/%08X'
                        % (tag, _u32(h, self + 0xA8), _u32(h, self + 0x94))]
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
