"""0x42EA10 (report a Win32 failure): GetLastError, FormatMessageA, wsprintfA, WriteErrorLog (0x42E930), MessageBoxA
and LocalFree are stubbed; their calls are observed through the log they fill and the error line they build."""
import struct

CAPTION = 0x00608C68                   # "Error"
FORMAT = 0x00608C70                    # "%s failed with error %d: %s"
REPORT = 0x0042EA10
WRITE_LOG = 0x0042E930
SLOT_GET_LAST_ERROR = 0x00607148
SLOT_FORMAT_MESSAGE = 0x0060714C
SLOT_LOCAL_FREE = 0x00607150
SLOT_WSPRINTF = 0x006076C4
SLOT_MESSAGE_BOX = 0x006076C8

saved = {}


def _u32(h, addr):
    return struct.unpack('<I', h.uc.mem_read(addr, 4))[0]


def _dword(addr):
    return struct.pack('<I', addr)


def _patch(h, address, data):
    saved.setdefault(address, bytes(h.uc.mem_read(address, len(data))))
    h.uc.mem_write(address, data)


def _restore(h):
    for address, data in saved.items():
        h.uc.mem_write(address, data)
        h.uc.ctl_remove_cache(address, address + len(data))
    saved.clear()


def _stub(h, code):
    p = h.alloc(len(code), code)
    h.uc.ctl_remove_cache(p, p + len(code))
    return p


def _hook(h, target, stub):
    _patch(h, target, b'\xE9' + struct.pack('<i', stub - (target + 5)))
    h.uc.ctl_remove_cache(target, target + 5)


def _log(offset):
    return b'\xA3' + _dword(offset)


def _get_last_error_stub(h, log):
    return _stub(h, b'\xB8' + _dword(0x42) + _log(log + 0x38) + b'\xC3')


def _format_message_stub(h, log, text):
    code = b'\x8B\x44\x24\x0C' + _log(log)              # dwMessageId
    code += b'\x8B\x44\x24\x04' + _log(log + 0x34)      # dwFlags
    code += b'\x8B\x44\x24\x14' + _log(log + 4)         # lpBuffer
    code += b'\x8B\x54\x24\x14' + b'\xC7\x02' + _dword(text)    # *lpBuffer = text
    code += b'\xB8' + _dword(1) + b'\xC2\x1C\x00'
    return _stub(h, code)


def _wsprintf_stub(h, log):
    code = b'\x8B\x44\x24\x04' + _log(log + 0x18)       # the line buffer
    code += b'\x8B\x44\x24\x08' + _log(log + 0x14)      # the format
    code += b'\x8B\x44\x24\x0C' + _log(log + 8)         # what
    code += b'\x8B\x44\x24\x10' + _log(log + 0xc)       # the error
    code += b'\x8B\x44\x24\x14' + _log(log + 0x10)      # the text
    code += b'\x8B\x54\x24\x04'                         # edx = the line buffer
    code += b'\xC7\x02' + b'line'
    code += b'\xC7\x42\x04' + _dword(0)
    code += b'\xB8' + _dword(4) + b'\xC3'
    return _stub(h, code)


def _message_box_stub(h, log):
    code = b'\x8B\x44\x24\x04' + _log(log + 0x20)
    code += b'\x8B\x44\x24\x08' + _log(log + 0x24)
    code += b'\x8B\x44\x24\x0C' + _log(log + 0x28)
    code += b'\x8B\x44\x24\x10' + _log(log + 0x2c)
    code += b'\xB8' + _dword(1) + b'\xC2\x10\x00'
    return _stub(h, code)


def _local_free_stub(h, log):
    return _stub(h, b'\x8B\x44\x24\x04' + _log(log + 0x30) + b'\x33\xC0' + b'\xC2\x04\x00')


def _write_log_stub(h, log):
    return _stub(h, b'\x8B\x44\x24\x04' + _log(log + 0x1c) + b'\xC3')


def _slot(h, address, name):
    """the original import table's slot and the rebuilt image's (new) one"""
    return [address, h.symbols[name]]


def test_error_report(h):
    heap0 = h.heap_ptr
    log = h.alloc(0x40, bytes(0x40))
    what = h.alloc(0x10, b'open failed\0\0\0\0\0')
    text = h.alloc(0x10, b'sys text\0\0\0\0\0\0\0\0')
    _hook(h, WRITE_LOG, _write_log_stub(h, log))
    for slot in _slot(h, SLOT_GET_LAST_ERROR, '__imp__GetLastError'):
        _patch(h, slot, _dword(_get_last_error_stub(h, log)))
    for slot in _slot(h, SLOT_FORMAT_MESSAGE, '__imp__FormatMessageA'):
        _patch(h, slot, _dword(_format_message_stub(h, log, text)))
    for slot in _slot(h, SLOT_WSPRINTF, '__imp__wsprintfA'):
        _patch(h, slot, _dword(_wsprintf_stub(h, log)))
    for slot in _slot(h, SLOT_MESSAGE_BOX, '__imp__MessageBoxA'):
        _patch(h, slot, _dword(_message_box_stub(h, log)))
    for slot in _slot(h, SLOT_LOCAL_FREE, '__imp__LocalFree'):
        _patch(h, slot, _dword(_local_free_stub(h, log)))
    try:
        problems = []
        h.uc.mem_write(log, bytes(0x40))
        diffs = h.compare(REPORT, args=[what], mem=False)
        if diffs:
            return ['report: %s' % '; '.join(diffs)]
        res = h.call(REPORT, args=[what])
        if res['fault']:
            return ['report: %s' % res['fault']]
        if _u32(h, log + 0x38) != 0x42:
            problems.append('GetLastError was not called (log %#x)' % _u32(h, log + 0x38))
        if _u32(h, log) != 0x42 or _u32(h, log + 0x34) != 0x1100:
            problems.append('FormatMessageA got (%#x, %#x)' % (_u32(h, log), _u32(h, log + 0x34)))
        if _u32(h, _u32(h, log + 4)) != text:
            problems.append('the formatted text pointer is not stored to the local')
        if _u32(h, log + 0x14) != h.to_rebuilt(FORMAT) or _u32(h, log + 8) != what \
                or _u32(h, log + 0xc) != 0x42 or _u32(h, log + 0x10) != text:
            problems.append('wsprintfA got (%#x, %#x, %#x, %#x)'
                            % (_u32(h, log + 0x14), _u32(h, log + 8), _u32(h, log + 0xc),
                               _u32(h, log + 0x10)))
        line = _u32(h, log + 0x18)
        if _u32(h, log + 0x1c) != line or _u32(h, log + 0x24) != line:
            problems.append('the line is logged, shown and boxed from different buffers')
        if struct.unpack('<I', h.uc.mem_read(line, 4))[0] != struct.unpack('<I', b'line')[0]:
            problems.append('the line buffer is not what wsprintfA wrote')
        if _u32(h, log + 0x20) or _u32(h, log + 0x28) != h.to_rebuilt(CAPTION) or _u32(h, log + 0x2c):
            problems.append('MessageBoxA got (%#x, %#x, %#x)'
                            % (_u32(h, log + 0x20), _u32(h, log + 0x28), _u32(h, log + 0x2c)))
        if _u32(h, log + 0x30) != text:
            problems.append('LocalFree got %#x' % _u32(h, log + 0x30))
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0
