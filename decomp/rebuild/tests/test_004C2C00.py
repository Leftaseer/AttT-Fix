"""Verify Sound3D volume changes through a mock DirectSound buffer."""
import struct

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_FPCW


def test_sound_volume(h):
    sound = h.alloc(0x68, bytes(0x68))
    vtable = h.alloc(0x40, bytes(0x40))
    buffer = h.alloc(4, struct.pack('<I', vtable))
    # Return the second stdcall argument, the volume requested of SetVolume.
    set_volume = h.alloc(8, bytes.fromhex('8b442408 c20800 90'))
    h.uc.mem_write(vtable + 0x3c, struct.pack('<I', set_volume))
    h.uc.mem_write(sound + 0x2c, struct.pack('<f', 1.0))
    h.uc.mem_write(sound + 0x5c, struct.pack('<I', buffer))
    regs = {UC_X86_REG_ECX: sound, UC_X86_REG_EAX: 0x01234567}
    cached = 0x3f000000
    cases = (
        (0, 0x3f800000, 0, 0x01234567, cached),
        (1, cached, 0, 0x123442cd, cached),
        (1, cached, 1, -2500, cached),
        (1, 0x3f800000, 0, 0, 0x3f800000),
        (1, 0x3d4ccccc, 0, -10000, 0x3d4ccccc),
        (1, 0x3d4ccccd, 0, -4750, 0x3d4ccccd),
        (1, 0x7fc00000, 0, 0x7fffec78, 0x7fc00000),
        (1, 0x7f800001, 0, 0x7fffec78, 0x7f800001),
        (1, 0x7f800000, 0, 0x7fffec78, 0x7f800000),
        (1, 0xff800000, 0, -10000, 0xff800000),
    )

    prepare = h.to_rebuilt(0x004C1F30)
    original = bytes(h.uc.mem_read(prepare, 6))
    saved_control = h.uc.reg_read(UC_X86_REG_FPCW)
    diffs = []
    try:
        # Isolate volume handling from the sound object's preparation routine.
        h.uc.mem_write(prepare, bytes.fromhex('b8cdab3412 c3'))
        h.uc.ctl_remove_cache(prepare, prepare + 16)
        for control in (0x27f, 0x7f):
            h.uc.reg_write(UC_X86_REG_FPCW, control)
            for active, bits, force, result, stored in cases:
                h.uc.mem_write(sound + 8, bytes([active]))
                h.uc.mem_write(sound + 0x64, struct.pack('<I', cached))
                label = f'cw={control:x} active={active} volume={bits:08x} force={force}'
                diffs.extend(f'{label}: {diff}' for diff in h.compare(0x004C2C00, (bits, force), regs))
                observed = h.call(h.to_rebuilt(0x004C2C00), (bits, force), regs)
                observed_bits, = struct.unpack('<I', h.uc.mem_read(sound + 0x64, 4))
                if observed['fault'] or observed['eax'] != result & 0xffffffff or observed_bits != stored:
                    diffs.append(f'{label}: got eax={observed["eax"]:08x}, stored={observed_bits:08x}')
    finally:
        h.uc.mem_write(prepare, original)
        h.uc.ctl_remove_cache(prepare, prepare + 16)
        h.uc.reg_write(UC_X86_REG_FPCW, saved_control)
    return diffs
