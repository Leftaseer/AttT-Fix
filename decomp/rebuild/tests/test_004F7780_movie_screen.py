"""0x004F7780 (cdecl, a by-value 28-byte string and two unsigned ints, 0x24 bytes of arguments left to the caller):
saves and mutes the Miles master volume twice, flags the application singleton, builds the movie element
(0x004F7430), fits its video (0x00430DC0 width, 0x00430DD0 height) into the screen (the second and the third
argument, min of height / video height and width / video width), places the animation (element +0x1C) centred
with the scaled size (0x004CA820), plays it with {27, 13, 32} and 100 (0x004F7640), releases the element (vtable
+0 with 1), restores the volume and destroys the by-value name.  Every callee and import is a recording stub."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x004F7780
VOL_GET_SLOT = 0x0060786C
VOL_GET_SYM = '__imp___AIL_digital_master_volume_level@4'
VOL_SET_SLOT = 0x00607868
VOL_SET_SYM = '__imp___AIL_set_digital_master_volume_level@8'
STR_DTOR_SLOT = 0x00607330
STR_DTOR_SYM = '__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ'
SINGLETON = 0x00421680
NEW = 0x005E3EAE
CTOR = 0x004F7430
WID = 0x00430DC0
HEI = 0x00430DD0
ENSURE = 0x00430CD0
RECT = 0x004CA820
PLAY = 0x004F7640
SAVED_VOLUME = 0x006CA494
DRIVER = 0x006CA498

DRIVER_PTR = 0xC0FFEE00
OLD_VOLUME = 0x3E800000              # 0.25f: stale preset of 0x6CA494, the live volume must replace it
CUR_VOLUME = 0x3F000000              # 0.5f
SETTING0, SETTING1, SETTING2 = 0x1B, 0x0D, 0x20
PLAY_TIME = 0x64
ELEMENT_SIZE = 0x34
VIDEO_W, VIDEO_H = 256, 512
NAME_W0, NAME_W1, NAME_SIZE, NAME_RES = 0x70696C63, 0x6976612E, 8, 15   # "clip.avi"

ORDER = 0x04                         # log+0 is _tag's call counter
GET_N, GET_DRV = 0x44, 0x48
SET_N, SET_DRV, SET_VOL = 0x50, 0x54, 0x64      # four calls: the driver array ends before the volumes
SING_N = 0x74
NEW_SIZE = 0x78
CTOR_N, CTOR_THIS, CTOR_W0, CTOR_W1, CTOR_SIZE, CTOR_MODE = 0x7C, 0x80, 0x84, 0x88, 0x8C, 0x90
ENS_N, ENS_THIS = 0x94, 0x98
WID_N, WID_THIS = 0x9C, 0xA0
HEI_N, HEI_THIS = 0xA4, 0xA8
RECT_N, RECT_THIS, RECT_X, RECT_Y, RECT_W, RECT_H = 0xAC, 0xB0, 0xB4, 0xB8, 0xBC, 0xC0
PLAY_THIS, PLAY_PTR, PLAY_S0, PLAY_S1, PLAY_S2, PLAY_WHEN = 0xC4, 0xC8, 0xCC, 0xD0, 0xD4, 0xD8
REL_THIS, REL_ARG = 0xDC, 0xE0
STR_ARG = 0xE4
LOG_SIZE = 0xF4

GET_OP, SET_OP, SING_OP, NEW_OP, CTOR_OP, WID_OP, HEI_OP, ENS_OP, RECT_OP, PLAY_OP, REL_OP, STR_OP = range(1, 13)

saved = {}


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


def _u32(h, address):
    return struct.unpack('<I', h.uc.mem_read(address, 4))[0]


def _f32(h, address):
    return struct.unpack('<f', h.uc.mem_read(address, 4))[0]


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)
    h.uc.ctl_remove_cache(address, address + len(data))


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, code):
    stub = _stub(h, code)
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    return stub


def _import(h, slot, symbol, code):
    stub = _stub(h, code)
    for address in (slot, h.symbols[symbol]):
        _patch(h, address, _dword(stub))


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _tag(log, op):
    return b'\x8B\x15' + _dword(log) + b'\xFF\x05' + _dword(log) + \
        b'\xC7\x04\x95' + _dword(log + ORDER) + _dword(op)


def _mov_eax(offset):
    return b'\x8B\x44\x24' + bytes([offset])


def _arg(offset, address):
    return _mov_eax(offset) + b'\xA3' + _dword(address)


def _ecx_store(address):
    return b'\x89\x0D' + _dword(address)


def _inc(address):
    return b'\xFF\x05' + _dword(address)


def _arr(offset, counter, address):
    return _mov_eax(offset) + b'\x8B\x15' + _dword(counter) + b'\x89\x04\x95' + _dword(address)


def _arr_ecx(counter, address):
    return b'\x8B\x15' + _dword(counter) + b'\x89\x0C\x95' + _dword(address)


def _name_args():
    return [0, NAME_W0, NAME_W1, 0, 0, NAME_SIZE, NAME_RES]


def _run(h, log, name, screen_w, screen_h):
    heap0 = h.heap_ptr
    try:
        singleton = h.alloc(0x240, bytes(0x240))
        element = h.alloc(0x40, bytes(0x40))
        volume_box = h.alloc(4, _dword(CUR_VOLUME))

        _hook(h, SINGLETON, _tag(log, SING_OP) + _inc(log + SING_N) + b'\xB8' + _dword(singleton) + b'\xC3')
        _hook(h, NEW, _tag(log, NEW_OP) + _arg(4, log + NEW_SIZE) + b'\xB8' + _dword(element) + b'\xC3')
        _hook(h, CTOR, _tag(log, CTOR_OP) + _inc(log + CTOR_N) + _ecx_store(log + CTOR_THIS) +
              _arg(8, log + CTOR_W0) + _arg(0xC, log + CTOR_W1) + _arg(0x18, log + CTOR_SIZE) +
              _arg(0x20, log + CTOR_MODE) + b'\x8B\xC1' + b'\xC2\x20\x00')
        _hook(h, WID, _tag(log, WID_OP) + _arr_ecx(log + WID_N, log + WID_THIS) + _inc(log + WID_N) +
              b'\xB8' + _dword(VIDEO_W) + b'\xC3')
        _hook(h, HEI, _tag(log, HEI_OP) + _arr_ecx(log + HEI_N, log + HEI_THIS) + _inc(log + HEI_N) +
              b'\xB8' + _dword(VIDEO_H) + b'\xC3')
        _hook(h, ENSURE, _tag(log, ENS_OP) + _arr_ecx(log + ENS_N, log + ENS_THIS) + _inc(log + ENS_N) + b'\xC3')
        _hook(h, RECT, _tag(log, RECT_OP) + _arr_ecx(log + RECT_N, log + RECT_THIS) +
              _arr(4, log + RECT_N, log + RECT_X) + _arr(8, log + RECT_N, log + RECT_Y) +
              _arr(0xC, log + RECT_N, log + RECT_W) + _arr(0x10, log + RECT_N, log + RECT_H) +
              _inc(log + RECT_N) + b'\xC2\x10\x00')
        _hook(h, PLAY, _tag(log, PLAY_OP) + _ecx_store(log + PLAY_THIS) + _mov_eax(4) +
              b'\xA3' + _dword(log + PLAY_PTR) + b'\x8B\x10' + b'\x89\x15' + _dword(log + PLAY_S0) +
              b'\x8B\x50\x04' + b'\x89\x15' + _dword(log + PLAY_S1) +
              b'\x8B\x50\x08' + b'\x89\x15' + _dword(log + PLAY_S2) +
              _arg(8, log + PLAY_WHEN) + b'\xC2\x08\x00')
        release_stub = _stub(h, _tag(log, REL_OP) + _ecx_store(log + REL_THIS) + _arg(4, log + REL_ARG) +
                             b'\xC2\x04\x00')
        vtable = h.alloc(4, _dword(release_stub))
        h.uc.mem_write(element, _dword(vtable))
        _import(h, VOL_GET_SLOT, VOL_GET_SYM,
                _tag(log, GET_OP) + _arr(4, log + GET_N, log + GET_DRV) + _inc(log + GET_N) +
                b'\xD9\x05' + _dword(volume_box) + b'\xC2\x04\x00')
        _import(h, VOL_SET_SLOT, VOL_SET_SYM,
                _tag(log, SET_OP) + _arr(4, log + SET_N, log + SET_DRV) + _arr(8, log + SET_N, log + SET_VOL) +
                _inc(log + SET_N) + b'\xC2\x08\x00')
        _import(h, STR_DTOR_SLOT, STR_DTOR_SYM,
                _tag(log, STR_OP) + _ecx_store(log + STR_ARG) + b'\xC3')
        h.uc.mem_write(DRIVER, _dword(DRIVER_PTR))
        h.uc.mem_write(SAVED_VOLUME, _dword(OLD_VOLUME))
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(singleton, bytes(0x240))
        h.uc.mem_write(element + 4, bytes(0x3C))

        diffs = h.compare(FN, args=name + [screen_w, screen_h], ret=None, mem=False)
        if diffs:
            return diffs, None
        h.uc.mem_write(DRIVER, _dword(DRIVER_PTR))
        h.uc.mem_write(SAVED_VOLUME, _dword(OLD_VOLUME))
        h.uc.mem_write(log, bytes(LOG_SIZE))
        h.uc.mem_write(singleton, bytes(0x240))
        h.uc.mem_write(element + 4, bytes(0x3C))
        result = h.call(FN, args=name + [screen_w, screen_h])
        if result['fault']:
            return [result['fault']], None
        got = {
            'esp': result['esp'],
            'order': [_u32(h, log + ORDER + 4 * i) for i in range(_u32(h, log))],
            'get_drv': [_u32(h, log + GET_DRV + 4 * i) for i in range(_u32(h, log + GET_N))],
            'set_drv': [_u32(h, log + SET_DRV + 4 * i) for i in range(_u32(h, log + SET_N))],
            'set_vol': [_u32(h, log + SET_VOL + 4 * i) for i in range(_u32(h, log + SET_N))],
            'singleton': _u32(h, log + SING_N),
            'singleton_flag': bytes(h.uc.mem_read(singleton + 0x228, 1)),
            'new_size': _u32(h, log + NEW_SIZE),
            'ctor_n': _u32(h, log + CTOR_N), 'ctor_this': _u32(h, log + CTOR_THIS),
            'ctor_w0': _u32(h, log + CTOR_W0), 'ctor_w1': _u32(h, log + CTOR_W1),
            'ctor_size': _u32(h, log + CTOR_SIZE), 'ctor_mode': _u32(h, log + CTOR_MODE),
            'wid_n': _u32(h, log + WID_N), 'wid_this': _u32(h, log + WID_THIS),
            'hei_n': _u32(h, log + HEI_N), 'hei_this': _u32(h, log + HEI_THIS),
            'ens_n': _u32(h, log + ENS_N), 'ens_this': _u32(h, log + ENS_THIS),
            'rect_n': _u32(h, log + RECT_N), 'rect_this': _u32(h, log + RECT_THIS),
            'rect': (_f32(h, log + RECT_X), _f32(h, log + RECT_Y),
                     _f32(h, log + RECT_W), _f32(h, log + RECT_H)),
            'play_this': _u32(h, log + PLAY_THIS), 'play_ptr': _u32(h, log + PLAY_PTR),
            'play_settings': (_u32(h, log + PLAY_S0), _u32(h, log + PLAY_S1), _u32(h, log + PLAY_S2)),
            'play_time': _u32(h, log + PLAY_WHEN),
            'rel_this': _u32(h, log + REL_THIS), 'rel_arg': _u32(h, log + REL_ARG),
            'str_arg': _u32(h, log + STR_ARG),
            'volume': _u32(h, SAVED_VOLUME),
            'driver': _u32(h, DRIVER),
            'element': h.uc.mem_read(element, 4),
        }
        return [], got
    finally:
        _restore(h)
        h.heap_ptr = heap0


def _check(h, got, screen_w, screen_h, problems):
    if got['esp'] != 0x4:
        problems.append('stack delta is %#x' % got['esp'])
    want = [GET_OP, GET_OP, SET_OP, SET_OP, SING_OP, NEW_OP, CTOR_OP, WID_OP, HEI_OP, ENS_OP, RECT_OP,
            PLAY_OP, REL_OP, SET_OP, SET_OP, STR_OP]
    if got['order'] != want:
        problems.append('call order is %s' % (got['order'],))
    if got['get_drv'] != [DRIVER_PTR, DRIVER_PTR]:
        problems.append('volume read on %s' % ([hex(x) for x in got['get_drv']],))
    if got['set_drv'] != [DRIVER_PTR] * 4:
        problems.append('volume set on %s' % ([hex(x) for x in got['set_drv']],))
    if got['set_vol'] != [0, 0, CUR_VOLUME, CUR_VOLUME]:
        problems.append('volume levels are %s' % ([hex(x) for x in got['set_vol']],))
    if got['volume'] != CUR_VOLUME or got['driver'] != DRIVER_PTR:
        problems.append('saved volume/driver left at %#x/%#x' % (got['volume'], got['driver']))
    if got['singleton'] != 1 or got['singleton_flag'] != b'\x01':
        problems.append('singleton %d flag %r' % (got['singleton'], got['singleton_flag']))
    if got['new_size'] != ELEMENT_SIZE:
        problems.append('element allocated with %#x bytes' % got['new_size'])
    element = None
    if got['ctor_n'] != 1 or got['ctor_mode'] != 0 or got['ctor_w0'] != NAME_W0 or \
            got['ctor_w1'] != NAME_W1 or got['ctor_size'] != NAME_SIZE:
        problems.append('element ctor %d with %#x/%#x size %d mode %d'
                        % (got['ctor_n'], got['ctor_w0'], got['ctor_w1'], got['ctor_size'], got['ctor_mode']))
    else:
        element = got['ctor_this']
    if got['wid_n'] != 1 or got['wid_this'] != got['ctor_this'] + 4 or \
            got['hei_n'] != 1 or got['hei_this'] != got['ctor_this'] + 4:
        problems.append('video size asked %d/%d on %#x/%#x'
                        % (got['wid_n'], got['hei_n'], got['wid_this'], got['hei_this']))
    if got['ens_n'] != 1 or got['ens_this'] != got['ctor_this'] + 4:
        problems.append('player prepared %d times on %#x' % (got['ens_n'], got['ens_this']))
    video_w, video_h = float(VIDEO_W), float(VIDEO_H)
    scale = min(screen_h / video_h, screen_w / video_w)
    sw, sh = int(scale * video_w), int(scale * video_h)
    want_rect = (float(int(screen_w - scale * video_w) / 2), float(int(screen_h - scale * video_h) / 2),
                 float(sw), float(sh))
    if got['rect_n'] != 1 or got['rect_this'] != got['ctor_this'] + 0x1C:
        problems.append('rectangle %d on %#x' % (got['rect_n'], got['rect_this']))
    if got['rect'] != want_rect:
        problems.append('rectangle is %s, want %s' % (got['rect'], want_rect))
    if got['play_this'] != got['ctor_this'] or got['play_settings'] != (SETTING0, SETTING1, SETTING2) or \
            got['play_time'] != PLAY_TIME:
        problems.append('play on %#x with %s for %#x'
                        % (got['play_this'], got['play_settings'], got['play_time']))
    if got['rel_this'] != got['ctor_this'] or got['rel_arg'] != 1:
        problems.append('release on %#x with %d' % (got['rel_this'], got['rel_arg']))
    if got['str_arg'] == 0 or h._str_get(got['str_arg']) != b'clip.avi':
        problems.append('name destroyed at %#x' % got['str_arg'])
    if element is None:
        problems.append('no element')


def test_movie_screen(h):
    log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
    name = _name_args()
    problems = []
    for screen_w, screen_h in ((800, 600), (1280, 720)):
        diffs, got = _run(h, log, name, screen_w, screen_h)
        if diffs:
            return ['%dx%d: %s' % (screen_w, screen_h, d) for d in diffs]
        _check(h, got, screen_w, screen_h, problems)
    return problems or None
