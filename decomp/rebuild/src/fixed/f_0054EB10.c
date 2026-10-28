/* 0x0054EB10: NParticleSystem::COriginPoint::vf1: the point's position from its delegate (+0x584: function +0x590,
 * context +0x598) into out; if the second delegate (+0x5AC: +0x5B0, +0x5B8) says so, its height follows the terrain:
 * out.y += height at out (x, z) - height at the delegate's (x, z) (0x00473110 of 0x00433620's terrain, the first
 * kept as a double) */
/* @conv - 12 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_00433620(void);
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
typedef unsigned int *(__thiscall *pos_54EB10)(void *ctx, void *out, void *d);
typedef unsigned int (__thiscall *flag_54EB10)(void *ctx, void *d);

DECOMP(0054EB10)
unsigned int __stdcall f_0054EB10(char *o, float *out, unsigned int unused)
{
    char *d = o + 0x584;
    unsigned int tmp[3], a[3], b[3], *v;
    unsigned int r;
    double h;
    v = ((pos_54EB10)*(void **)(o + 0x590))(*(void **)(o + 0x598), tmp, d);
    ((unsigned int *)out)[0] = v[0];
    ((unsigned int *)out)[1] = v[1];
    ((unsigned int *)out)[2] = v[2];
    r = ((flag_54EB10)*(void **)(o + 0x5b0))(*(void **)(o + 0x5b8), o + 0x5ac);
    if (!(char)r)
        return r;
    v = ((pos_54EB10)*(void **)(d + 0xc))(*(void **)(d + 0x14), tmp, d);
    a[0] = v[0]; a[1] = v[1]; a[2] = v[2];
    v = ((pos_54EB10)*(void **)(d + 0xc))(*(void **)(d + 0x14), tmp, d);
    b[0] = v[0]; b[1] = v[1]; b[2] = v[2];
    h = sub_00473110(sub_00433620(), out[0], out[2]);
    out[1] = (float)(h - sub_00473110(sub_00433620(), ((float *)b)[0], ((float *)a)[2]) + out[1]);
    return r;
}
