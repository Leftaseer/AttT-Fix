"""sub_004219E0 (size 112, cdecl, 2 stack args), sub_00421AB0 / sub_00421B50 (size 160 / 176, ECX thiscall, ret 4):
copy constructors.  0x004219E0 does nothing for a null destination; otherwise it copies the string at +0 (MSVCP80,
IAT 0x607334) and the four dwords at +0x1C..+0x28 and returns nothing.  0x00421AB0 copies the strings at +0, +0xAC,
+0xC8 and the blocks at +0x1C, +0x64 through 0x00421150.  0x00421B50 copies the strings at +0, +0xB4, the blocks at
+0x1C, +0x68, +0xD0 and the floats at +0x64, +0xB0; both return this."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

IAT_STR = 0x00607334
BLOCK = 0x00421150

L_STR_CALLS = 0x00
L_STR_ARGS = 0x08
L_BLK_CALLS = 0x28
L_BLK_ARGS = 0x30
LOG_SIZE = 0x60

STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z'

CASES = {
    0x004219E0: (False, [('str', 0x00), ('dword', 0x1C)]),
    0x00421AB0: (True, [('str', 0x00), ('blk', 0x1C), ('blk', 0x64), ('str', 0xAC), ('str', 0xC8)]),
    0x00421B50: (True, [('str', 0x00), ('blk', 0x1C), ('float', 0x64), ('blk', 0x68), ('float', 0xB0),
                        ('str', 0xB4), ('blk', 0xD0)]),
}

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
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _patch_thunk(h, address, code):
    stub = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', stub - (address + 5)))


def _patch_callee(h, address, code):
    _patch_thunk(h, address, code)
    target = h.symbols.get('_sub_%08X' % address)
    if target is not None and target != address:
        _patch_thunk(h, target, code)


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def _pair_stub(log, calls, args, marker):
    return (b'\xFF\x05' + _dword(log + calls)                               # inc [calls]
            + b'\xA1' + _dword(log + calls)                                 # mov eax, [calls]
            + b'\x48'                                                       # dec eax (call index)
            + b'\x89\x0C\xC5' + _dword(log + args)                          # ecx -> this[index]
            + b'\x8B\x54\x24\x04'                                           # mov edx, [esp+4] (src)
            + b'\x89\x14\xC5' + _dword(log + args + 4)                      # edx -> src[index]
            + marker
            + b'\xC2\x04\x00')                                              # ret 4


def _check(h, vf):
    thiscall, steps = CASES[vf]
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_import(h, IAT_STR, STR_SYM, _pair_stub(
            log, L_STR_CALLS, L_STR_ARGS,
            b'\xC7\x01' + _dword(0xBBBBBBBB)                                # mov [ecx], BBBB
            + b'\xC7\x41\x04' + _dword(0xCCCCCCCC)                          # mov [ecx+4], CCCC
            + b'\xC7\x41\x08' + _dword(0xDDDDDDDD)))                        # mov [ecx+8], DDDD
        _patch_callee(h, BLOCK, _pair_stub(
            log, L_BLK_CALLS, L_BLK_ARGS, b'\xC7\x01' + _dword(0xE1E1E1E1)))  # mov [ecx], E1E1
        this = h.alloc(0x100, bytes(0x100))
        src = h.alloc(0x100, bytes(0x100))
        SRC = bytes(range(0x100))
        want = bytearray(b'\x11' * 0x100)
        for kind, off in steps:
            if kind == 'str':
                want[off:off + 4] = _dword(0xBBBBBBBB)
                want[off + 4:off + 8] = _dword(0xCCCCCCCC)
                want[off + 8:off + 12] = _dword(0xDDDDDDDD)
            elif kind == 'blk':
                want[off:off + 4] = _dword(0xE1E1E1E1)
            elif kind == 'dword':
                want[off:off + 16] = SRC[off:off + 16]
            else:
                want[off:off + 4] = SRC[off:off + 4]

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(this, b'\x11' * 0x100)
            h.uc.mem_write(src, SRC)

        regs = {UC_X86_REG_ECX: this} if thiscall else None
        args = [src] if thiscall else [this, src]
        diffs = h.compare(vf, args=args, regs=regs, setup=lambda hh: setup(), ret='eax' if thiscall else None)
        if diffs:
            return diffs
        setup()
        res = h.call(vf, args=args, regs=regs)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if thiscall and res['eax'] != this:
            return ['returned %08X' % res['eax']]
        str_steps = [off for kind, off in steps if kind == 'str']
        blk_steps = [off for kind, off in steps if kind == 'blk']
        if _u32(h, log + L_STR_CALLS) != len(str_steps):
            return ['the strings were copied %d times' % _u32(h, log + L_STR_CALLS)]
        if _u32(h, log + L_BLK_CALLS) != len(blk_steps):
            return ['the blocks were copied %d times' % _u32(h, log + L_BLK_CALLS)]
        for i, off in enumerate(str_steps):
            got = (_u32(h, log + L_STR_ARGS + 8 * i), _u32(h, log + L_STR_ARGS + 8 * i + 4))
            if got != (this + off, src + off):
                return ['string %d copied from (%08X, %08X)' % (i, got[0], got[1])]
        for i, off in enumerate(blk_steps):
            got = (_u32(h, log + L_BLK_ARGS + 8 * i), _u32(h, log + L_BLK_ARGS + 8 * i + 4))
            if got != (this + off, src + off):
                return ['block %d copied from (%08X, %08X)' % (i, got[0], got[1])]
        if bytes(h.uc.mem_read(this, 0x100)) != bytes(want):
            return ['the record is not laid out as the copy steps say']
        if bytes(h.uc.mem_read(src, 0x100)) != SRC:
            return ['the source changed']
        if not thiscall:
            setup()
            res = h.call(vf, args=[0, src])
            if res['fault']:
                return ['null: replacement faulted: %s' % res['fault']]
            if _u32(h, log + L_STR_CALLS) or _u32(h, log + L_BLK_CALLS):
                return ['null: the strings or blocks were copied anyway']
            if bytes(h.uc.mem_read(src, 0x100)) != SRC:
                return ['null: the source changed']
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None


def test_004219E0(h):
    return _check(h, 0x004219E0)


def test_00421AB0(h):
    return _check(h, 0x00421AB0)


def test_00421B50(h):
    return _check(h, 0x00421B50)
