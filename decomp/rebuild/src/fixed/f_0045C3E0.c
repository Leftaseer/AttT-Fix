/* 0x0045C3E0: turns a 24-float record into a ratio of sqrt(length) to tan(scale); the original rounds the
 * deltas, the length, both CRT results and both quotients to float, and feeds tan with the exact double pi/180
 * rather than its float rounding, which matters next to a tan pole */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP_C char d_00607CE0[], d_00608528[], d_006CA2C4[];
DECOMP_C double decomp_CIsqrt(double), decomp_CItan(double);

DECOMP(0045C3E0)
float __thiscall f_0045C3E0(void *this, float param_1)
{
    float v[24];
    int i;
    int p = *(int *)(*(int *)((int)this + 0x254) + 0x1c4);
    volatile float d0, d1, d2;
    volatile float dx, dy, dz;
    volatile float l2, s, t, tanv, q, out;

    for (i = 0; i < 24; i++) v[i] = *(float *)(p + 0x40 + i * 4);

    d0 = v[21] - v[0];
    d1 = v[22] - v[1];
    d2 = v[23] - v[2];
    dx = *(float *)((int)this + 0x98) * d0;
    dy = *(float *)((int)this + 0x9c) * d1;
    dz = *(float *)((int)this + 0xa0) * d2;

    l2 = (dx * dx + dy * dy) + dz * dz;
    s = (float)decomp_CIsqrt(l2);
    t = 0.5 * *(float *)(*(int *)d_006CA2C4 + 0x74) * *(double *)d_00608528;
    tanv = (float)decomp_CItan(t);
    q = (float)((double)s * 0.5 / tanv);
    out = q * param_1;
    return out;
}
