/* 0x004E0000: a texture node's load from its DDS file (name +8): the mip levels to skip (once: 0x00427990's +0x64,
 * 0x006CA6F4) are skipped unless the node keeps all (+0x64); the file (0x00459290 reader, "cannot open file - '<name>'"
 * TextureNode.cpp:138) gives the 0x7C-byte header after the magic and the format (0x004DFDA0 from the pixel format:
 * bytes per pixel and whether it is block-compressed, "unknown file format - '<name>'" :155 when none, +0x74); with
 * skipping the size (+0x68 / +0x6C) is divided by twice the skip and the levels (+0x70) reduced, the skipped levels'
 * data passed over; a default-pool texture (+0x60) and a system-memory one are created, each level read into the
 * latter (LockRect NOSYSLOCK; blocks at least 8 bytes) and the former updated from it (UpdateTexture); +0x68 / +0x6C
 * end as the file's full width and height. +0x78 / +0x7C cleared */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C void __thiscall sub_00459290(void *self, void *name, int a);
DECOMP_C void __thiscall sub_00458F80(void *stream, void *dst, unsigned int size);
DECOMP_C void __thiscall sub_00459010(void *self);
DECOMP_C void __thiscall sub_00459170(void *self);
DECOMP_C unsigned int __stdcall sub_004DFDA0(unsigned int pf0, unsigned int pf1, unsigned int pf2, unsigned int pf3,
                                             unsigned int pf4, unsigned int pf5, unsigned int pf6, unsigned int pf7,
                                             unsigned char *packed, float *bpp);
DECOMP_C void __cdecl sub_00458940(int hr, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C char d_006CA6F8[], d_006CA6F4[], d_0060F280[], d_0060B008[], d_006125BC[], d_0069916C[], d_0061259C[],
    d_006C8C10[], d_0068AE08[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
typedef void (__thiscall *skip_4E0000)(void *self, unsigned int n);
typedef int (__stdcall *create_4E0000)(void *dev, unsigned int w, unsigned int h, unsigned int levels,
                                       unsigned int usage, unsigned int fmt, unsigned int pool, void **out,
                                       void *share);
typedef int (__stdcall *getsurf_4E0000)(void *tex, unsigned int level, void **out);
typedef int (__stdcall *lock_4E0000)(void *surf, void *lr, void *rect, unsigned int flags);
typedef int (__stdcall *com_4E0000)(void *o);
typedef int (__stdcall *update_4E0000)(void *dev, void *src, void *dst);

#define VT(o) (*(void ***)(o))

static void fail_4E0000(char *s, const char *text, int line)
{
    unsigned int a[7], b[7], c[7], thrown[7];
    imp_00607324(a, text);
    sub_00421220(thrown, imp_006071DC(c, imp_006071C0(b, a, s + 8), d_0060B008), d_006125BC, line);
    sub_005E3EC0(thrown, d_0069916C);
}

static unsigned int size_4E0000(unsigned int h, unsigned int w, float bpp, unsigned char packed)
{
    unsigned int n = h * w, sz;
    float f = (float)(int)n;
    if ((int)n < 0)
        f += *(float *)d_0068AE08;
    sz = (unsigned int)(long long)(f * bpp);
    if (packed && sz < 8)
        sz = 8;
    return sz;
}

DECOMP(004E0000)
void __thiscall f_004E0000(void *this)
{
    char *s = (char *)this, *dev;
    unsigned int rd[0x30 / 4], hdr[0x7c / 4], *pf, h, w, mips, skip, lvl;
    unsigned char packed;
    float bpp;
    void *tmp = 0, *surf;
    struct { int pitch; void *bits; } lr;
    if (!(*(unsigned int *)d_006CA6F8 & 1)) {
        *(unsigned int *)d_006CA6F8 |= 1;
        *(unsigned int *)d_006CA6F4 = *(unsigned int *)(sub_00427990() + 0x64);
    }
    *(unsigned int *)(s + 0x78) = 0;
    *(unsigned int *)(s + 0x7c) = 0;
    sub_00459290(rd, s + 8, 1);
    if (!((unsigned char *)rd)[0x2c])
        fail_4E0000(s, d_0060F280, 0x8a);
    ((skip_4E0000)VT(rd[9])[0xc / 4])((void *)rd[9], 4);
    sub_00458F80(rd, hdr, 0x7c);
    if (!hdr[6])
        hdr[6] = 1;
    pf = &hdr[0x48 / 4];
    *(unsigned int *)(s + 0x74) = sub_004DFDA0(pf[0], pf[1], pf[2], pf[3], pf[4], pf[5], pf[6], pf[7], &packed, &bpp);
    if (!*(unsigned int *)(s + 0x74))
        fail_4E0000(s, d_0061259C, 0x9b);
    w = hdr[3];
    h = hdr[2];
    mips = hdr[6];
    skip = *(unsigned int *)d_006CA6F4;
    if (!s[0x64] && mips > skip && skip) {
        unsigned int k;
        int v = (int)(mips - skip);
        *(int *)(s + 0x70) = v > 1 ? v : 1;
        v = (int)(w / (skip * 2));
        *(int *)(s + 0x68) = v > 1 ? v : 1;
        v = (int)(h / (skip * 2));
        *(int *)(s + 0x6c) = v > 1 ? v : 1;
        for (k = 0; k < *(unsigned int *)d_006CA6F4; k++) {
            ((skip_4E0000)VT(rd[9])[0xc / 4])((void *)rd[9], size_4E0000(h, w, bpp, packed));
            h >>= 1;
            w >>= 1;
        }
    } else {
        *(unsigned int *)(s + 0x70) = mips;
        *(unsigned int *)(s + 0x68) = w;
        *(unsigned int *)(s + 0x6c) = h;
    }
    dev = *(char **)d_006C8C10;
    sub_00458940(((create_4E0000)VT(dev)[0x5c / 4])(dev, *(unsigned int *)(s + 0x68), *(unsigned int *)(s + 0x6c),
                                                    *(unsigned int *)(s + 0x70), 0, *(unsigned int *)(s + 0x74), 0,
                                                    (void **)(s + 0x60), 0), d_006125BC, 0xc4);
    dev = *(char **)d_006C8C10;
    sub_00458940(((create_4E0000)VT(dev)[0x5c / 4])(dev, *(unsigned int *)(s + 0x68), *(unsigned int *)(s + 0x6c),
                                                    *(unsigned int *)(s + 0x70), 0, *(unsigned int *)(s + 0x74), 2,
                                                    &tmp, 0), d_006125BC, 0xc9);
    for (lvl = 0; lvl < *(unsigned int *)(s + 0x70); lvl++) {
        unsigned int sz = size_4E0000(h, w, bpp, packed);
        ((getsurf_4E0000)VT(tmp)[0x48 / 4])(tmp, lvl, &surf);
        ((lock_4E0000)VT(surf)[0x34 / 4])(surf, &lr, 0, 0x8000);   /* D3DLOCK_NOSYSLOCK */
        sub_00458F80(rd, lr.bits, sz);
        ((com_4E0000)VT(surf)[0x38 / 4])(surf);
        ((com_4E0000)VT(surf)[2])(surf);
        h >>= 1;
        w >>= 1;
        surf = 0;
    }
    ((com_4E0000)VT(*(void **)(s + 0x60))[1])(*(void **)(s + 0x60));
    dev = *(char **)d_006C8C10;
    sub_00458940(((update_4E0000)VT(dev)[0x7c / 4])(dev, tmp, *(void **)(s + 0x60)), d_006125BC, 0xe5);
    ((com_4E0000)VT(*(void **)(s + 0x60))[2])(*(void **)(s + 0x60));
    if (tmp) {
        ((com_4E0000)VT(tmp)[2])(tmp);
        tmp = 0;
    }
    *(unsigned int *)(s + 0x6c) = hdr[2];
    *(unsigned int *)(s + 0x68) = hdr[3];
    sub_00459010(rd);
    sub_00459170(rd);
}
