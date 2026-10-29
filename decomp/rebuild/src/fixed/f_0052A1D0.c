/* 0x0052A1D0: CContinent::vf4 (restoring the device objects): creates what is missing of its two vertex buffers
 * (+0x208 / +0x20C: +0x2D8 vertices of 32 bytes, write-only dynamic, FVF 0x112), its index buffer (+0x214: +0x2DC
 * 16-bit indices) and its RenderToSurface (+0x2C0: +0x2D4 square, R5G6B5, D3DXCreateRenderToSurface), each checked by
 * 0x00458940 (Continent.cpp) and throwing "Continent: error creating the vertex buffer / index buffer /
 * RenderToSurface" on failure; both vertex buffers get the vertices of +0x1EC..+0x1F0, and 0x005296B0 finishes.
 * Returns its EAX */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00458940(int hr, const char *file, int line);
DECOMP_C int __stdcall sub_005B8050(void *dev, unsigned int w, unsigned int h, unsigned int fmt, int depth,
                                    unsigned int dfmt, void **out);   /* D3DXCreateRenderToSurface */
DECOMP_C int __thiscall sub_005296B0(void *self);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void *__cdecl sub_005E4232(void *d, const void *s, unsigned int n);   /* memcpy */
DECOMP_C char d_006C8C10[], d_00615060[], d_00615030[], d_00615000[], d_00614FD4[], d_0069916C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
typedef int (__stdcall *create_52A1D0)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                       unsigned int pool, void **out, void *share);
typedef int (__stdcall *lock_52A1D0)(void *b, unsigned int off, unsigned int len, void **p, unsigned int flags);
typedef int (__stdcall *unlock_52A1D0)(void *b);

#define VT(o) (*(void ***)(o))

static void fail_52A1D0(const char *text, int line)
{
    unsigned int msg[7], thrown[7];
    imp_00607324(msg, text);
    sub_00421220(thrown, msg, d_00615060, line);
    sub_005E3EC0(thrown, d_0069916C);
}

static void fill_52A1D0(char *s, void **f)
{
    void *p, *b = *f;
    char *v = *(char **)(s + 0x1ec);
    ((lock_52A1D0)VT(b)[0x2c / 4])(b, 0, (v ? (unsigned int)((*(char **)(s + 0x1f0) - v) >> 5) : 0) << 5, &p, 0);
    v = *(char **)(s + 0x1ec);
    sub_005E4232(p, v, (v ? (unsigned int)((*(char **)(s + 0x1f0) - v) >> 5) : 0) << 5);
    b = *f;
    ((unlock_52A1D0)VT(b)[0x30 / 4])(b);
}

DECOMP(0052A1D0)
int __thiscall f_0052A1D0(void *this)
{
    char *s = (char *)this;
    void *dev;
    int hr;
    if (!*(void **)(s + 0x208)) {
        dev = *(void **)d_006C8C10;
        hr = ((create_52A1D0)VT(dev)[0x68 / 4])(dev, *(unsigned int *)(s + 0x2d8) << 5, 0x208, 0x112, 0,
                                                 (void **)(s + 0x208), 0);
        sub_00458940(hr, d_00615060, 0xce);
        if (hr)
            fail_52A1D0(d_00615030, 0xd2);
    }
    if (!*(void **)(s + 0x20c)) {
        dev = *(void **)d_006C8C10;
        hr = ((create_52A1D0)VT(dev)[0x68 / 4])(dev, *(unsigned int *)(s + 0x2d8) << 5, 0x208, 0x112, 0,
                                                 (void **)(s + 0x20c), 0);
        sub_00458940(hr, d_00615060, 0xd9);
        if (hr)
            fail_52A1D0(d_00615030, 0xdd);
    }
    if (!*(void **)(s + 0x214)) {
        dev = *(void **)d_006C8C10;
        hr = ((create_52A1D0)VT(dev)[0x6c / 4])(dev, *(unsigned int *)(s + 0x2dc) * 2, 0x208, 0x65, 0,
                                                 (void **)(s + 0x214), 0);
        sub_00458940(hr, d_00615060, 0xe4);
        if (hr)
            fail_52A1D0(d_00615000, 0xe8);
    }
    fill_52A1D0(s, (void **)(s + 0x208));
    fill_52A1D0(s, (void **)(s + 0x20c));
    if (!*(void **)(s + 0x2c0)) {
        unsigned int n = *(unsigned int *)(s + 0x2d4);
        hr = sub_005B8050(*(void **)d_006C8C10, n, n, 0x17, 0, 0, (void **)(s + 0x2c0));
        sub_00458940(hr, d_00615060, 0xf7);
        if (hr)
            fail_52A1D0(d_00614FD4, 0xfa);
    }
    return sub_005296B0(this);
}
