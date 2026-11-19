"""0x004301F0 (ECX = the back buffer texture, no stack arguments): with +4 already set it builds and throws
"Нельзя дважды инициализировать CBackBufferTexture" (0x00608FE8 through 0x00607324 / 0x00607334, 0x005E3EC0 with
the throw info 0x0069916C).  Otherwise it allocates 0x54 bytes (0x005E3EAE), constructs them (0x004DF860 with half
of the screen, 0x006C8964 x 0x006C8960, one level, format 0x15, no pool), stores them at +4, calls the virtual
+0x2C for a0 and [a0]+0x48 (a0, 0, this+0xC), then D3DXCreateRenderToSurface (0x005B8050) for the device
0x006C8C10 into +8 and returns its result.  The stubs log what they see; the returning throw stub lets the code
behind the throw be compared too."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004301F0
NEW = 0x005E3EAE
CTOR = 0x004DF860
ROOT = 0x00427990
D3DX = 0x005B8050
THROW = 0x005E3EC0
STR_SLOT = 0x00607324
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'

MESSAGE = 0x00608FE8
THROW_INFO = 0x0069916C
G_HEIGHT = 0x006C8960
G_WIDTH = 0x006C8964
G_DEVICE = 0x006C8C10

L_NEW = 0x00
L_NEW_SIZE = 0x04
L_NEW_RESULT = 0x08
L_CTOR = 0x0C
L_CTOR_THIS = 0x10
L_CTOR_W = 0x14
L_CTOR_H = 0x18
L_CTOR_C = 0x1C
L_CTOR_D = 0x20
L_CTOR_USAGE = 0x24
L_CTOR_POOL = 0x28
L_ROOT = 0x2C
L_ROOT_VAL = 0x30
L_D3DX = 0x34
L_DEV = 0x38
L_W = 0x3C
L_H = 0x40
L_FMT = 0x44
L_DEPTH = 0x48
L_DFMT = 0x4C
L_OUT = 0x50
L_VFN = 0x54
L_CTX = 0x58
L_A0_VAL = 0x5C
L_SLOT = 0x60
L_SLOT_A0 = 0x64
L_SLOT_ZERO = 0x68
L_SLOT_THIRD = 0x6C
L_STR = 0x70
L_STR_ARG = 0x74
L_THROW = 0x78
L_THROW_INFO = 0x7C
LOG_SIZE = 0x80

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
    _patch(h, address, b'\xE9' + struct.pack('<i', _stub(h, code) - (address + 5)))


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def test_004301F0(h):
    heap0 = h.heap_ptr
    globals0 = {a: bytes(h.uc.mem_read(a, 4)) for a in (G_HEIGHT, G_WIDTH, G_DEVICE)}
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        block = h.alloc(0x54, b'\x33' * 0x54)
        _patch_thunk(h, NEW, b'\xFF\x05' + _dword(log + L_NEW)                   # inc [new]
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_NEW_SIZE)        # size -> [new size]
                     + b'\xA1' + _dword(log + L_NEW_RESULT)                      # eax = [new result]
                     + b'\xC3')                                                  # ret
        _patch_thunk(h, CTOR, b'\xFF\x05' + _dword(log + L_CTOR)                 # inc [ctor]
                     + b'\x89\x0D' + _dword(log + L_CTOR_THIS)                   # this -> [ctor this]
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_CTOR_W)
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_CTOR_H)
                     + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_CTOR_C)
                     + b'\x8B\x44\x24\x10\xA3' + _dword(log + L_CTOR_D)
                     + b'\x8B\x44\x24\x14\xA3' + _dword(log + L_CTOR_USAGE)
                     + b'\x8B\x44\x24\x18\xA3' + _dword(log + L_CTOR_POOL)
                     + b'\x8B\xC1'                                               # eax = ecx
                     + b'\xC2\x18\x00')                                          # ret 0x18
        _patch_thunk(h, ROOT, b'\xFF\x05' + _dword(log + L_ROOT)                 # inc [root]
                     + b'\xA1' + _dword(log + L_ROOT_VAL)                        # eax = [root]
                     + b'\xC3')                                                  # ret
        _patch_thunk(h, D3DX, b'\xFF\x05' + _dword(log + L_D3DX)                 # inc [d3dx]
                     + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_DEV)
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_W)
                     + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_H)
                     + b'\x8B\x44\x24\x10\xA3' + _dword(log + L_FMT)
                     + b'\x8B\x44\x24\x14\xA3' + _dword(log + L_DEPTH)
                     + b'\x8B\x44\x24\x18\xA3' + _dword(log + L_DFMT)
                     + b'\x8B\x44\x24\x1C\xA3' + _dword(log + L_OUT)
                     + b'\x8B\x44\x24\x1C\xC7\x00' + _dword(0x12345678)          # *out = 12345678
                     + b'\xB8' + _dword(0x11223344)                              # eax = hr
                     + b'\xC2\x1C\x00')                                          # ret 0x1C
        stub_vfn = _stub(h, b'\xFF\x05' + _dword(log + L_VFN)                    # inc [virtual]
                         + b'\x89\x0D' + _dword(log + L_CTX)                     # ecx -> [ctx]
                         + b'\xA1' + _dword(log + L_A0_VAL)                      # eax = [a0]
                         + b'\xC3')                                              # ret
        stub_slot = _stub(h, b'\xFF\x05' + _dword(log + L_SLOT)                  # inc [slot]
                          + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_SLOT_A0)
                          + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_SLOT_ZERO)
                          + b'\x8B\x44\x24\x0C\xA3' + _dword(log + L_SLOT_THIRD)
                          + b'\xC2\x0C\x00')                                     # ret 0xC
        _patch_import(h, STR_SLOT, STR_SYM,
                      b'\xFF\x05' + _dword(log + L_STR)                          # inc [string]
                      + b'\x8B\x44\x24\x04\xA3' + _dword(log + L_STR_ARG)        # literal -> [arg]
                      + b'\xC7\x41\x14\x00\x00\x00\x00'                          # size 0
                      + b'\xC7\x41\x18\x0F\x00\x00\x00'                          # capacity 15 (SSO)
                      + b'\xC6\x41\x04\x00'                                      # empty buffer
                      + b'\x8B\xC1'                                              # eax = ecx
                      + b'\xC2\x04\x00')                                         # ret 4
        _patch_thunk(h, THROW, b'\xFF\x05' + _dword(log + L_THROW)               # inc [throw]
                     + b'\x8B\x44\x24\x08\xA3' + _dword(log + L_THROW_INFO)      # info -> [info]
                     + b'\x31\xC0'                                               # xor eax, eax
                     + b'\xC2\x08\x00')                                          # ret 8
        vt2 = h.alloc(0x100, bytes(0x100))
        vt3 = h.alloc(0x100, bytes(0x100))
        h.uc.mem_write(vt2 + 0x2c, _dword(stub_vfn))
        h.uc.mem_write(vt3 + 0x48, _dword(stub_slot))
        a0 = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(a0, _dword(vt3))
        root = h.alloc(0x80, bytes(0x80))
        self = h.alloc(0x30, bytes(0x30))
        DEV = 0x60006000
        WIDTH = 800
        HEIGHT = 600
        DFMT = 0x77770001

        def setup(handle):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + L_NEW_RESULT, _dword(block))
            h.uc.mem_write(log + L_A0_VAL, _dword(a0))
            h.uc.mem_write(log + L_ROOT_VAL, _dword(root))
            h.uc.mem_write(G_HEIGHT, _dword(HEIGHT))
            h.uc.mem_write(G_WIDTH, _dword(WIDTH))
            h.uc.mem_write(G_DEVICE, _dword(DEV))
            h.uc.mem_write(root, b'\x22' * 0x80)
            h.uc.mem_write(root + 0x5c, _dword(DFMT))
            h.uc.mem_write(self, b'\x11' * 0x30)
            h.uc.mem_write(self + 4, _dword(handle))
            h.uc.mem_write(block, _dword(vt2) + bytes(0x50))

        # the first initialisation
        setup(0)
        diffs = h.compare(THIS, regs={UC_X86_REG_ECX: self}, ret='eax')
        if diffs:
            return ['first: %s' % d for d in diffs]
        setup(0)
        res = h.call(THIS, regs={UC_X86_REG_ECX: self})
        if res['fault']:
            return ['first: replacement faulted: %s' % (res['fault'],)]
        if res['eax'] != 0x11223344:
            return ['first: returned %08X' % res['eax']]
        if res['esp'] != 4:
            return ['first: stack delta %d, not 4' % res['esp']]
        if _u32(h, log + L_NEW) != 1 or _u32(h, log + L_NEW_SIZE) != 0x54:
            return ['first: the allocator ran %d times for %d bytes'
                    % (_u32(h, log + L_NEW), _u32(h, log + L_NEW_SIZE))]
        if _u32(h, log + L_CTOR) != 1 or _u32(h, log + L_CTOR_THIS) != block:
            return ['first: the constructor ran %d times on %08X'
                    % (_u32(h, log + L_CTOR), _u32(h, log + L_CTOR_THIS))]
        got = tuple(_u32(h, log + o) for o in (L_CTOR_W, L_CTOR_H, L_CTOR_C, L_CTOR_D,
                                               L_CTOR_USAGE, L_CTOR_POOL))
        want = (WIDTH >> 1, HEIGHT >> 1, 1, 1, 0x15, 0)
        if got != want:
            return ['first: constructed as %r, not %r' % (got, want)]
        if _u32(h, self + 4) != block:
            return ['first: the texture is %08X' % _u32(h, self + 4)]
        if _u32(h, log + L_VFN) != 1 or _u32(h, log + L_CTX) != block:
            return ['first: the virtual ran %d times on %08X'
                    % (_u32(h, log + L_VFN), _u32(h, log + L_CTX))]
        if _u32(h, log + L_SLOT) != 1:
            return ['first: the surface slot ran %d times' % _u32(h, log + L_SLOT)]
        if (_u32(h, log + L_SLOT_A0) != a0 or _u32(h, log + L_SLOT_ZERO) != 0
                or _u32(h, log + L_SLOT_THIRD) != self + 0xc):
            return ['first: the surface slot got (%08X, %08X, %08X)'
                    % (_u32(h, log + L_SLOT_A0), _u32(h, log + L_SLOT_ZERO),
                       _u32(h, log + L_SLOT_THIRD))]
        if _u32(h, log + L_ROOT) != 1 or _u32(h, log + L_D3DX) != 1:
            return ['first: %d data root and %d create calls' % (_u32(h, log + L_ROOT), _u32(h, log + L_D3DX))]
        got = tuple(_u32(h, log + o) for o in (L_DEV, L_W, L_H, L_FMT, L_DEPTH, L_DFMT))
        want = (DEV, WIDTH >> 1, HEIGHT >> 1, 0x15, 1, DFMT)
        if got != want:
            return ['first: the surface was created as %r, not %r' % (got, want)]
        if _u32(h, log + L_OUT) != self + 8 or _u32(h, self + 8) != 0x12345678:
            return ['first: the surface went to %08X, handle %08X'
                    % (_u32(h, log + L_OUT), _u32(h, self + 8))]
        if _u32(h, log + L_STR) or _u32(h, log + L_THROW):
            return ['first: a string was built or thrown']

        # the second initialisation: the string, the returning throw, then the ordinary path behind it
        setup(block)
        diffs = h.compare(THIS, regs={UC_X86_REG_ECX: self}, ret='eax')
        if diffs:
            return ['second: %s' % d for d in diffs]
        setup(block)
        res = h.call(THIS, regs={UC_X86_REG_ECX: self})
        if res['fault']:
            return ['second: replacement faulted: %s' % (res['fault'],)]
        if _u32(h, log + L_STR) != 1 or _u32(h, log + L_STR_ARG) != MESSAGE:
            return ['second: the message built %d times from %08X'
                    % (_u32(h, log + L_STR), _u32(h, log + L_STR_ARG))]
        if _u32(h, log + L_THROW) != 1 or _u32(h, log + L_THROW_INFO) != THROW_INFO:
            return ['second: %d throws with info %08X'
                    % (_u32(h, log + L_THROW), _u32(h, log + L_THROW_INFO))]

        # the real throw: the allocation must not happen
        h.uc.mem_write(THROW, saved[THROW])
        h.uc.ctl_remove_cache(THROW, THROW + 5)
        setup(block)
        res = h.call(THIS, regs={UC_X86_REG_ECX: self})
        if res['fault'] != 'threw':
            return ['throw: fault %r, not threw' % (res['fault'],)]
        if _u32(h, log + L_NEW) or _u32(h, log + L_CTOR) or _u32(h, log + L_D3DX):
            return ['throw: the texture was built after all']
        if _u32(h, log + L_STR_ARG) != MESSAGE:
            return ['throw: the message came from %08X' % _u32(h, log + L_STR_ARG)]
        h.heap_ptr = heap0
    finally:
        for a, v in globals0.items():
            h.uc.mem_write(a, v)
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
