/* 0x00586BA0: sets up a 2D rectangle outline: a managed vertex buffer (+0x290) holding a closed line strip of five
 * XYZ|DIFFUSE vertices round the unit square (0 and 0x0068AE40 in x and y, z 0x0060B874) in the colour (arg 5),
 * failures reported to 0x00458940 with ".\Rect.cpp"; when locked, filled, then the "2dline" effect (vf2C), the
 * position (vf78: args 1, 2 plus the 0x00607CE0 offset) and the size (vf94: args 3, 4) */
/* @conv ECX 20 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00458940(long hr, const char *file, int line);
DECOMP_C char d_006C8C10[], d_0060B874[], d_0068AE40[], d_0061E97C[], d_0061E974[], d_00607CE0[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef long (__stdcall *create_586BA0)(void *dev, unsigned int len, unsigned int usage, unsigned int fmt,
                                        unsigned int pool, void *out, void *h);
typedef long (__stdcall *lock_586BA0)(void *self, unsigned int off, unsigned int size, void **data, unsigned int fl);
typedef long (__stdcall *com_586BA0)(void *self);
typedef void (__thiscall *fx_586BA0)(void *self, void *name, int a);
typedef void (__thiscall *xy_586BA0)(void *self, float x, float y);

#define DEV (*(void ***)d_006C8C10)

DECOMP(00586BA0)
void __thiscall f_00586BA0(void *this, float x, float y, float w, float h, unsigned int color)
{
    char *s = (char *)this;
    unsigned int v[20], z = *(unsigned int *)d_0060B874, one = *(unsigned int *)d_0068AE40, str[7];
    void **vb, *data;
    float fx, fy;
    v[0] = 0, v[1] = 0, v[2] = z, v[3] = color;
    v[4] = one, v[5] = 0, v[6] = z, v[7] = color;
    v[8] = one, v[9] = one, v[10] = z, v[11] = color;
    v[12] = 0, v[13] = one, v[14] = z, v[15] = color;
    v[16] = 0, v[17] = 0, v[18] = z, v[19] = color;
    sub_00458940(((create_586BA0)(*(void ***)DEV)[0x68 / 4])(DEV, 0x50, 8, 0x42, 1, s + 0x290, 0), d_0061E97C, 0x28);
    vb = *(void ***)(s + 0x290);
    if (((lock_586BA0)(*(void ***)vb)[0x2c / 4])(vb, 0, 0x50, &data, 0) < 0)
        return;
    __builtin_memcpy(data, v, 0x50);
    vb = *(void ***)(s + 0x290);
    ((com_586BA0)(*(void ***)vb)[0x30 / 4])(vb);
    imp_00607324(str, d_0061E974);
    ((fx_586BA0)(*(void ***)this)[0x2c / 4])(this, str, 0);
    imp_00607330(str);
    fy = (float)(y + *(double *)d_00607CE0);
    fx = (float)(x + *(double *)d_00607CE0);
    ((xy_586BA0)(*(void ***)this)[0x78 / 4])(this, fx, fy);
    ((xy_586BA0)(*(void ***)this)[0x94 / 4])(this, w, h);
}
