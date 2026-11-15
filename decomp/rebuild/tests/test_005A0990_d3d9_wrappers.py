"""sub_005A0990 / sub_005A09B0: Direct3DCreate9 (export pointer at 0x8D128C, one argument) and D3DPERF_BeginEvent
(0x8D1290, color and name).  0x5A0870 resolves the d3d9.dll exports (AL=1 on success); when it fails, or the
export is missing, the wrappers return 0 and -1.  The resolver, its glue adapter and the two exports are stubs;
the input EAX is forwarded to the resolver untouched."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX

D3DCREATE = 0x005A0990
BEGIN_EVENT = 0x005A09B0
SET_MARKER = 0x005A09F0
SET_REGION = 0x005A0A10
SET_OPTIONS = 0x005A0A50
RESOLVER = 0x005A0870
EXPORT_D3DCREATE = 0x008D128C
EXPORT_BEGIN = 0x008D1290
EXPORT_MARKER = 0x008D1298
EXPORT_REGION = 0x008D129C
EXPORT_OPTIONS = 0x008D12A4

LOG_CALLS = 0x00
LOG_THIS = 0x04
LOG_ARG0 = 0x08
LOG_ARG1 = 0x0C
LOG_SIZE = 0x20

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


def _symbol(h, name):
    for key in (name, '_' + name):
        if key in h.symbols:
            return h.symbols[key]
    return None


def _patch_resolver(h, found):
    # 0x5A0870 leaves EAX = 0 on both failure paths, and the wrappers without an explicit mask return it
    code = b'\xB0\x01\xC3' if found else b'\x31\xC0\xC3'                          # mov al,1 / xor eax,eax; ret
    for address in {RESOLVER, _symbol(h, 'sub_005A0870')} - {None}:
        _patch(h, address, code)


def _patch_export(h, original_slot, stub):
    addresses = {original_slot, _symbol(h, 'd_%08X' % original_slot)} - {None}
    for address in addresses:
        _patch(h, address, _dword(stub))


def _run(h, entry, args, log, export, found, have_export, want, want_arg0, name):
    _patch_resolver(h, found)
    _patch_export(h, export, have_export)
    h.uc.mem_write(log, bytes(LOG_SIZE))
    diffs = h.compare(entry, args=args, regs={UC_X86_REG_EAX: 0xFEEDFACE})
    if diffs:
        return ['%s: %s' % (name, d) for d in diffs]
    h.uc.mem_write(log, bytes(LOG_SIZE))
    res = h.call(entry, args=args, regs={UC_X86_REG_EAX: 0xFEEDFACE})
    if res['fault']:
        return ['%s: replacement faulted: %s' % (name, res['fault'])]
    if res['eax'] != want:
        return ['%s: returned %08X, want %08X' % (name, res['eax'], want)]
    calls = _u32(h, log + LOG_CALLS)
    if not (found and have_export):
        if calls:
            return ['%s: export called %d times' % (name, calls)]
        return []
    if calls != 1:
        return ['%s: export called %d times' % (name, calls)]
    if _u32(h, log + LOG_ARG0) != want_arg0:
        return ['%s: first argument %08X' % (name, _u32(h, log + LOG_ARG0))]
    return []


def test_d3dcreate(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        create = _stub(h, b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_ARG0)   # mov eax, [esp+4]; mov [arg0], eax
                         + b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_ARG1)  # mov eax, [esp+4]; mov [arg1], eax
                         + b'\xFF\x05' + _dword(log + LOG_CALLS)             # inc [calls]
                         + b'\xB8\xDD\xDD\xDD\x0D'                          # mov eax, 0DDDDDDDh
                         + b'\xC2\x04\x00')                                  # ret 4
        for name, found, have_export, want in (('resolved', 1, create, 0x0DDDDDDD),
                                               ('export missing', 1, 0, 0),
                                               ('d3d9 missing', 0, create, 0)):
            errs = _run(h, D3DCREATE, [0x20], log, EXPORT_D3DCREATE, found, have_export, want, 0x20, name)
            if errs:
                return errs
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None


def test_d3dperf_begin(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        begin = _stub(h, b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_ARG0)    # mov eax, [esp+4]; mov [arg0], eax
                        + b'\x8B\x44\x24\x08\xA3' + _dword(log + LOG_ARG1)   # mov eax, [esp+8]; mov [arg1], eax
                        + b'\xFF\x05' + _dword(log + LOG_CALLS)              # inc [calls]
                        + b'\xB8\x2A\x00\x00\x00'                            # mov eax, 42
                        + b'\xC2\x08\x00')                                   # ret 8
        for name, found, have_export, want in (('resolved', 1, begin, 42),
                                               ('export missing', 1, 0, -1),
                                               ('d3d9 missing', 0, begin, -1)):
            errs = _run(h, BEGIN_EVENT, [0x00FF00FF, 0x20001000], log, EXPORT_BEGIN, found, have_export,
                        want & 0xFFFFFFFF, 0x00FF00FF, name)
            if errs:
                return errs
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None


def _export2(h, log, ret):
    return _stub(h, b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_ARG0)         # mov eax, [esp+4]; mov [arg0], eax
                    + b'\x8B\x44\x24\x08\xA3' + _dword(log + LOG_ARG1)       # mov eax, [esp+8]; mov [arg1], eax
                    + b'\xFF\x05' + _dword(log + LOG_CALLS)                  # inc [calls]
                    + b'\xB8' + _dword(ret)                                  # mov eax, ret
                    + b'\xC2\x08\x00')                                       # ret 8


def test_d3dperf_marker_region(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        for entry, export, tag in ((SET_MARKER, EXPORT_MARKER, 'marker'), (SET_REGION, EXPORT_REGION, 'region')):
            call = _export2(h, log, 7)
            for name, found, have_export, want in (('resolved', 1, call, 7),
                                                   ('export missing', 1, 0, 0),
                                                   ('d3d9 missing', 0, call, 0)):
                errs = _run(h, entry, [0x00112233, 0x20002000], log, export, found, have_export,
                            want, 0x00112233, '%s %s' % (tag, name))
                if errs:
                    return errs
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None


def test_d3dperf_set_options(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        set_options = _stub(h, b'\x8B\x44\x24\x04\xA3' + _dword(log + LOG_ARG0)  # mov eax, [esp+4]; mov [arg0], eax
                               + b'\xFF\x05' + _dword(log + LOG_CALLS)           # inc [calls]
                               + b'\xB8\x09\x00\x00\x00'                         # mov eax, 9
                               + b'\xC2\x04\x00')                                # ret 4
        for name, found, have_export, want in (('resolved', 1, set_options, 9),
                                               ('export missing', 1, 0, 0),
                                               ('d3d9 missing', 0, set_options, 0)):
            errs = _run(h, SET_OPTIONS, [0xFF], log, EXPORT_OPTIONS, found, have_export, want, 0xFF, name)
            if errs:
                return errs
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
