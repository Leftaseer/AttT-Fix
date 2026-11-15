"""0x42EEF0 (crash-dump dialog): GetLocalTime, the two formatted lines, MessageBoxA, SetActiveWindow and the dump
writer 0x0047C4F0 are stubbed; the dialog flag 0x006C88AD is set around the boxes."""
import struct

from unicorn.x86_const import UC_X86_REG_EBX, UC_X86_REG_EDI

DUMP_DIALOG = 0x0042EEF0
FORMAT = 0x0042EEC0
DUMP_WRITER = 0x0047C4F0
GET_LOCAL_TIME_SLOT = 0x00607154
GET_LOCAL_TIME_IMPORT = '__imp__GetLocalTime'
MESSAGE_BOX_SLOT = 0x006076C8
MESSAGE_BOX_IMPORT = '__imp__MessageBoxA'
SET_ACTIVE_SLOT = 0x006076AC
SET_ACTIVE_IMPORT = '__imp__SetActiveWindow'
OWNER = 0x006C889C
DIALOG_UP = 0x006C88AD

NAME_FORMAT = 0x00608D80
LINE_FORMAT = 0x00608CF4
LINE_OK = 0x00608D38
LINE_FAILED = 0x00608D1C
BOX_NOTICE_TEXT = 0x00608D54
BOX_NOTICE_CAPTION = 0x00608D74
BOX_ERROR_CAPTION = 0x00608CEC
OWNER_VALUE = 0x0001ABCD

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


def _record(log, counter):
    """edx = log + 32 * [counter]++, the 8-dword record the stubs fill"""
    return (b'\x8B\x15' + _dword(counter) + b'\xFF\x05' + _dword(counter) +
            b'\xC1\xE2\x05' + b'\x81\xC2' + _dword(log))


def _store(value, slot):
    return b'\x8B\x44\x24' + bytes([value]) + b'\x89\x82' + _dword(slot)


def _local_time_stub(h):
    code = (b'\x8B\x44\x24\x04' +                                     # mov eax,[esp+4]
            b'\xC7\x00' + _dword(0x000307E8) +                         # year 2024, month 3
            b'\xC7\x40\x04' + _dword(0x00110005) +                     # day of week 5, day 17
            b'\xC7\x40\x08' + _dword(0x002A0009) +                     # hour 9, minute 42
            b'\xC7\x40\x0C' + _dword(0x007B0021) +                     # second 33, milliseconds 123
            b'\xC2\x04\x00')
    return _stub(h, code)


def _format_stub(h, log, counter, values):
    """logs the dwords at the given stack slots; writes "O" and returns 1"""
    code = _record(log, counter) + b''.join(_store(v, 4 * i) for i, v in enumerate(values))
    code += b'\x8B\x44\x24\x04' + b'\xC6\x00\x4F' + b'\xC6\x40\x01\x00' + b'\xB8\x01\x00\x00\x00' + b'\xC3'
    return _stub(h, code)


def _message_box_stub(h, log, counter, full):
    """logs (hwnd, text or its first byte, caption, type, the dialog flag); returns 6"""
    code = _record(log, counter) + _store(4, 0)                        # hwnd
    if full:
        code += _store(8, 4)                                           # text pointer
    else:
        code += b'\x8B\x44\x24\x08' + b'\x0F\xB6\x00' + b'\x89\x42\x04'   # first text byte
    code += _store(0xC, 8) + _store(0x10, 0xC)                         # caption, type
    code += b'\x0F\xB6\x05' + _dword(DIALOG_UP) + b'\x89\x42\x10'      # the dialog flag
    code += b'\xB8\x06\x00\x00\x00' + b'\xC2\x10\x00'
    return _stub(h, code)


def _set_active_stub(h, log):
    return _stub(h, b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log) + b'\xC2\x04\x00')


def _dump_stub(h, log, result):
    """logs (mode, the first name byte); returns `result`"""
    code = (b'\x8B\x44\x24\x04' + b'\xA3' + _dword(log) +              # mode
            b'\x8B\x44\x24\x08' + b'\x0F\xB6\x00' + b'\xA3' + _dword(log + 4) +
            b'\xB8' + _dword(result) + b'\xC3')
    return _stub(h, code)


def _patch_import(h, slot, name, stub):
    _patch(h, slot, _dword(stub))
    _patch(h, h.symbols[name], _dword(stub))


def _install(h, fmt_values, msg_full, result):
    """installs the stubs for one case; returns the logs (fmt, msg, active, dump, counters)"""
    fmt_log, fmt_count = h.alloc(0x80, bytes(0x80)), h.alloc(4, bytes(4))
    msg_log, msg_count = h.alloc(0x80, bytes(0x80)), h.alloc(4, bytes(4))
    active_log, dump_log = h.alloc(4, bytes(4)), h.alloc(8, bytes(8))
    hooks = {'fmt': _format_stub(h, fmt_log, fmt_count, fmt_values),
             'msg': _message_box_stub(h, msg_log, msg_count, msg_full),
             'active': _set_active_stub(h, active_log),
             'dump': _dump_stub(h, dump_log, result)}
    _hook(h, FORMAT, hooks['fmt'])
    _hook(h, DUMP_WRITER, hooks['dump'])
    _patch_import(h, MESSAGE_BOX_SLOT, MESSAGE_BOX_IMPORT, hooks['msg'])
    _patch_import(h, SET_ACTIVE_SLOT, SET_ACTIVE_IMPORT, hooks['active'])
    return (fmt_log, fmt_count), (msg_log, msg_count), active_log, dump_log


def _clear(h, *pairs):
    for log, counter in pairs:
        h.uc.mem_write(log, bytes(0x80))
        h.uc.mem_write(counter, bytes(4))


def _run_case(h, result):
    """compare, then run once more and check the whole dialog; returns problems"""
    heap0 = h.heap_ptr
    local_time = _local_time_stub(h)
    _patch_import(h, GET_LOCAL_TIME_SLOT, GET_LOCAL_TIME_IMPORT, local_time)
    _patch(h, OWNER, _dword(OWNER_VALUE))
    _patch(h, DIALOG_UP, b'\x55')
    ok = result == 0
    fmt_values = (8, 0xC, 0x10)
    (fmt_log, fmt_count), (msg_log, msg_count), active_log, dump_log = _install(h, fmt_values, False, result)
    regs = {UC_X86_REG_EBX: 0x0B0B0B0B, UC_X86_REG_EDI: 0x0D0D0D0D}
    try:
        problems = []
        _clear(h, (fmt_log, fmt_count), (msg_log, msg_count))
        diffs = h.compare(DUMP_DIALOG, regs=regs, ret=None)
        if diffs:
            return ['%s' % '; '.join(diffs)]
        # the detailed run
        _clear(h, (fmt_log, fmt_count), (msg_log, msg_count))
        h.uc.mem_write(active_log, bytes(4))
        h.uc.mem_write(dump_log, bytes(8))
        swap = {'fmt': _format_stub(h, fmt_log, fmt_count, (4, 8, 0xC, 0x10, 0x14, 0x18, 0x1C, 0x20)),
                'msg': _message_box_stub(h, msg_log, msg_count, True)}
        _hook(h, FORMAT, swap['fmt'])
        _patch_import(h, MESSAGE_BOX_SLOT, MESSAGE_BOX_IMPORT, swap['msg'])
        res = h.call(DUMP_DIALOG, regs=regs)
        if res['fault']:
            return [res['fault']]
        calls = _u32(h, fmt_count)
        if calls != 2:
            problems.append('the formatter was called %d times' % calls)
        else:
            rec = [ _u32(h, fmt_log + 4 * i) for i in range(8) ]
            if rec[1:7] != [0x104, NAME_FORMAT, 17, 3, 2024, 9]:
                problems.append('the name line is (%s)' % ', '.join('%#x' % v for v in rec[1:7]))
            rec2 = [ _u32(h, fmt_log + 0x20 + 4 * i) for i in range(8) ]
            if rec2[1:4] != [0x400, LINE_FORMAT, LINE_OK if ok else LINE_FAILED]:
                problems.append('the result line is (%s)' % ', '.join('%#x' % v for v in rec2[1:4]))
        if _u32(h, dump_log) != 2:
            problems.append('the dump writer got mode %#x' % _u32(h, dump_log))
        if _u32(h, dump_log + 4) != ord('O'):
            problems.append('the dump name starts with %#x' % _u32(h, dump_log + 4))
        boxes = _u32(h, msg_count)
        if boxes != 2:
            problems.append('MessageBoxA was called %d times' % boxes)
        else:
            box1 = [_u32(h, msg_log + 4 * i) for i in range(5)]
            if box1[0] != OWNER_VALUE:
                problems.append('box 1 owns up to %#x' % box1[0])
            if box1[2] != BOX_NOTICE_CAPTION or box1[3] != 0x40:
                problems.append('box 1 is (%#x, %#x)' % (box1[2], box1[3]))
            if box1[4] != 1:
                problems.append('box 1 ran with the dialog flag %#x' % box1[4])
            box2 = [_u32(h, msg_log + 0x20 + 4 * i) for i in range(5)]
            if box1[1] != BOX_NOTICE_TEXT:
                problems.append('box 1 text is %#x' % box1[1])
            if box2[1] != rec2[0]:
                problems.append('box 2 text is %#x, not the result line %#x' % (box2[1], rec2[0]))
            if box2[2] != (BOX_ERROR_CAPTION if ok else BOX_NOTICE_CAPTION) or box2[3] != (0x40 if ok else 0x10):
                problems.append('box 2 is (%#x, %#x)' % (box2[2], box2[3]))
            if box2[4] != 1:
                problems.append('box 2 ran with the dialog flag %#x' % box2[4])
        if _u32(h, active_log) != OWNER_VALUE:
            problems.append('SetActiveWindow got %#x' % _u32(h, active_log))
        if h.uc.mem_read(DIALOG_UP, 1)[0] != 0:
            problems.append('the dialog flag was left at %#x' % h.uc.mem_read(DIALOG_UP, 1)[0])
        return problems or None
    finally:
        _restore(h)
        h.heap_ptr = heap0


def test_dump_dialog_ok(h):
    """the dump writer succeeds: "created" line, the error caption and 0x40"""
    return _run_case(h, 0)


def test_dump_dialog_failed(h):
    """the dump writer fails: the "no dump" line, the notice caption and 0x10"""
    return _run_case(h, 1)
