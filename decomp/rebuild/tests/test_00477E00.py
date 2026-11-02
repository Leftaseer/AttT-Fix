"""Tween-animation construction with valid device calls and shared declarations."""
import struct


def test_tween_constructor(h):
    from unicorn.x86_const import UC_X86_REG_ECX

    device_global = 0x006C8C10
    declarations = 0x006CA09C
    references = 0x006CA0A8
    saved = [(device_global, bytes(h.uc.mem_read(device_global, 4))),
             (declarations, bytes(h.uc.mem_read(declarations, 16)))]
    diffs = []
    try:
        # stdcall CreateVertexDeclaration(device, elements, out): count calls,
        # provide a synthetic declaration, return S_OK, and pop three arguments.
        target = h.alloc(32, bytes.fromhex(
            '8b542404 ff4204 8b4c240c c70178563412 31c0 c20c00'))
        table = h.alloc(0x15c, bytes(0x15c))
        h.uc.mem_write(table + 0x158, struct.pack('<I', target))
        for initial_references in (0, 1):
            device = h.alloc(8, struct.pack('<II', table, 0))
            obj = h.alloc(0x100, b'\xa5' * 0x100)
            h.uc.mem_write(device_global, struct.pack('<I', device))
            h.uc.mem_write(declarations, bytes(16))
            h.uc.mem_write(references, struct.pack('<I', initial_references))
            diffs += h.compare(0x00477E00, regs={UC_X86_REG_ECX: obj}, ret='eax')
            result = h.call(0x00477E00, regs={UC_X86_REG_ECX: obj})
            if result['fault'] or result['eax'] != obj or result['esp'] != 4:
                diffs.append('constructor did not return this normally: %r' % result)
            count = struct.unpack('<I', h.uc.mem_read(device + 4, 4))[0]
            expected = 0 if initial_references else 2
            if count != expected:
                diffs.append('device calls: %d, expected %d' % (count, expected))
            count = struct.unpack('<I', h.uc.mem_read(references, 4))[0]
            if count != initial_references + 1:
                diffs.append('shared declaration reference was not acquired')
    finally:
        for address, data in saved:
            h.uc.mem_write(address, data)
    return diffs
