"""Check UI position updates and the native comparison byte in AH."""
import struct


def test_ui_position_flags(h):
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_FPCW

    obj = h.alloc(0x224, bytes(0x224))
    regs = {UC_X86_REG_ECX: obj, UC_X86_REG_EAX: 0x01234567}
    cases = [
        (0x00000000, 0x42, 0x42C80000, 0x43480000),  # default (100, 200)
        (0x80000000, 0x42, 0x42C80000, 0x43480000),
        (0x437A0000, 0x02, 0x437A0000, 0x42800000),  # (250, 64)
        (0xC0000000, 0x03, 0xC0000000, 0x42800000),
        (0x7FC00000, 0x47, 0x7FC00000, 0x42800000),
        (0x7F800001, 0x47, 0x7F800001, 0x42800000),
    ]

    def setup(harness):
        harness.uc.mem_write(obj + 0x74, struct.pack('<ffB', 12.0, 24.0, 0))
        harness.uc.mem_write(obj + 0x20c, struct.pack('<ff', 100.0, 200.0))
        harness.uc.mem_write(obj + 0x21c, struct.pack('<ff', 100.0, 200.0))
        harness.uc.mem_write(harness.to_rebuilt(0x006C8958), struct.pack('<ff', 768.0, 1366.0))

    saved_control = h.uc.reg_read(UC_X86_REG_FPCW)
    diffs = []
    try:
        for control in (0x27f, 0x7f):
            for x, ah, stored_x, stored_y in cases:
                for addresses, args, expected in (
                    ((0x004797D0, 0x00479D80), (x, 0x42800000), (stored_x, stored_y, 1)),
                    ((0x00479810, 0x00479DF0), (x,), (stored_x, 0x41C00000, 1)),
                    ((0x00479840, 0x00479E40), (x,), (0x41400000, stored_y if ah == 0x42 else x, 1)),
                ):
                    for address in addresses:
                        label = f'{address:08x} cw={control:x} coordinate={x:08x}'
                        h.uc.reg_write(UC_X86_REG_FPCW, control)
                        diffs.extend(f'{label}: {diff}' for diff in
                                     h.compare(address, args=args, regs=regs, setup=setup))
                        result = h.call(h.to_rebuilt(address), args=args, regs=regs)
                        observed = struct.unpack('<IIB', h.uc.mem_read(obj + 0x74, 9))
                        if result['fault'] or result['eax'] != (0x01230067 | (ah << 8)) or observed != expected:
                            diffs.append(f'{label}: expected position {expected} and AH={ah:02x}, got {observed}, {result}')
    finally:
        h.uc.reg_write(UC_X86_REG_FPCW, saved_control)
    return diffs
