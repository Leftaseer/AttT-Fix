"""CConsole::OpenLog (0x004425E0): despite the name and the "game.log" its caller passes, the function only
recomputes the game folder at +0x1638 from GetModuleFileNameA: the exe path cut after its last backslash plus a
trailing backslash.  A path without any backslash keeps the whole name."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

OPEN_LOG = 0x004425E0
GAME_FOLDER = 0x1638


def _put_string(h, addr, text=b''):
    """a VC8 string: allocator, inline buffer or heap pointer, size, capacity"""
    h.uc.mem_write(addr, bytes(4))
    if len(text) < 16:
        h.uc.mem_write(addr + 4, text + b'\0' * (16 - len(text)))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(text), 15))
    else:
        buffer = h.alloc(len(text) + 1, text + b'\0')
        h.uc.mem_write(addr + 4, struct.pack('<I', buffer))
        h.uc.mem_write(addr + 20, struct.pack('<II', len(text), len(text)))


def _get_string(h, addr):
    size, capacity = struct.unpack('<II', h.uc.mem_read(addr + 20, 8))
    pointer = addr + 4 if capacity < 16 else struct.unpack('<I', h.uc.mem_read(addr + 4, 4))[0]
    return bytes(h.uc.mem_read(pointer, size))


def _install_module_stubs(h, exe, log):
    def module_handle():
        log['handle'].append(h._arg(0))
        h._ret(0x00400000, 4)

    def module_file_name():
        module, buffer, size = h._arg(0), h._arg(1), h._arg(2)
        log['name'].append((module, size))
        text = exe[:size - 1]
        h.uc.mem_write(buffer, text + b'\0')
        h._ret(len(text), 12)

    saved = {}
    for attr, fn in (('crt_GetModuleHandleA', module_handle), ('crt_GetModuleFileNameA', module_file_name)):
        saved[attr] = getattr(h, attr, None)
        setattr(h, attr, fn)

    def restore():
        for attr, old in saved.items():
            if old is None:
                delattr(h, attr)
            else:
                setattr(h, attr, old)

    return restore


def test_open_log(h):
    for exe, want in ((b'D:\\Games\\ATThrone\\atthrone.exe', b'D:\\Games\\ATThrone\\'),
                      (b'atthrone.exe', b'atthrone.exe\\')):
        console = h.alloc(0x1700, bytes(0x1700))
        _put_string(h, console + GAME_FOLDER, b'C:\\stale\\')
        name = h.alloc(28, bytes(28))
        _put_string(h, name, b'game.log')
        log = {'handle': [], 'name': []}
        restore = _install_module_stubs(h, exe, log)
        try:
            diffs = h.compare(OPEN_LOG, args=[name], regs={UC_X86_REG_ECX: console}, ret=None)
            if diffs:
                return ['%r: %s' % (exe, d) for d in diffs]
            log['handle'].clear()
            log['name'].clear()
            res = h.call(OPEN_LOG, args=[name], regs={UC_X86_REG_ECX: console})
            if res['fault']:
                return ['%r: replacement faulted: %s' % (exe, res['fault'])]
            if log['handle'] != [0]:
                return ['%r: GetModuleHandleA called with %r' % (exe, log['handle'])]
            if len(log['name']) != 1 or log['name'][0][0] != 0x00400000 or log['name'][0][1] != 260:
                return ['%r: GetModuleFileNameA called with %r' % (exe, log['name'])]
            got = _get_string(h, console + GAME_FOLDER)
            if got != want:
                return ['%r: folder %r, want %r' % (exe, got, want)]
            if _get_string(h, name) != b'game.log':
                return ['%r: the log name was modified' % (exe,)]
        finally:
            restore()
    return None
