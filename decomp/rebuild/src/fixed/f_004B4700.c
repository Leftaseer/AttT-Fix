/* 0x004B4700: (re)creates the save-game thumbnail: its texture (+0x1C) and surface (+0x20) released, a render target
 * of the configured size (Config.SaveWidth / SaveHeight, truncated) and format (+0x5C of 0x00427990): D3DX render-to-
 * surface and a texture (X8R8G8B8), and one frame drawn into it (Clear with the colour +0xA0 of 0x0042F160, the scene
 * by 0x0044A210) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C char *__cdecl sub_0042F160(void);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C unsigned int __thiscall sub_0044A210(void *self);
DECOMP_C long __stdcall sub_005B8050(void *dev, unsigned int w, unsigned int h, unsigned int fmt, int depth,
                                     unsigned int dsfmt, void **out);                  /* D3DXCreateRenderToSurface */
DECOMP_C long __stdcall sub_005B8092(void *dev, unsigned int w, unsigned int h, unsigned int mips, unsigned int usage,
                                     unsigned int fmt, unsigned int pool, void **out);   /* D3DXCreateTexture */
DECOMP_C char d_006C8C10[], d_0060AFF4[], d_00610EB4[], d_00610EA8[];
typedef unsigned long (__stdcall *Release_4B4700)(void *o);
typedef long (__stdcall *GetSurface_4B4700)(void *tex, unsigned int level, void **out);
typedef long (__stdcall *Begin_4B4700)(void *rts, void *surf, const void *vp);
typedef long (__stdcall *End_4B4700)(void *rts, unsigned int filter);
typedef long (__stdcall *Clear_4B4700)(void *dev, unsigned int n, const void *rects, unsigned int flags,
                                       unsigned int color, float z, unsigned int stencil);

#define DEV (*(void ***)d_006C8C10)
#define VT(o) (*(void ***)(o))

DECOMP(004B4700)
void __thiscall f_004B4700(void *this)
{
    char *s = (char *)this;
    void ***surf = (void ***)(s + 0x20), ***tex = (void ***)(s + 0x1c), **rts;
    unsigned int fmt, w, h, t[3];
    if (*surf) {
        ((Release_4B4700)VT(*surf)[2])(*surf);
        *surf = 0;
    }
    if (*tex) {
        ((Release_4B4700)VT(*tex)[2])(*tex);
        *tex = 0;
    }
    fmt = *(unsigned int *)(sub_00427990() + 0x5c);
    w = (unsigned int)(long long)sub_0057AD40(sub_004323E0(t, d_0060AFF4), d_00610EB4);
    sub_004220A0(t);
    h = (unsigned int)(long long)sub_0057AD40(sub_004323E0(t, d_0060AFF4), d_00610EA8);
    sub_004220A0(t);
    sub_005B8050(DEV, w, h, 0x16, 1, fmt, (void **)&rts);
    sub_005B8092(DEV, w, h, 1, 0, 0x16, 1, (void **)tex);
    ((GetSurface_4B4700)VT(*tex)[0x48 / 4])(*tex, 0, (void **)surf);
    ((Begin_4B4700)VT(rts)[0x14 / 4])(rts, *surf, 0);
    ((Clear_4B4700)VT(DEV)[0xac / 4])(DEV, 0, 0, 3, *(unsigned int *)(sub_0042F160() + 0xa0), 1.0f, 0);
    sub_0044A210(sub_0042F160());
    ((End_4B4700)VT(rts)[0x18 / 4])(rts, 1);
    if (rts)
        ((Release_4B4700)VT(rts)[2])(rts);
}
