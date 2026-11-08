"""CMainMenuScene vf15 (0x00472E20): base GUIScene call, script/GUI tables, camera defaults, state copy."""
import struct
from unicorn.x86_const import UC_X86_REG_ECX


def test_main_menu_scene_vf15(h):
    saved = []

    def stub(address, code):
        n = max(8, len(code) + 4)
        saved.append((address, bytes(h.uc.mem_read(address, n))))
        h.uc.mem_write(address, code + b'\x90' * (n - len(code)))
        h.uc.ctl_remove_cache(address, address + n)

    try:
        cam = h.alloc(0x244, bytes(0x244))
        counter = h.alloc(4, bytes(4))
        # inc dword ptr [counter]; ret
        called = h.alloc(8, b'\xff\x05' + struct.pack('<I', counter) + b'\xc3' + bytes(1))
        vt = h.alloc(8 * 4, bytes(8 * 4))
        h.uc.mem_write(vt + 0x18, struct.pack('<I', called))
        h.uc.mem_write(cam + 4, struct.pack('<I', vt))
        state = h.alloc(0x44, bytes(range(0x44)))
        scene = h.alloc(0x200, bytes(0x200))

        stub(0x00584190, b'\xc2\x0c\x00')                          # base vf15(this, name, args, modal)
        stub(0x004323E0, b'\x8b\xc1\xc2\x04\x00')                  # table ctor: return self
        stub(0x00437870, b'\x8b\x44\x24\x04\xc2\x08\x00')          # out table lookup: return out
        stub(0x0057B4E0, b'\x8b\x44\x24\x04\xc2\x08\x00')          # out table lookup: return out
        stub(0x004220A0, b'\x33\xc0\xc3')                          # table destructor: 0
        stub(0x00424E70, b'\xb8' + struct.pack('<I', cam) + b'\xc3')       # camera factory
        stub(0x00435550, b'\xb8' + struct.pack('<I', state) + b'\xc2\x04\x00')  # camera state

        diffs = h.compare(0x00472E20, args=[0, 0, 0], regs={UC_X86_REG_ECX: scene}, ret='eax')
        if diffs:
            return diffs
        # compare restores its snapshot; run the replacement once more for the state assertions
        res = h.call(0x00472E20, args=[0, 0, 0], regs={UC_X86_REG_ECX: scene})
        if res['fault']:
            return ['replacement faulted: %s' % res['fault']]
        if struct.unpack('<I', h.uc.mem_read(counter, 4))[0] != 1:
            return ['the camera vtbl+0x18 method did not run']
        for off, want in ((0x50, 0), (0x54, 0), (0x5c, 0), (0x60, 0), (0x64, 0), (0x214, 0)):
            if struct.unpack('<I', h.uc.mem_read(cam + off, 4))[0] != want:
                return ['camera +0x%X was not zeroed' % off]
        if h.uc.mem_read(cam + 0x70, 1) != b'\x01' or h.uc.mem_read(cam + 0x84, 1) != b'\x01':
            return ['camera flags +0x70/+0x84 were not set']
        if h.uc.mem_read(scene + 0xa8, 0x44) != bytes(range(0x44)):
            return ['camera state was not copied to scene +0xa8']
        return []
    finally:
        for address, data in saved:
            h.uc.mem_write(address, data)
            h.uc.ctl_remove_cache(address, address + len(data))
