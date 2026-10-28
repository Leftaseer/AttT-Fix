/* 0x00551F60: a particle emitter's update (flags): within the distance +0x600 of the camera (0x6CA2C4 +0x44, the
 * squared xz distance of its position: the delegate at +0x2E4 plus +0x64 / +0x6C) and once its delay counter (+0x608)
 * reaches +0x604: its time advances (+0x5E4 = +0x5E0 + the rate +0x24 / the double at 0x68AE10), emits (flag 1:
 * 0x00551A70) and moves its particles (flag 2: 0x0054FED0), keeps the time and the source (+0x2E4 at +0x56C); when
 * its life delegate (+0x24C) says so and its duration delegate (+0x2BC) gives a nonzero time shorter than the
 * emitter's, it stops (+0x24C cleared) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00551A70(void *self);
DECOMP_C void __thiscall sub_0054FED0(void *self);
DECOMP_C char d_006CA2C4[], d_0068AE10[];
typedef unsigned int *(__thiscall *pos_551F60)(void *ctx, void *out, void *d);
typedef char (__thiscall *flag_551F60)(void *ctx, void *d);
typedef float (__thiscall *time_551F60)(void *ctx, void *d);

DECOMP(00551F60)
void __thiscall f_00551F60(void *this, unsigned int flags)
{
    char *s = (char *)this;
    float *cam = (float *)(*(char **)d_006CA2C4 + 0x44), tmp[3], p[3], x, z, dx, dz, d2;
    unsigned int c;
    char *e;
    unsigned int *v = ((pos_551F60)*(void **)(s + 0x2f0))(*(void **)(s + 0x2f8), tmp, s + 0x2e4);
    ((unsigned int *)p)[0] = v[0];
    ((unsigned int *)p)[1] = v[1];
    ((unsigned int *)p)[2] = v[2];
    x = *(float *)(s + 0x64) + p[0];
    z = *(float *)(s + 0x6c) + p[2];
    dx = cam[0] - x;
    dz = cam[2] - z;
    d2 = dx * dx + 0.0f * 0.0f + dz * dz;
    if (d2 >= *(float *)(s + 0x600))
        return;
    c = *(unsigned int *)(s + 0x608);
    *(unsigned int *)(s + 0x608) = c + 1;
    if (c < *(unsigned int *)(s + 0x604))
        return;
    *(float *)(s + 0x5e4) = (float)(*(float *)(s + 0x24) / *(double *)d_0068AE10 + *(float *)(s + 0x5e0));
    if (flags & 1)
        sub_00551A70(this);
    if (flags & 2)
        sub_0054FED0(this);
    *(float *)(s + 0x5e0) = *(float *)(s + 0x5e4);
    ((unsigned int *)(s + 0x56c))[0] = ((unsigned int *)(s + 0x2e4))[0];
    ((unsigned int *)(s + 0x56c))[1] = ((unsigned int *)(s + 0x2e4))[1];
    ((unsigned int *)(s + 0x56c))[2] = ((unsigned int *)(s + 0x2e4))[2];
    if (!((flag_551F60)*(void **)(s + 0x250))(*(void **)(s + 0x258), s + 0x24c))
        return;
    e = s + 0x2bc;
    if (((time_551F60)*(void **)(e + 4))(*(void **)(e + 0xc), e) != 0.0f) {
        float w = ((time_551F60)*(void **)(e + 4))(*(void **)(e + 0xc), e);
        if (*(float *)(s + 0x5e4) > w)
            s[0x24c] = 0;
    }
}
