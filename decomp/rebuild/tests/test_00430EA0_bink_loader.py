"""0x430EA0 Bink memory-movie loader; Bink imports, file reading and object hooks are stubs."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

FN = 0x00430EA0
READ = 0x00458F80
ERROR = 0x00430C70
FINISH = 0x00430E10
NEW_ARRAY = 0x005E3B10
DELETE_ARRAY = 0x005E3EBA
SOUND_FLAG = 0x006C88CC
SOUND_SYSTEM = 0x12345678
STR_SLOT = 0x00607324
STR_SYM = '__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z'
saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(value):
    return struct.pack('<I', value & 0xFFFFFFFF)


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


def _import(h, slot, symbol, code):
    stub = _stub(h, code)
    for address in (slot, h.symbols[symbol]):
        _patch(h, address, _dword(stub))


def _arg(offset, log):
    return b'\x8B\x44\x24' + bytes([offset]) + b'\xA3' + _dword(log)


def _inc(log):
    return b'\xFF\x05' + _dword(log)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _fixture(h):
    log = h.alloc(0x70, bytes(0x70))
    buffer = h.alloc(0x200, bytes(0x200))
    old_buffer = h.alloc(0x80, bytes(0x80))
    file = h.alloc(0x40, bytes(0x40))
    release = _arg(4, log + 8) + _inc(log + 0x0c) + b'\xC2\x04\x00'
    release_stub = _stub(h, release)
    vtable = h.alloc(0x0c, bytes(0x0c))
    h.uc.mem_write(vtable + 8, _dword(release_stub))
    old_object = h.alloc(4, _dword(vtable))
    obj = h.alloc(0x20, bytes(0x20))

    _import(h, 0x00607714, '__imp___BinkClose@4',
            _arg(4, log) + _inc(log + 4) + b'\xC2\x04\x00')
    _import(h, 0x00607718, '__imp___BinkSetSoundSystem@8',
            _arg(4, log + 0x18) + _arg(8, log + 0x1c) + _inc(log + 0x20) +
            b'\xA1' + _dword(log + 0x60) + b'\xC2\x08\x00')
    for address in (0x0060771C, h.symbols['__imp___BinkOpenDirectSound@4']):
        _patch(h, address, _dword(SOUND_SYSTEM))
    _import(h, 0x00607734, '__imp___BinkOpen@8',
            _arg(4, log + 0x3c) + _arg(8, log + 0x40) + _inc(log + 0x44) +
            b'\xA1' + _dword(log + 0x64) + b'\xC2\x08\x00')
    _import(h, STR_SLOT, STR_SYM, _arg(4, log + 0x48) + _inc(log + 0x4c) +
            b'\x8B\xC1\xC2\x04\x00')
    _hook(h, DELETE_ARRAY, _arg(4, log + 0x10) + _inc(log + 0x14) + b'\xC3')
    _hook(h, NEW_ARRAY, _arg(4, log + 0x24) + _inc(log + 0x28) +
          b'\xB8' + _dword(buffer) + b'\xC3')
    _hook(h, READ, b'\x89\x0D' + _dword(log + 0x2c) + _arg(4, log + 0x30) +
          _arg(8, log + 0x34) + _inc(log + 0x38) + b'\xC2\x08\x00')
    _hook(h, ERROR, _inc(log + 0x50) + b'\xC2\x04\x00')
    _hook(h, FINISH, b'\x89\x0D' + _dword(log + 0x54) + _inc(log + 0x58) + b'\xC3')
    _patch(h, SOUND_FLAG, b'\0')
    return log, obj, file, buffer, old_buffer, old_object


def _check(h, fixture, initialized, sound_initialized, sound_result, open_handle, with_old_object=True):
    log, obj, file, buffer, old_buffer, old_object = fixture
    old_handle = 0x11223344
    h.uc.mem_write(obj, bytes(0x20))
    h.uc.mem_write(obj + 8, b'\x01' if initialized else b'\0')
    h.uc.mem_write(obj + 0x0c, _dword(old_handle))
    h.uc.mem_write(obj + 4, _dword(old_object if with_old_object else 0))
    h.uc.mem_write(obj + 0x10, _dword(old_buffer))
    h.uc.mem_write(SOUND_FLAG, bytes([sound_initialized]))
    h.uc.mem_write(log + 0x60, _dword(sound_result))
    h.uc.mem_write(log + 0x64, _dword(open_handle))
    args = (file, 0x200, 0x20)
    label = 'init %d sound %d/%d open %#x old %d' % (
        initialized, sound_initialized, sound_result, open_handle, with_old_object)
    diffs = h.compare(FN, args=args, regs={UC_X86_REG_ECX: obj}, ret=None, mem=False)
    if diffs:
        return ['%s: %s' % (label, d) for d in diffs]
    h.uc.mem_write(log, bytes(0x5c))
    result = h.call(FN, args=args, regs={UC_X86_REG_ECX: obj})
    if result['fault']:
        return ['%s: %s' % (label, result['fault'])]
    sound_calls = int(not sound_initialized)
    release_calls = int(initialized and with_old_object)
    expected = (
        (0, old_handle if initialized else 0, 'closed handle'), (4, int(initialized), 'close calls'),
        (8, old_object if release_calls else 0, 'released object'), (0x0c, release_calls, 'release calls'),
        (0x10, old_buffer if initialized else 0, 'deleted buffer'), (0x14, int(initialized), 'delete calls'),
        (0x18, SOUND_SYSTEM if sound_calls else 0, 'sound system'), (0x1c, 0, 'sound argument'),
        (0x20, sound_calls, 'sound calls'), (0x24, 0x200, 'allocation size'), (0x28, 1, 'allocation calls'),
        (0x2c, file, 'file object'), (0x30, buffer, 'read buffer'), (0x34, 0x200, 'read size'),
        (0x38, 1, 'read calls'), (0x3c, buffer, 'open buffer'), (0x40, 0x04100020, 'open flags'),
        (0x44, 1, 'open calls'), (0x48, 0x006091D0 if not open_handle else 0, 'error literal'),
        (0x4c, int(not open_handle), 'string calls'), (0x50, int(not open_handle), 'error calls'),
        (0x54, obj, 'finish object'), (0x58, 1, 'finish calls'),
    )
    problems = []
    for offset, want, name in expected:
        got = _u32(h, log + offset)
        if got != want:
            problems.append('%s: %s is %#x, want %#x' % (label, name, got, want))
    fields = ((0x0c, open_handle), (0x10, buffer), (0x14, 0x20))
    for offset, want in fields:
        got = _u32(h, obj + offset)
        if got != want:
            problems.append('%s: field +%#x is %#x, want %#x' % (label, offset, got, want))
    if (h.uc.mem_read(obj + 8, 1)[0]) != 1:
        problems.append('%s: initialized flag was not set' % label)
    want_sound = (sound_initialized or sound_result) and 1
    if h.uc.mem_read(SOUND_FLAG, 1)[0] != want_sound:
        problems.append('%s: sound flag is incorrect' % label)
    return problems


def test_bink_memory_loader(h):
    heap0 = h.heap_ptr
    try:
        fixture = _fixture(h)
        problems = []
        for case in (
            (True, False, True, 0x55667788, True),
            (False, True, True, 0, True),
            (True, False, False, 0x66778899, False),
        ):
            problems += _check(h, fixture, *case)
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
