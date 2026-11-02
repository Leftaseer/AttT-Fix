"""Forest loading with an initialized filesystem and bounded file entries."""
import struct


def test_forest_loader(h):
    from unicorn.x86_const import UC_X86_REG_ECX
    saved_globals = bytes(h.uc.mem_read(0x006C8DE0, 8))
    saved = []
    diffs = []
    try:
        terrain = h.alloc(16, bytes(16))
        manager = h.alloc(0xb0, bytes(0xb0))
        definition = h.alloc(0x40, bytes(0x40))
        h.uc.mem_write(definition + 0x20, bytes(28))
        h._str_set(definition + 0x20, b'test/forest/world/')
        filesystem = h.alloc(0x100, bytes(0x100))
        opened = h.alloc(4, bytes(4))
        loaded = h.alloc(4, bytes(4))
        getter = lambda p: b'\xb8' + struct.pack('<I', p) + b'\xc3'
        stubs = [(0x00433620, getter(terrain)), (0x00518B10, getter(manager)),
                 (0x00427990, getter(definition)),
                 (0x00459010, b'\xc3'),
                 (0x0055A830, b'\xff\x05' + struct.pack('<I', loaded) + bytes.fromhex('c20400'))]
        for address, code in stubs:
            saved.append((address, bytes(h.uc.mem_read(address, max(5, len(code))))))
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.append((0x00459050, bytes(h.uc.mem_read(0x00459050, 13))))
        for count, file_state in ((0, 0), (2, 0), (2, 1)):
            # The normal engine contract: the filesystem already exists. This
            # avoids testing its unrelated lazy constructor's empty allocator.
            h.uc.mem_write(0x006C8DE0, struct.pack('<II', 1, filesystem))
            h.uc.mem_write(opened, bytes(4))
            h.uc.mem_write(loaded, bytes(4))
            entries = h.alloc(max(0x54, count * 0x54), bytes(max(0x54, count * 0x54)))
            for i in range(count):
                h._str_set(entries + i * 0x54, ('tree%d' % i).encode())
            h.uc.mem_write(manager + 0xa0, struct.pack('<II', entries, entries + count * 0x54))
            obj = h.alloc(0x4270, bytes(0x4270))
            h._str_set(obj + 0x4250, b'')
            # File access is a stub: record the visit and select either branch.
            code = bytes([0xc6, 0x41, 0x2c, file_state]) + b'\xff\x05' + struct.pack('<I', opened) + bytes.fromhex('c20800')
            h.uc.mem_write(0x00459050, code)
            h.uc.ctl_remove_cache(0x00459050, 0x00459050 + len(code))
            diffs += h.compare(0x0055B850, regs={UC_X86_REG_ECX: obj}, ret=None)
            result = h.call(0x0055B850, regs={UC_X86_REG_ECX: obj})
            if result['fault']:
                diffs.append('bounded forest loader faulted: %s' % result['fault'])
            if struct.unpack('<II', h.uc.mem_read(obj + 0x4248, 8)) != (terrain, manager):
                diffs.append('forest loader did not retain its terrain and manager')
            if struct.unpack('<I', h.uc.mem_read(opened, 4))[0] != count:
                diffs.append('forest loader visited the wrong number of files')
            if struct.unpack('<I', h.uc.mem_read(loaded, 4))[0] != (0 if file_state else count):
                diffs.append('forest loader took the wrong file-state branch')
            if struct.unpack('<I', h.uc.mem_read(0x006C8DE0, 4))[0] != 1:
                diffs.append('filesystem reference count was not restored')
    finally:
        for address, data in saved:
            h.uc.mem_write(address, data)
            h.uc.ctl_remove_cache(address, address + len(data))
        h.uc.mem_write(0x006C8DE0, saved_globals)
    return diffs
