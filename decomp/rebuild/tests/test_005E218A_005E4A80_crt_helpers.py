"""Two CRT helpers:
0x005E218A (cdecl, four arguments, EAX result): a count above 0x7FFFFFFF stops the call with E_INVALIDARG
(0x80070057); otherwise the arguments go to 0x005B818A (a stdcall callee that pops its 16 bytes) with the
address of the fourth caller slot as its last argument - the stub logs what it sees, including the value the
pointer leads to, so a pointer to the wrong slot shows up.
0x005E4A80 (cdecl, no arguments): the initializer-table walk whose both bounds are the same address, so the
table is empty, nothing is called and no register or stack slot is touched."""
import struct

FORWARD = 0x005B818A
VF_FORWARD = 0x005E218A
VF_INITTERM = 0x005E4A80

L_COUNT = 0x00
L_EVENTS = 0x10
C_RET = 0x480
LOG_SIZE = 0x500

E_ARG0 = 1
E_COUNT = 2
E_ARG2 = 3
E_VALUE = 4

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


def _jump(h, address, target):
    _patch(h, address, b'\xE9' + _dword((target - (address + 5)) & 0xFFFFFFFF))


def _events(h, log):
    count = _u32(h, log + L_COUNT)
    return [struct.unpack('<II', h.uc.mem_read(log + L_EVENTS + 8 * i, 8)) for i in range(count)]


def _ev(log, code, load):
    return (b'\xFF\x05' + _dword(log + L_COUNT)                      # inc [count]
            + b'\xA1' + _dword(log + L_COUNT)                        # eax = [count]
            + b'\x48'                                                # dec eax
            + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)               # edx = events + 8*eax
            + b'\xC7\x82' + _dword(0) + _dword(code)                 # [edx] = code
            + load                                                   # eax = value
            + b'\x89\x82' + _dword(4))                               # [edx+4] = eax


def _restore(h, heap0):
    for address, code in saved.items():
        h.uc.mem_write(address, code)
        h.uc.ctl_remove_cache(address, address + len(code))
    saved.clear()
    h.heap_ptr = heap0


def test_005E218A(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        slot = h.alloc(4, _dword(0x55AA55AA))          # the caller's fourth argument
        fwd = _stub(h,
                    _ev(log, E_ARG0, b'\x8B\x44\x24\x04')            # arg0
                    + _ev(log, E_COUNT, b'\x8B\x44\x24\x08')         # count
                    + _ev(log, E_ARG2, b'\x8B\x44\x24\x0C')          # arg2
                    + _ev(log, E_VALUE, b'\x8B\x44\x24\x10\x8B\x00') # the slot the fourth pointer leads to
                    + b'\xA1' + _dword(log + C_RET)
                    + b'\xC2\x10\x00')
        _jump(h, FORWARD, fwd)

        def setup(ret):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + C_RET, _dword(ret))

        args = [0x11111111, 0, 0x22222222, slot]
        for count, ret in ((0, 0), (0x7FFFFFFF, 0x12345678), (0x80000000, 0), (0xFFFFFFFF, 0)):
            args[1] = count
            forwarded = count <= 0x7FFFFFFF
            want = [(E_ARG0, 0x11111111), (E_COUNT, count), (E_ARG2, 0x22222222), (E_VALUE, slot)] \
                if forwarded else []
            setup(ret)
            diffs = h.compare(VF_FORWARD, args=args)
            if diffs:
                return ['count %08X: %s' % (count, d) for d in diffs]
            setup(ret)
            res = h.call(VF_FORWARD, args=args)
            if res['fault']:
                return ['count %08X: replacement faulted: %s' % (count, res['fault'])]
            got = _events(h, log)
            if got != want:
                return ['count %08X: events %r, expected %r' % (count, got, want)]
            if res['eax'] != (ret if forwarded else 0x80070057):
                return ['count %08X: returned %08X' % (count, res['eax'])]
            h.heap_ptr = heap0
    finally:
        _restore(h, heap0)
    return None


def test_005E4A80(h):
    heap0 = h.heap_ptr
    try:
        diffs = h.compare(VF_INITTERM, ret=None)
        if diffs:
            return diffs
        res = h.call(VF_INITTERM)
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if (res['esp'], res['ebx'], res['esi'], res['edi'], res['ebp']) != (4, 0x0BB0BB0B, 0x05150515,
                                                                            0x0D150D15, 0x0EB00EB0):
            return ['registers or stack changed: %r' % (res,)]
    finally:
        _restore(h, heap0)
    return None
