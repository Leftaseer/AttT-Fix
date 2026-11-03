"""Exercise the numeric Lua SubHealth path on a tactical creature without a script table."""
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_FPCW


def test_tactical_health_contract(h):
    method = 0x005640F0
    unit = h.alloc(0x400)
    context = h.alloc(0x14, bytes(0x14))
    values = h.alloc(8)
    state = h.alloc(0x40, bytes(0x40))
    lua_global = h.to_rebuilt(0x008D122C)
    saved_global = bytes(h.uc.mem_read(lua_global, 4))
    saved_control = h.uc.reg_read(UC_X86_REG_FPCW)
    h.uc.mem_write(state + 8, struct.pack('<II', values + 8, values))
    h.uc.mem_write(lua_global, struct.pack('<I', state))
    args = [context]
    regs = {UC_X86_REG_ECX: unit}
    cases = (
        (80, 7.875, 73),
        (80, -7.875, 87),
        (80, 0.75, 80),
        (7, 7.0, 0),
        (7, 8.0, 0),
        (95, -10.0, 100),
    )
    differences = []
    try:
        for control in (0x027F, 0x007F):
            for initial, damage, expected in cases:
                h.uc.reg_write(UC_X86_REG_FPCW, control)
                h.uc.mem_write(values, struct.pack('<fI', damage, 3))  # Lua number TValue.
                before = bytearray(0x400)
                struct.pack_into('<I', before, 0x1E0, 100)
                struct.pack_into('<fI', before, 0x1E8, initial / 100, initial)
                before[0x3BC] = 1
                struct.pack_into('<IB', before, 0x3DC, 77, 1)
                h.uc.mem_write(unit, bytes(before))
                differences.extend(h.compare(method, args=args, regs=regs))

                after = bytearray(before)
                struct.pack_into('<fI', after, 0x1E8, expected / 100, expected)
                after[0x3BC] = int(expected != 0)
                struct.pack_into('<IB', after, 0x3DC, 0, 0)
                result = h.call(h.to_rebuilt(method), args=args, regs=regs)
                if (result['fault'] or result['eax'] != 0 or result['esp'] != 8 or
                        bytes(h.uc.mem_read(unit, len(after))) != bytes(after) or
                        h.uc.reg_read(UC_X86_REG_FPCW) != control):
                    actual = struct.unpack('<fI', h.uc.mem_read(unit + 0x1E8, 8))
                    differences.append(f'health {initial}, damage {damage}, x87 {control:#x}: '
                                       f'expected {expected}, observed {actual}, call {result}')
    finally:
        h.uc.mem_write(lua_global, saved_global)
        h.uc.reg_write(UC_X86_REG_FPCW, saved_control)
    return differences
