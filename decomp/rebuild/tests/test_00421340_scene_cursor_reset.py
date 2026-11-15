"""0x00421340 (C2DScene vf, thiscall): the cursor point comes from the scene's +0x90 object (vtable slot 0x88).
Every entry of the +0x8C object's +0x66C dword table that is 0 while the cursor is outside the rectangle at +0xA0
(sized by the +0x80 object's +0x74/+0x78) resets the input (0x0046CF30 on the +0x38 object's +0x80, state +0xAC
set to 6); a clear +0xB4 makes every zero entry count.  Every two-byte entry of the +0x664 table with its second
byte set and its first 1 resets the input as well.  The scene then hands its +0x88 object (also when +0xB4 is clear
or the cursor is outside) or else its +0x84 object to the +0x90 object's vtable slot 0xE8 and returns its result.
The vtable slots and the input reset are stubs that log their calls."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX

THIS = 0x00421340
RESET = 0x0046CF30

SLOT_POS = 0x22
SLOT_NEXT = 0x3a
NEXT_RESULT = 0x5A5A5A5A

L_RESET = 0x00
L_RESET_THIS = 0x10
L_NEXT = 0x40
L_NEXT_PAIR = 0x44
LOG_SIZE = 0x90

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
    target = _stub(h, code)
    _patch(h, address, b'\xE9' + struct.pack('<i', target - (address + 5)))


def _return_stub(h, value):
    return _stub(h, b'\xB8' + _dword(value) + b'\xC3')


def _next_stub(log):
    return (b'\xFF\x05' + _dword(log + L_NEXT)                             # inc [calls]
            + b'\xA1' + _dword(log + L_NEXT)                               # mov eax, [calls]
            + b'\x48'                                                      # dec eax
            + b'\x8D\x14\xC5' + _dword(log + L_NEXT_PAIR)                  # lea edx, [eax*8 + pairs]
            + b'\x89\x0A'                                                  # mov [edx], ecx (this)
            + b'\x8B\x44\x24\x04'                                          # mov eax, [esp+4] (arg)
            + b'\x89\x42\x04'                                              # mov [edx+4], eax
            + b'\xB8' + _dword(NEXT_RESULT)                                # mov eax, result
            + b'\xC2\x04\x00')                                             # ret 4


def _reset_stub(log):
    return (b'\xFF\x05' + _dword(log + L_RESET)                            # inc [calls]
            + b'\xA1' + _dword(log + L_RESET)                              # mov eax, [calls]
            + b'\x48'                                                      # dec eax
            + b'\x89\x0C\x85' + _dword(log + L_RESET_THIS)                 # mov [eax*4 + this], ecx
            + b'\xC3')                                                     # ret


def _calls(h, log, count_slot, array_slot, width):
    n = _u32(h, log + count_slot)
    return [struct.unpack('<%dI' % (width // 4), h.uc.mem_read(log + array_slot + width * i, width))
            for i in range(n)]


def test_00421340(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        _patch_thunk(h, RESET, _reset_stub(log))
        point = h.alloc(8, bytes(8))
        vtable = h.alloc(0x100, bytes(0x100))
        owner = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(owner, _dword(vtable))
        h.uc.mem_write(vtable + SLOT_POS * 4, _dword(_return_stub(h, point)))
        h.uc.mem_write(vtable + SLOT_NEXT * 4, _dword(_stub(h, _next_stub(log))))
        s = h.alloc(0x100, bytes(0x100))
        bounds = h.alloc(0x80, bytes(0x80))
        scene = h.alloc(0x100, bytes(0x100))
        input_obj = h.alloc(0x40, bytes(0x40))
        tables = h.alloc(0x700, bytes(0x700))
        flags = h.alloc(16, bytes(16))
        pairs = h.alloc(16, bytes(16))
        obj88 = h.alloc(0x10, bytes(0x10))
        obj84 = h.alloc(0x10, bytes(0x10))
        h.uc.mem_write(s + 0x38, _dword(scene))
        h.uc.mem_write(s + 0x80, _dword(bounds))
        h.uc.mem_write(s + 0x84, _dword(obj84))
        h.uc.mem_write(s + 0x88, _dword(obj88))
        h.uc.mem_write(s + 0x8c, _dword(tables))
        h.uc.mem_write(s + 0x90, _dword(owner))
        h.uc.mem_write(scene + 0x80, _dword(input_obj))
        h.uc.mem_write(bounds + 0x74, struct.pack('<f', 100.0))
        h.uc.mem_write(bounds + 0x78, struct.pack('<f', 50.0))

        # name, x, y, border flag, flag table, pair table, resets, next argument
        cases = (
            ('no-border', 500.0, 500.0, 0, [], [], 0, obj88),
            ('inside', 50.0, 40.0, 1, [0, 1], [], 0, obj84),
            ('left', 5.0, 40.0, 1, [0, 1], [], 1, obj88),
            ('bottom', 50.0, 100.0, 1, [0, 0], [], 2, obj88),
            ('pairs', 50.0, 40.0, 1, [], [(1, 1), (1, 0), (2, 1), (0, 1)], 1, obj84),
            ('clear', 50.0, 40.0, 0, [0, 1], [(1, 1)], 2, obj88),
        )
        for name, x, y, border, flag_table, pair_table, resets, arg in cases:
            def setup():
                h.uc.mem_write(log, bytes(LOG_SIZE))
                h.uc.mem_write(point, struct.pack('<ff', x, y))
                h.uc.mem_write(tables, bytes(0x700))
                h.uc.mem_write(s + 0xa0, struct.pack('<ff', 10.0, 20.0))
                h.uc.mem_write(s + 0xb4, bytes([border]))
                h.uc.mem_write(scene + 0xac, bytes(4))
                h.uc.mem_write(flags, bytes(16))
                h.uc.mem_write(flags, b''.join(_dword(v) for v in flag_table))
                h.uc.mem_write(tables + 0x66c, _dword(flags))
                h.uc.mem_write(tables + 0x670, _dword(len(flag_table)))
                h.uc.mem_write(pairs, bytes(16))
                h.uc.mem_write(pairs, b''.join(struct.pack('<H', a | (b << 8)) for a, b in pair_table))
                h.uc.mem_write(tables + 0x660, _dword(pairs))
                h.uc.mem_write(tables + 0x664, _dword(len(pair_table)))

            setup()
            diffs = h.compare(THIS, regs={UC_X86_REG_ECX: s}, ret='eax')
            if diffs:
                return ['%s: %s' % (name, d) for d in diffs]
            setup()
            res = h.call(THIS, regs={UC_X86_REG_ECX: s})
            if res['fault']:
                return ['%s: replacement faulted: %s' % (name, res['fault'])]
            if res['eax'] != NEXT_RESULT:
                return ['%s: returned %08X' % (name, res['eax'])]
            got = _calls(h, log, L_RESET, L_RESET_THIS, 4)
            if got != [(input_obj,)] * resets:
                return ['%s: input reset %d times on %r' % (name, len(got), got)]
            got = _calls(h, log, L_NEXT, L_NEXT_PAIR, 8)
            if got != [(owner, arg)]:
                return ['%s: next called with %r' % (name, got)]
            state = _u32(h, scene + 0xac)
            if state != (6 if resets else 0):
                return ['%s: scene state is %d' % (name, state)]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
