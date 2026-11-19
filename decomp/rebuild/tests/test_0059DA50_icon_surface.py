"""0x0059DA50 (cdecl, args dev/icon/border, EAX result): an icon becomes a scratch surface and the device's cursor.
GetIconInfo (IAT 0x607668) fills the ICONINFO, GetObjectA (0x607014) on its mask bitmap (0x8A00) gives the width and
height; without a colour bitmap (0x8B00) the rows are halved.  The device's slot 0x90 creates a w*h*4 surface
(format 0x15, pool 3) and the assertion 0x00458940 gets the HRESULT with ".\\DXUTmisc.cpp" 0x61FD10 and line 0x32B.
new[] (0x005E3B10) takes the full-height buffer, memset zeroes the BITMAPINFOHEADER and fills it (0x28, 1, 0x20, 0),
GetDC (0x607604) then CreateCompatibleDC (0x607020) of it, SelectObject (0x607024) the mask, GetDIBits (0x607010)
with the full row count and the mask descriptor, SelectObject the old object back; a colour bitmap gets a second
buffer, DC (0x607020), selection and GetDIBits.  The surface is locked through slot 0x34 (only the pBits of the
D3DLOCKED_RECT is used), the mask rows are walked bottom-up with the colour rows from the second half of the buffer
(mask only) or the equally indexed colour buffer, the border flag ORs 0xFF808080 into the first 12 columns of the
first 5 rows by 0xCCC0/0xA2A0/0xA4A0/0xA2A0/0xCCC0 (bit 15-column), the unlock goes through slot 0x38 and the
device's slot 0x28 receives the hotspot and the surface.  Cleanup releases the bitmaps (0x607028), the DC
(0x607608/0x607018), the buffers (0x005E3EBA) and slot 0x08 of the surface.  Every import is a stub on both its
original and rebuilt slot; the device, the surface and the allocator are stubs that log what they see."""
import struct

VF = 0x0059DA50
ICON = 0x00001C0F
MASK = 0x00008A00
COLOR = 0x00008B00
HDC = 0x00007DC0
MEMDC = 0x00007000
MEMDC2 = 0x00007100
OLDSURF = 0x00000500
DEVFMT = 0x15
POOL = 3
ASSERT_FILE = 0x0061FD10
ASSERT_LINE = 0x32B
E_FAIL = 0x80004005

NEW = 0x005E3B10
FREE = 0x005E3EBA
ASSERT = 0x00458940

IAT = ((0x00607668, 'GetIconInfo', '__imp__GetIconInfo'),
       (0x00607014, 'GetObjectA', '__imp__GetObjectA'),
       (0x00607604, 'GetDC', '__imp__GetDC'),
       (0x00607020, 'CreateCompatibleDC', '__imp__CreateCompatibleDC'),
       (0x00607024, 'SelectObject', '__imp__SelectObject'),
       (0x00607010, 'GetDIBits', '__imp__GetDIBits'),
       (0x00607608, 'ReleaseDC', '__imp__ReleaseDC'),
       (0x00607018, 'DeleteDC', '__imp__DeleteDC'),
       (0x00607028, 'DeleteObject', '__imp__DeleteObject'))

L_COUNT = 0x00
L_EVENTS = 0x10
C_INFO = 0x480
C_OKICON = 0x494
C_BMP = 0x498
C_OKOBJ = 0x4B0
C_DC = 0x4B4
C_DCSTATE = 0x4B8
C_DC2 = 0x4BC
C_HR = 0x4C0
C_ALLOC = 0x4C4
C_WIDTH = 0x4C8
C_CURS = 0x4CC
LOG_SIZE = 0x500

E_ICON = 1
E_OBJ = 2
E_OBJCB = 3
E_DIB_HBM = 4
E_DIB_LINES = 5
E_DIB_BITS = 6
E_DIB_SIZE = 7
E_DIB_W = 8
E_DIB_H = 9
E_DIB_PB = 10
E_DIB_COMP = 11
E_DIB_IMG = 12
E_DIB_USED = 13
E_DIB_IMPORTANT = 14
E_CDCHDC = 15
E_SEL_HDC = 16
E_SEL_OBJ = 17
E_ALLOC = 18
E_LOCK = 19
E_UNLOCK = 20
E_CURS_DEV = 21
E_CURS_X = 22
E_CURS_Y = 23
E_CURS_SURF = 24
E_DOBJ = 25
E_RELEASEDC = 26
E_DELETEDC = 27
E_FREE = 28
E_RELEASE = 29
E_CREATE_DEV = 30
E_CREATE_W = 31
E_CREATE_H = 32
E_CREATE_FMT = 33
E_CREATE_POOL = 34
E_ASSERT_HR = 35
E_ASSERT_FILE = 36
E_ASSERT_LINE = 37

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


def test_0059DA50(h):
    heap0 = h.heap_ptr
    try:
        log = h.alloc(LOG_SIZE, bytes(LOG_SIZE))
        probe = h.alloc(0x800, bytes(0x800))
        dev = h.alloc(0x40, bytes(0x40))
        surf = h.alloc(0x40, bytes(0x40))
        pix = h.alloc(0x400, bytes(0x400))
        vt_surf = h.alloc(0x100, bytes(0x100))
        vt_dev = h.alloc(0x100, bytes(0x100))

        def ev(code, load):
            return (b'\xFF\x05' + _dword(log + L_COUNT)                      # inc [count]
                    + b'\xA1' + _dword(log + L_COUNT)                        # eax = [count]
                    + b'\x48'                                                # dec eax
                    + b'\x8D\x14\xC5' + _dword(log + L_EVENTS)               # edx = events + 8*eax
                    + b'\xC7\x82' + _dword(0) + _dword(code)                 # [edx] = code
                    + load                                                   # eax = value
                    + b'\x89\x82' + _dword(4))                               # [edx+4] = eax

        def stk(n):
            return b'\x8B\x44\x24' + bytes([n])

        def store(off):
            return b'\x89\x0A' if off == 0 else b'\x89\x4A' + bytes([off])   # [edx+off] = ecx

        info_write = b''.join(b'\x8B\x0D' + _dword(log + C_INFO + 4 * i) + store(4 * i) for i in range(5))
        bmp_write = b''.join(b'\x8B\x0D' + _dword(log + C_BMP + 4 * i) + store(4 * i) for i in range(6))

        get_icon = _stub(h, ev(E_ICON, stk(4))
                         + b'\xA1' + _dword(log + C_OKICON)                  # eax = the result
                         + b'\x85\xC0' + b'\x74' + bytes([4 + len(info_write)])   # nothing on failure
                         + b'\x8B\x54\x24\x08'                               # edx = pinfo
                         + info_write
                         + b'\xC2\x08\x00')
        get_object = _stub(h, ev(E_OBJ, stk(4)) + ev(E_OBJCB, stk(8))
                           + b'\xA1' + _dword(log + C_OKOBJ)
                           + b'\x85\xC0' + b'\x74' + bytes([4 + len(bmp_write)])
                           + b'\x8B\x54\x24\x0C'                             # edx = out
                           + bmp_write
                           + b'\xC2\x0C\x00')
        get_dc = _stub(h, b'\xA1' + _dword(log + C_DC) + b'\xC2\x04\x00')
        create_dc = _stub(h, ev(E_CDCHDC, stk(4))
                          + b'\xA1' + _dword(log + C_DCSTATE)                # eax = the settled value
                          + b'\x8B\x0D' + _dword(log + C_DC2)                # ecx = the next one
                          + b'\x89\x0D' + _dword(log + C_DCSTATE)
                          + b'\xC2\x04\x00')
        select = _stub(h, ev(E_SEL_HDC, stk(4)) + ev(E_SEL_OBJ, stk(8))
                       + b'\xB8' + _dword(OLDSURF) + b'\xC2\x08\x00')
        dib_events = (ev(E_DIB_HBM, stk(0x14)) + ev(E_DIB_LINES, stk(0x1C))
                      + ev(E_DIB_BITS, stk(0x20))
                      + ev(E_DIB_SIZE, b'\x8B\x44\x24\x24\x8B\x80' + _dword(0x00))
                      + ev(E_DIB_W, b'\x8B\x44\x24\x24\x8B\x80' + _dword(0x04))
                      + ev(E_DIB_H, b'\x8B\x44\x24\x24\x8B\x80' + _dword(0x08))
                      + ev(E_DIB_PB, b'\x8B\x44\x24\x24\x8B\x80' + _dword(0x0C))
                      + ev(E_DIB_COMP, b'\x8B\x44\x24\x24\x8B\x80' + _dword(0x10))
                      + ev(E_DIB_IMG, b'\x8B\x44\x24\x24\x8B\x80' + _dword(0x14))
                      + ev(E_DIB_USED, b'\x8B\x44\x24\x24\x8B\x80' + _dword(0x20))
                      + ev(E_DIB_IMPORTANT, b'\x8B\x44\x24\x24\x8B\x80' + _dword(0x24)))
        get_dibits = _stub(h,
                           b'\x53\x56\x57'
                           + dib_events
                           + b'\x8B\x5C\x24\x14'                              # ebx = hbm
                           + b'\x8B\x7C\x24\x20'                              # edi = bits
                           + b'\x8B\x4C\x24\x1C'                              # ecx = lines
                           + b'\x0F\xAF\x0D' + _dword(log + C_WIDTH)          # ecx *= width
                           + b'\x31\xD2'                                      # xor edx,edx
                           + b'\xF6\xC2\x03'                                  # test dl,3
                           + b'\x75\x04'                                      # jnz nonzero
                           + b'\x31\xC0'                                      # xor eax,eax
                           + b'\xEB\x0A'                                      # jmp store
                           + b'\x89\xD0'                                      # nonzero: eax = edx
                           + b'\x69\xC0' + _dword(0x9E3779B1)                 # imul eax,eax,K
                           + b'\x01\xD8'                                      # add eax,ebx
                           + b'\x89\x04\x97'                                  # store: [edi+edx*4] = eax
                           + b'\x42'                                          # inc edx
                           + b'\x3B\xD1'                                      # cmp edx,ecx
                           + b'\x72\xE5'                                      # jb loop
                           + b'\x5F\x5E\x5B'
                           + b'\xB8' + _dword(1) + b'\xC2\x1C\x00')
        release_dc = _stub(h, ev(E_RELEASEDC, stk(8)) + b'\xB8' + _dword(1) + b'\xC2\x08\x00')
        delete_dc = _stub(h, ev(E_DELETEDC, stk(4)) + b'\xB8' + _dword(1) + b'\xC2\x04\x00')
        delete_object = _stub(h, ev(E_DOBJ, stk(4)) + b'\xB8' + _dword(1) + b'\xC2\x04\x00')
        new_block = _stub(h, ev(E_ALLOC, stk(4))
                          + b'\x8B\x4C\x24\x04'                              # ecx = size
                          + b'\xA1' + _dword(log + C_ALLOC)                  # eax = the bump pointer
                          + b'\x01\x0D' + _dword(log + C_ALLOC)              # bump += size
                          + b'\xC3')
        free_block = _stub(h, ev(E_FREE, stk(4)) + b'\xC3')
        assert_stub = _stub(h, ev(E_ASSERT_HR, stk(4)) + ev(E_ASSERT_FILE, stk(8))
                            + ev(E_ASSERT_LINE, stk(12)) + b'\xC3')
        create = _stub(h, ev(E_CREATE_DEV, stk(4)) + ev(E_CREATE_W, stk(8))
                       + ev(E_CREATE_H, stk(12)) + ev(E_CREATE_FMT, stk(16))
                       + ev(E_CREATE_POOL, stk(20))
                       + b'\x8B\x54\x24\x18'                                 # edx = out
                       + b'\xA1' + _dword(log + C_HR)
                       + b'\x85\xC0'                                         # test eax,eax
                       + b'\x78\x06'                                         # js skip
                       + b'\xC7\x02' + _dword(surf)                          # *out = the surface
                       + b'\xC2\x1C\x00')
        cursor = _stub(h, ev(E_CURS_DEV, stk(4)) + ev(E_CURS_X, stk(8))
                       + ev(E_CURS_Y, stk(12)) + ev(E_CURS_SURF, stk(16))
                       + b'\xA1' + _dword(log + C_CURS) + b'\xC2\x10\x00')
        lock = _stub(h, ev(E_LOCK, stk(4))
                     + b'\x8B\x44\x24\x08'                               # eax = the D3DLOCKED_RECT
                     + b'\xC7\x00' + _dword(0x100)                       # pitch
                     + b'\xC7\x40\x04' + _dword(pix)                     # pBits
                     + b'\x31\xC0' + b'\xC2\x10\x00')
        unlock = _stub(h, ev(E_UNLOCK, stk(4)) + b'\x31\xC0' + b'\xC2\x04\x00')
        release = _stub(h, ev(E_RELEASE, stk(4)) + b'\xB8' + _dword(1) + b'\xC2\x04\x00')

        h.uc.mem_write(vt_surf + 0x08, _dword(release))
        h.uc.mem_write(vt_surf + 0x34, _dword(lock))
        h.uc.mem_write(vt_surf + 0x38, _dword(unlock))
        h.uc.mem_write(vt_dev + 0x28, _dword(cursor))
        h.uc.mem_write(vt_dev + 0x90, _dword(create))
        h.uc.mem_write(surf, _dword(vt_surf))
        h.uc.mem_write(dev, _dword(vt_dev))

        stubs = {'GetIconInfo': get_icon, 'GetObjectA': get_object, 'GetDC': get_dc,
                 'CreateCompatibleDC': create_dc, 'SelectObject': select, 'GetDIBits': get_dibits,
                 'ReleaseDC': release_dc, 'DeleteDC': delete_dc, 'DeleteObject': delete_object}
        for slot, name, symbol in IAT:
            for address in (slot, h.symbols[symbol]):
                _patch(h, address, _dword(stubs[name]))
        _jump(h, NEW, new_block)
        _jump(h, FREE, free_block)
        _jump(h, ASSERT, assert_stub)

        def setup(case):
            h.uc.mem_write(log, bytes(LOG_SIZE))
            h.uc.mem_write(log + C_INFO, struct.pack('<IIIII', 1, 7, 9, MASK, case['color']))
            h.uc.mem_write(log + C_OKICON, _dword(case['icon_ok']))
            h.uc.mem_write(log + C_BMP, struct.pack('<iiiiHHI', 0, case['w'], case['bmh'], case['w'] * 4, 1, 0x20,
                                                    0x1234))
            h.uc.mem_write(log + C_OKOBJ, _dword(case['obj_ok']))
            h.uc.mem_write(log + C_DC, _dword(HDC))
            h.uc.mem_write(log + C_DCSTATE, _dword(case['dc1']))
            h.uc.mem_write(log + C_DC2, _dword(case['dc2']))
            h.uc.mem_write(log + C_HR, _dword(case['hr']))
            h.uc.mem_write(log + C_ALLOC, _dword(probe))
            h.uc.mem_write(log + C_WIDTH, _dword(case['w']))
            h.uc.mem_write(log + C_CURS, _dword(case['cur']))
            h.uc.mem_write(probe, b'\xAA' * 0x800)
            h.uc.mem_write(pix, b'\xCC' * 0x400)

        def dib(hbm, lines, bits, w, hgt):
            return [(E_DIB_HBM, hbm), (E_DIB_LINES, lines), (E_DIB_BITS, bits), (E_DIB_SIZE, 0x28), (E_DIB_W, w),
                    (E_DIB_H, hgt), (E_DIB_PB, (0x20 << 16) | 1), (E_DIB_COMP, 0), (E_DIB_IMG, 0),
                    (E_DIB_USED, 0), (E_DIB_IMPORTANT, 0)]

        def expected(case):
            w, bmh, color = case['w'], case['bmh'], case['color']
            hh = (bmh >> 1) if color == 0 else bmh
            evs = [(E_ICON, ICON)]
            if not case['icon_ok']:
                return evs
            evs += [(E_OBJ, MASK), (E_OBJCB, 0x18)]
            tail = [(E_DOBJ, MASK)] + ([(E_DOBJ, color)] if color else [])
            if not case['obj_ok']:
                return evs + tail
            evs += [(E_CREATE_DEV, dev), (E_CREATE_W, w), (E_CREATE_H, hh), (E_CREATE_FMT, DEVFMT),
                    (E_CREATE_POOL, POOL), (E_ASSERT_HR, case['hr']), (E_ASSERT_FILE, ASSERT_FILE),
                    (E_ASSERT_LINE, ASSERT_LINE)]
            if case['hr'] & 0x80000000:
                return evs + tail
            maskbuf = probe
            colorbuf = probe + bmh * w * 4
            evs += [(E_ALLOC, bmh * w * 4), (E_CDCHDC, HDC)]
            if not case['dc1']:
                return evs + tail + [(E_RELEASEDC, HDC), (E_FREE, maskbuf), (E_RELEASE, surf)]
            evs += [(E_SEL_HDC, case['dc1']), (E_SEL_OBJ, MASK)] + dib(MASK, bmh, maskbuf, w, bmh)
            evs += [(E_SEL_HDC, case['dc1']), (E_SEL_OBJ, OLDSURF)]
            if color:
                evs += [(E_ALLOC, hh * w * 4), (E_CDCHDC, HDC)]
                if not case['dc2']:
                    return evs + tail + [(E_RELEASEDC, HDC), (E_DELETEDC, case['dc1']), (E_FREE, colorbuf),
                                         (E_FREE, maskbuf), (E_RELEASE, surf)]
                evs += [(E_SEL_HDC, case['dc2']), (E_SEL_OBJ, color)] + dib(color, bmh, colorbuf, w, bmh)
            evs += [(E_LOCK, surf), (E_UNLOCK, surf)]
            evs += [(E_CURS_DEV, dev), (E_CURS_X, 7), (E_CURS_Y, 9), (E_CURS_SURF, surf)]
            evs += tail + [(E_RELEASEDC, HDC)]
            if color and case['dc2']:
                evs += [(E_DELETEDC, case['dc2'])]
            evs += [(E_DELETEDC, case['dc1'])]
            if color:
                evs += [(E_FREE, colorbuf)]
            return evs + [(E_FREE, maskbuf), (E_RELEASE, surf)]

        base = dict(w=4, bmh=6, color=COLOR, border=1, icon_ok=1, obj_ok=1, hr=0, dc1=MEMDC, dc2=MEMDC2, cur=0)
        cases = [dict(base, name='color'),
                 dict(base, name='mono', w=5, bmh=10, color=0, border=0),
                 dict(base, name='mono-border', w=3, bmh=4, color=0, border=1),
                 dict(base, name='color-thin', w=1, bmh=2),
                 dict(base, name='create-fail', hr=0x887601C2),
                 dict(base, name='icon-fail', icon_ok=0),
                 dict(base, name='object-fail', obj_ok=0),
                 dict(base, name='dc-fail', dc1=0),
                 dict(base, name='second-dc-fail', dc2=0),
                 dict(base, name='cursor-fail', cur=0x8007000E),
                 dict(base, name='cursor-sfalse', cur=1)]
        for case in cases:
            if case['cur'] & 0x80000000:
                want = case['cur']
            elif case['cur']:
                want = 0
            elif not case['icon_ok'] or not case['obj_ok']:
                want = E_FAIL
            elif case['hr'] & 0x80000000:
                want = case['hr']
            elif not case['dc1'] or (case['color'] and not case['dc2']):
                want = E_FAIL
            else:
                want = 0
            setup(case)
            diffs = h.compare(VF, args=[dev, ICON, case['border']])
            if diffs:
                return ['%s: %s' % (case['name'], d) for d in diffs]
            setup(case)
            res = h.call(VF, args=[dev, ICON, case['border']])
            if res['fault']:
                return ['%s: replacement faulted: %s' % (case['name'], res['fault'])]
            got = _events(h, log)
            if got != expected(case):
                return ['%s: events %r, expected %r' % (case['name'], got, expected(case))]
            if res['eax'] != want:
                return ['%s: returned %08X, expected %08X' % (case['name'], res['eax'], want)]
            h.heap_ptr = heap0
    finally:
        for address, code in saved.items():
            h.uc.mem_write(address, code)
            h.uc.ctl_remove_cache(address, address + len(code))
        saved.clear()
        h.heap_ptr = heap0
    return None
