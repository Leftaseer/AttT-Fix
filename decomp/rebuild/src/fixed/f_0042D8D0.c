/* 0x0042D8D0: a point of the trajectory at time t: x = v.x * t - v.y * 0.5 (the 0.5 at 0x00607CE0),
 * y = x^2 / gravity (0x00608B40) * scale (the float at +0), z = 0. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_00607CE0[], d_00608B40[];                               /* double 0.5, gravity */

DECOMP(0042D8D0)
void __thiscall f_0042D8D0(char *this, float *out, float t)
{
    float x = *(float *)(this + 0x1c) * t - *(float *)(this + 0x20) * *(double *)d_00607CE0;

    out[2] = 0.0f;
    out[0] = x;
    out[1] = (x * x / *(double *)d_00608B40) * *(float *)this;
}
