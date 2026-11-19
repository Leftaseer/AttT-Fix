/* 0x0059DA50: turns an icon into a scratch surface and hands it to the device's cursor (DXUTmisc.cpp, the
 * assertion at line 0x32B names ".\\DXUTmisc.cpp").  GetIconInfo splits the icon into its mask and colour
 * bitmaps and GetObjectA on the mask gives the width and the height; without a colour bitmap the mask is a
 * double-height AND mask, so the row count is halved (the DIB still reads both halves).  A W*H*4-byte scratch
 * surface (format 0x15 = A8R8G8B8, pool 3) is created through the device's slot 0x90, a zeroed 40-byte
 * BITMAPINFOHEADER (biPlanes 1, biBitCount 0x20, biCompression 0) is set up, and a memory DC selects the mask
 * and GetDIBits it into the mask buffer; with a colour bitmap a second DC reads that one too.  The surface is
 * locked (slot 0x34, only its pBits is used), the mask rows are walked bottom-up while the colour rows are
 * walked from the bottom of the second half (mask-only) or from the equally indexed colour buffer: a zero
 * test pixel takes the other pixel made opaque (0xFF000000), a non-zero one is left transparent; with the
 * border flag the first 12 columns of the first 5 rows are additionally ORed with 0xFF808080 where the row's
 * bit pattern (0xCCC0, 0xA2A0, 0xA4A0, 0xA2A0, 0xCCC0; bit 15-column) is set.  After the unlock (slot 0x38)
 * the device's slot 0x28 gets the icon's hotspot and the surface.  The bitmaps, DCs, buffers and the surface
 * are released.  Returns S_OK or the failing HRESULT (E_FAIL 0x80004005 for a missing icon, bitmap, DC or
 * surface). */
/* @conv 0 */
#include "auto_pre.h"
DECOMP_C char d_0061FD10[];
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C void *__cdecl sub_005E3B10(unsigned int size);                              /* operator new[] */
DECOMP_C void __cdecl sub_005E3EBA(void *block);                                     /* operator delete[] */
DECOMP_C void *__cdecl sub_005E40BE(void *dst, int value, unsigned int size);        /* memset */
DECOMP_C int (__stdcall *imp_00607668)(void *icon, void *info) __asm__("__imp__GetIconInfo@8");
DECOMP_C int (__stdcall *imp_00607014)(void *obj, int size, void *out) __asm__("__imp__GetObjectA@12");
DECOMP_C void *(__stdcall *imp_00607604)(void *wnd) __asm__("__imp__GetDC@4");
DECOMP_C void *(__stdcall *imp_00607020)(void *hdc) __asm__("__imp__CreateCompatibleDC@4");
DECOMP_C void *(__stdcall *imp_00607024)(void *hdc, void *obj) __asm__("__imp__SelectObject@8");
DECOMP_C int (__stdcall *imp_00607010)(void *hdc, void *bmp, unsigned int start, unsigned int lines,
                                       void *bits, void *bmi, unsigned int usage)
    __asm__("__imp__GetDIBits@28");
DECOMP_C int (__stdcall *imp_00607608)(void *wnd, void *hdc) __asm__("__imp__ReleaseDC@8");
DECOMP_C int (__stdcall *imp_00607018)(void *hdc) __asm__("__imp__DeleteDC@4");
DECOMP_C int (__stdcall *imp_00607028)(void *obj) __asm__("__imp__DeleteObject@4");

typedef long (__stdcall *create_59DA50)(void *dev, unsigned int w, unsigned int h, unsigned int fmt,
                                        unsigned int pool, void **out, void *shared);
typedef long (__stdcall *lock_59DA50)(void *surf, void *locked, unsigned int a, unsigned int b);
typedef long (__stdcall *unlock_59DA50)(void *surf);
typedef long (__stdcall *release_59DA50)(void *surf);
typedef long (__stdcall *cursor_59DA50)(void *dev, unsigned int xhot, unsigned int yhot, void *surface);

struct bitmap_59DA50 { int type, width, height, width_bytes; short planes, bits; void *pixels; };
struct bmi_59DA50 {
    int size, width, height;
    short planes, bitcount;
    int compression, size_image, x_ppm, y_ppm, used, important;
};

#define VT_59DA50(o) (*(void ***)(o))

static unsigned int bytes_59DA50(int count)
{
    unsigned long long bytes = (unsigned long long)(unsigned int)count * 4;
    return bytes > 0xffffffffu ? 0xffffffffu : (unsigned int)bytes;
}

DECOMP(0059DA50)
long __cdecl f_0059DA50(void *dev, void *icon, int border)
{
    int info[5] = { 0, 0, 0, 0, 0 };
    struct bitmap_59DA50 bmp;
    struct bmi_59DA50 bmi;
    unsigned int locked[2] = { 0, 0 };
    void *hdc = 0, *memdc = 0, *memdc2 = 0, *oldsurf = 0, *surface = 0;
    void *mask_bits = 0, *color_bits = 0;
    long hr = 0x80004005;
    int mask_only, width, full_height, height, src_off;

    if (!imp_00607668(icon, info))
        goto done;
    if (!imp_00607014(info[3], 0x18, &bmp))
        goto done;
    width = bmp.width;
    full_height = bmp.height;
    mask_only = info[4] == 0;
    height = mask_only ? full_height >> 1 : full_height;

    hr = ((create_59DA50)VT_59DA50(dev)[0x90 / 4])(dev, (unsigned int)width, (unsigned int)height, 0x15, 3,
                                                   &surface, 0);
    sub_00458940(hr, d_0061FD10, 0x32b);
    if (hr < 0)
        goto done;

    mask_bits = sub_005E3B10(bytes_59DA50(full_height * width));
    sub_005E40BE(&bmi, 0, 0x2c);
    bmi.size = 0x28;
    bmi.width = width;
    bmi.height = full_height;
    bmi.planes = 1;
    bmi.bitcount = 0x20;
    bmi.compression = 0;

    hdc = imp_00607604(0);
    memdc = imp_00607020(hdc);
    if (!memdc) {
        hr = 0x80004005;
        goto done;
    }
    oldsurf = imp_00607024(memdc, info[3]);
    imp_00607010(memdc, info[3], 0, (unsigned int)full_height, mask_bits, &bmi, 0);
    imp_00607024(memdc, oldsurf);

    if (!mask_only) {
        color_bits = sub_005E3B10(bytes_59DA50(height * width));
        memdc2 = imp_00607020(hdc);
        if (!memdc2) {
            hr = 0x80004005;
            goto done;
        }
        imp_00607024(memdc2, info[4]);
        imp_00607010(memdc2, info[4], 0, (unsigned int)full_height, color_bits, &bmi, 0);
    }

    ((lock_59DA50)VT_59DA50(surface)[0x34 / 4])(surface, locked, 0, 0);
    src_off = (height * 4 - 4) * width;
    {
        char *src = (char *)mask_bits + src_off, *dst = (char *)locked[1];
        int color_index = (full_height - 1) * width;
        int row, col;

        for (row = 0; row < height; row++, src -= 4 * width, dst += 4 * width, color_index -= width) {
            for (col = 0; col < width; col++) {
                unsigned int maskpix = *(unsigned int *)(src + 4 * col);
                unsigned int other = mask_only
                    ? *(unsigned int *)((char *)mask_bits + 4 * (color_index + col))
                    : *(unsigned int *)((char *)color_bits + (src + 4 * col - (char *)mask_bits));
                unsigned int value = mask_only ? maskpix : other;
                unsigned int test = mask_only ? other : maskpix;

                *(unsigned int *)(dst + 4 * col) = test == 0 ? (value | 0xff000000) : 0;
                if (border && col < 12 && row < 5) {
                    static const unsigned short edge[5] = { 0xccc0, 0xa2a0, 0xa4a0, 0xa2a0, 0xccc0 };
                    if (edge[row] & (1 << (15 - col)))
                        *(unsigned int *)(dst + 4 * col) |= 0xff808080;
                }
            }
        }
    }
    ((unlock_59DA50)VT_59DA50(surface)[0x38 / 4])(surface);

    hr = ((cursor_59DA50)VT_59DA50(dev)[0x28 / 4])(dev, (unsigned int)info[1], (unsigned int)info[2],
                                                   surface);
    if (hr >= 0)
        hr = 0;

done:
    if (info[3])
        imp_00607028(info[3]);
    if (info[4])
        imp_00607028(info[4]);
    if (hdc)
        imp_00607608(0, hdc);
    if (memdc2)
        imp_00607018(memdc2);
    if (memdc)
        imp_00607018(memdc);
    if (color_bits)
        sub_005E3EBA(color_bits);
    if (mask_bits)
        sub_005E3EBA(mask_bits);
    if (surface)
        ((release_59DA50)VT_59DA50(surface)[0x08 / 4])(surface);
    return hr;
}
