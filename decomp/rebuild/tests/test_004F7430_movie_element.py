"""0x004F7430 (ECX = the new element, a by-value 28-byte string name and an int flag, ret 0x20): builds the Bink
player at +4 (0x00430B80) and the animation at +0x1C (0x004CAA00), both with the device at 0x6C8C10; opens the name
as a CGameFile without loading (0x00459290), plays that file (0x00430EA0) with its FsFile size and the flag; hands
the player's sound system (+8) to the animation (0x004CA710); sizes the animation at the origin from 0x00430DC0
(width) and 0x00430DD0 (height), both taken as unsigned; destroys the CGameFile (0x00459170) and the name (the
string destructor import 0x607330); returns this.  Every callee is a stub that logs what it sees; whether the
CGameFile destructor runs before the string destructor is recorded in a shared order slot."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x004F7430
MOVIE = 0x00430B80
ANIM = 0x004CAA00
GFILE = 0x00459290
PLAY = 0x00430EA0
SND = 0x004CA710
HEI = 0x00430DD0
WID = 0x00430DC0
RECT = 0x004CA820
GFDTOR = 0x00459170
STR_SLOT = 0x00607330
STR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
DEVICE_GLOBAL = 0x006C8C10
VTBL = 0x00612D6C

WIDTH = 640
HEIGHT = 480
FILE_SIZE = 0x1234
SOUND = 0xCAFEBABE

N_MOVIE = 0x00
MOVIE_THIS = 0x04
MOVIE_DEV = 0x08
N_ANIM = 0x0C
ANIM_THIS = 0x10
ANIM_DEV = 0x14
N_GFILE = 0x18
GFILE_THIS = 0x1C
GFILE_NAME = 0x20
GFILE_NOLOAD = 0x24
N_PLAY = 0x28
PLAY_THIS = 0x2C
PLAY_FILE = 0x30
PLAY_SIZE = 0x34
PLAY_FLAGS = 0x38
N_SND = 0x3C
SND_THIS = 0x40
SND_ARG = 0x44
N_HEI = 0x48
N_WID = 0x4C
N_RECT = 0x50
RECT_THIS = 0x54
RECT_X = 0x58
RECT_Y = 0x5C
RECT_W = 0x60
RECT_H = 0x64
N_GFDTOR = 0x68
GFDTOR_THIS = 0x6C
N_STRDTOR = 0x70
STRDTOR_ARG = 0x74
SEQ = 0x78
LOG_SIZE = 0x80

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _f32(h, addr):
    return struct.unpack('<f', h.uc.mem_read(addr, 4))[0]


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
    target = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', target - (address + 5)))


def _patch_import(h, original_slot, symbol, code):
    stub = _stub(h, code)
    for slot in (original_slot, h.symbols[symbol]):
        _patch(h, slot, _dword(stub))


def test_004F7430(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, MOVIE, b'\x89\x0D' + _dword(log + MOVIE_THIS)
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + MOVIE_DEV)
                     + b'\xFF\x05' + _dword(log + N_MOVIE)
                     + b'\x8B\xC1'                                             # eax = this
                     + b'\xC2\x04\x00')                                        # ret 4
        _patch_thunk(h, ANIM, b'\x89\x0D' + _dword(log + ANIM_THIS)
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + ANIM_DEV)
                     + b'\xFF\x05' + _dword(log + N_ANIM)
                     + b'\x8B\xC1'
                     + b'\xC2\x04\x00')
        fs_file = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(fs_file + 8, _dword(FILE_SIZE))
        _patch_thunk(h, GFILE, b'\x89\x0D' + _dword(log + GFILE_THIS)
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + GFILE_NAME)
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + GFILE_NOLOAD)
                     + b'\xB8' + _dword(fs_file)                               # eax = the FsFile
                     + b'\x89\x41\x24'                                         # [this+0x24] = eax
                     + b'\xFF\x05' + _dword(log + N_GFILE)
                     + b'\x8B\xC1'
                     + b'\xC2\x08\x00')                                        # ret 8
        _patch_thunk(h, PLAY, b'\x89\x0D' + _dword(log + PLAY_THIS)
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + PLAY_FILE)
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + PLAY_SIZE)
                     + b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + PLAY_FLAGS)
                     + b'\xFF\x05' + _dword(log + N_PLAY)
                     + b'\xC2\x0C\x00')
        _patch_thunk(h, SND, b'\x89\x0D' + _dword(log + SND_THIS)
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + SND_ARG)
                     + b'\xFF\x05' + _dword(log + N_SND)
                     + b'\xC2\x04\x00')
        _patch_thunk(h, HEI, b'\xFF\x05' + _dword(log + N_HEI) + b'\xB8' + _dword(HEIGHT) + b'\xC3')
        _patch_thunk(h, WID, b'\xFF\x05' + _dword(log + N_WID) + b'\xB8' + _dword(WIDTH) + b'\xC3')
        _patch_thunk(h, RECT, b'\x89\x0D' + _dword(log + RECT_THIS)
                     + b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log + RECT_X)
                     + b'\x8B\x44\x24\x08' + b'\xA3' + _dword(log + RECT_Y)
                     + b'\x8B\x44\x24\x0C' + b'\xA3' + _dword(log + RECT_W)
                     + b'\x8B\x44\x24\x10' + b'\xA3' + _dword(log + RECT_H)
                     + b'\xFF\x05' + _dword(log + N_RECT)
                     + b'\xC2\x10\x00')
        _patch_thunk(h, GFDTOR, b'\x89\x0D' + _dword(log + GFDTOR_THIS)
                     + b'\xFF\x05' + _dword(log + N_GFDTOR)
                     + b'\xC7\x05' + _dword(log + SEQ) + _dword(1)             # order marker 1
                     + b'\xC3')
        _patch_import(h, STR_SLOT, STR_SYM,
                      b'\x89\x0D' + _dword(log + STRDTOR_ARG)
                      + b'\xFF\x05' + _dword(log + N_STRDTOR)
                      + b'\xC7\x05' + _dword(log + SEQ) + _dword(2)           # order marker 2
                      + b'\xC3')
        device = h.alloc(0x20, bytes(0x20))
        h.uc.mem_write(DEVICE_GLOBAL, _dword(device))
        self = h.alloc(0x300, bytes(0x300))
        name = (0, 0, 0, 0, 0, 0, 15)   # an empty MSVC string in SSO form
        heap_base = h.heap_ptr

        def setup():
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(self, b'\xA5' * 0x300)
            h.uc.mem_write(self + 8, _dword(SOUND))

        for mode in (0, 0x110000):
            h.heap_ptr = heap_base
            setup()
            diffs = h.compare(THIS, args=list(name) + [mode], regs={UC_X86_REG_ECX: self},
                              ret='eax', mem=False)
            if diffs:
                return ['mode %d: %s' % (mode, d) for d in diffs]
            h.heap_ptr = heap_base
            setup()
            res = h.call(THIS, args=list(name) + [mode], regs={UC_X86_REG_ECX: self})
            tag = 'mode %d' % mode
            if res['fault']:
                return ['%s: replacement faulted: %s' % (tag, res['fault'])]
            if res['esp'] != 0x24:
                return ['%s: stack delta %d, not 0x24' % (tag, res['esp'])]
            if res['eax'] != self:
                return ['%s: returned %08X, expected %08X' % (tag, res['eax'], self)]
            if _u32(h, self) != VTBL:
                return ['%s: vtable %08X' % (tag, _u32(h, self))]
            if _u32(h, log + N_MOVIE) != 1 or _u32(h, log + MOVIE_THIS) != self + 4 \
                    or _u32(h, log + MOVIE_DEV) != device:
                return ['%s: player %d on %08X with %08X'
                        % (tag, _u32(h, log + N_MOVIE), _u32(h, log + MOVIE_THIS), _u32(h, log + MOVIE_DEV))]
            if _u32(h, log + N_ANIM) != 1 or _u32(h, log + ANIM_THIS) != self + 0x1C \
                    or _u32(h, log + ANIM_DEV) != device:
                return ['%s: animation %d on %08X with %08X'
                        % (tag, _u32(h, log + N_ANIM), _u32(h, log + ANIM_THIS), _u32(h, log + ANIM_DEV))]
            if _u32(h, log + N_GFILE) != 1 or _u32(h, log + GFILE_NOLOAD) != 1:
                return ['%s: CGameFile ctor %d with no-load %d'
                        % (tag, _u32(h, log + N_GFILE), _u32(h, log + GFILE_NOLOAD))]
            if _u32(h, log + GFILE_NAME) != _u32(h, log + STRDTOR_ARG):
                return ['%s: opened %08X, destroyed %08X (not the same by-value string)'
                        % (tag, _u32(h, log + GFILE_NAME), _u32(h, log + STRDTOR_ARG))]
            if _u32(h, log + N_PLAY) != 1 or _u32(h, log + PLAY_THIS) != self + 4 \
                    or _u32(h, log + PLAY_FILE) != _u32(h, log + GFILE_THIS) \
                    or _u32(h, log + PLAY_SIZE) != FILE_SIZE or _u32(h, log + PLAY_FLAGS) != mode:
                return ['%s: play %d on %08X file %08X size %d flags %d'
                        % (tag, _u32(h, log + N_PLAY), _u32(h, log + PLAY_THIS),
                           _u32(h, log + PLAY_FILE), _u32(h, log + PLAY_SIZE), _u32(h, log + PLAY_FLAGS))]
            if _u32(h, log + N_SND) != 1 or _u32(h, log + SND_THIS) != self + 0x1C \
                    or _u32(h, log + SND_ARG) != SOUND:
                return ['%s: sound %d on %08X with %08X'
                        % (tag, _u32(h, log + N_SND), _u32(h, log + SND_THIS), _u32(h, log + SND_ARG))]
            if _u32(h, log + N_HEI) != 1 or _u32(h, log + N_WID) != 1:
                return ['%s: size calls %d / %d' % (tag, _u32(h, log + N_HEI), _u32(h, log + N_WID))]
            got = (_u32(h, log + RECT_THIS), _f32(h, log + RECT_X), _f32(h, log + RECT_Y),
                   _f32(h, log + RECT_W), _f32(h, log + RECT_H))
            if _u32(h, log + N_RECT) != 1 or got != (self + 0x1C, 0.0, 0.0, float(WIDTH), float(HEIGHT)):
                return ['%s: rectangle %d on %08X at (%r, %r) size (%r, %r)'
                        % (tag, _u32(h, log + N_RECT), _u32(h, log + RECT_THIS),
                           _f32(h, log + RECT_X), _f32(h, log + RECT_Y),
                           _f32(h, log + RECT_W), _f32(h, log + RECT_H))]
            if _u32(h, log + N_GFDTOR) != 1 or _u32(h, log + GFDTOR_THIS) != _u32(h, log + GFILE_THIS):
                return ['%s: CGameFile dtor %d on %08X (ctor on %08X)'
                        % (tag, _u32(h, log + N_GFDTOR), _u32(h, log + GFDTOR_THIS), _u32(h, log + GFILE_THIS))]
            if _u32(h, log + N_STRDTOR) != 1:
                return ['%s: string dtor %d times' % (tag, _u32(h, log + N_STRDTOR))]
            if _u32(h, log + SEQ) != 2:
                return ['%s: destruction order marker %d, expected the CGameFile first'
                        % (tag, _u32(h, log + SEQ))]
        h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
