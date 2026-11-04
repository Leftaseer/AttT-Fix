"""Normal-input contracts for fuzz-only divide, pointer and instruction-budget differences."""
import struct


def test_nonempty_random_selection(h):
    from unicorn.x86_const import UC_X86_REG_ECX
    diffs = []
    for address, offset in ((0x004E0E50, 0x2c), (0x004E0E90, 0x3c)):
        for count in (1, 2, 8):
            values = list(range(100, 100 + count))
            data = h.alloc(count * 4, struct.pack('<%dI' % count, *values))
            obj = h.alloc(0x50, bytes(0x50))
            h.uc.mem_write(obj + offset, struct.pack('<II', data, data + count * 4))
            regs = {UC_X86_REG_ECX: obj}
            diffs += h.compare(address, regs=regs)
            result = h.call(address, regs=regs)
            if result['fault'] or result['eax'] not in values:
                diffs.append('nonempty random selection failed: %r' % result)
    return diffs


def test_integer_power_contract(h):
    diffs = []
    for base in (-2, -1, 0, 1, 2, 7):
        for exponent in (0, 1, 2, 3, -1, -2):
            if base == 0 and exponent < 0:
                continue  # Original integer reciprocal divides by zero: outside this normal contract.
            args = [base, exponent]
            diffs += h.compare(0x00555E80, args=args)
            result = h.call(0x00555E80, args=args)
            if result['fault']:
                diffs.append('integer power faulted for %r: %s' % (args, result['fault']))
    return diffs


def test_noop_troop_iteration(h):
    from unicorn.x86_const import UC_X86_REG_ECX
    diffs = []
    for count in (0, 1, 4):
        units = [h.alloc(16, bytes(16)) for _ in range(count)]
        data = h.alloc(max(4, count * 4), struct.pack('<%dI' % count, *units) if count else bytes(4))
        obj = h.alloc(0x60, bytes(0x60))
        h.uc.mem_write(obj + 0x58, struct.pack('<II', data, count))
        regs = {UC_X86_REG_ECX: obj}
        diffs += h.compare(0x0051DB90, regs=regs, ret=None)
        result = h.call(0x0051DB90, regs=regs)
        if result['fault']:
            diffs.append('valid troop iteration faulted: %s' % result['fault'])
    return diffs


def test_container_lookup_contract(h):
    from unicorn.x86_const import UC_X86_REG_ECX
    address = 0x005874D0
    saved = bytes(h.uc.mem_read(address, 5))
    diffs = []
    try:
        h.uc.mem_write(address, bytes.fromhex('d9ee c3'))  # float getter -> +0.0
        h.uc.ctl_remove_cache(address, address + 5)
        setter = h.alloc(16, bytes.fromhex('ff4104 c20800'))
        getter = h.alloc(16, bytes.fromhex('b878563412 c3'))
        table = h.alloc(0x80, bytes(0x80))
        h.uc.mem_write(table + 0x78, struct.pack('<I', setter))
        h.uc.mem_write(table + 0x4c, struct.pack('<I', getter))
        for count in (0, 1, 2):
            first = h.alloc(8, struct.pack('<II', table, 0))
            second = h.alloc(8, struct.pack('<II', table, 0))
            next_node = h.alloc(12, struct.pack('<III', 0, 0, second))
            node = h.alloc(12, struct.pack('<III', next_node, 0, first))
            holder = h.alloc(4, struct.pack('<I', node))
            obj = h.alloc(0x48, bytes(0x48))
            h.uc.mem_write(obj + 0x40, struct.pack('<II', holder, count))
            regs = {UC_X86_REG_ECX: obj}
            diffs += h.compare(0x0047BF50, regs=regs)
            result = h.call(0x0047BF50, regs=regs)
            expected = 0x12345678 if count > 1 else holder
            if result['fault'] or result['eax'] != expected:
                diffs.append('valid container lookup failed: %r' % result)
    finally:
        h.uc.mem_write(address, saved)
        h.uc.ctl_remove_cache(address, address + len(saved))
    return diffs


def test_bounded_position_setter(h):
    from unicorn.x86_const import UC_X86_REG_ECX
    address = 0x00552E60
    saved = bytes(h.uc.mem_read(address, 5))
    diffs = []
    try:
        # Isolate the setter from the unrelated update/logging routine.
        h.uc.mem_write(address, b'\xc3')
        h.uc.ctl_remove_cache(address, address + 5)
        for count in (0, 3, 16):
            for values in ((0.0, 0.0, 0.0), (1.0, -2.0, 3.0)):
                data = h.alloc(max(4, count * 4), bytes(max(4, count * 4)))
                obj = h.alloc(0x130, bytes(0x130))
                h.uc.mem_write(obj + 0x68, struct.pack('<II', data, data + count * 4))
                position = h.alloc(12, struct.pack('<3f', *values))
                regs = {UC_X86_REG_ECX: obj}
                diffs += h.compare(0x00553260, args=[position], regs=regs, ret=None)
                result = h.call(0x00553260, args=[position], regs=regs)
                if result['fault'] or bytes(h.uc.mem_read(obj + 0x120, 12)) != struct.pack('<3f', *values):
                    diffs.append('bounded position setter failed: %r' % result)
    finally:
        h.uc.mem_write(address, saved)
        h.uc.ctl_remove_cache(address, address + len(saved))
    return diffs


def test_initialized_forest_scalar_setters(h):
    from unicorn.x86_const import UC_X86_REG_ECX
    diffs = []
    for count in (0, 3, 16):
        data = h.alloc(count * 4, bytes(count * 4)) if count else 0
        for address, offset, value, ret in [
            (0x005531A0, 0x12c, struct.pack('<f', 1.25), None),
            (0x005531A0, 0x12c, struct.pack('<I', 0x7fc00000), None),
            (0x00553320, 0x11d, b'\x01', 'eax'),
        ]:
            obj = h.alloc(0x130, bytes(0x130))
            h.uc.mem_write(obj + 0x11c, b'\x01')
            h.uc.mem_write(obj + 0x68, struct.pack('<II', data, data + count * 4))
            args = [int.from_bytes(value, 'little')]
            regs = {UC_X86_REG_ECX: obj}
            diffs += h.compare(address, args=args, regs=regs, ret=ret)
            result = h.call(h.to_rebuilt(address), args=args, regs=regs)
            if result['fault'] or h.uc.mem_read(obj + offset, len(value)) != value:
                diffs.append('%08X failed for %d forest entries: %r' % (address, count, result))
    return diffs
