/* 0x0042D9E0: 0x0042D8D0's point at time t, then 0x005B8026(out, out, +0x24); returns out. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void *__stdcall sub_005B8026(void *a, void *b, void *c);
DECOMP_C char d_00607CE0[], d_00608B40[];                               /* double 0.5, gravity */

DECOMP(0042D9E0)
float *__thiscall f_0042D9E0(char *this, float *out, float t)
{
    float x = *(float *)(this + 0x1c) * t - *(float *)(this + 0x20) * *(double *)d_00607CE0;

    out[2] = 0.0f;
    out[0] = x;
    out[1] = (x * x / *(double *)d_00608B40) * *(float *)this;
    sub_005B8026(out, out, this + 0x24);
    return out;
}
