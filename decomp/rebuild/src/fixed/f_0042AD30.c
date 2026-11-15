/* 0x0042AD30: the vertical (y, z) direction of key `index` (its z minus the previous key's z) turned by the angle:
 * sin in y and cos in z.  The first key has no step and yields (0, 0). */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C double decomp_CIcos(double);
DECOMP_C double decomp_CIsin(double);
DECOMP_C char d_00608528[];

DECOMP(0042AD30)
float *__thiscall f_0042AD30(void *this, float *out, float degrees, int index)
{
    const float *keys = *(const float **)((char *)this + 0x1d8);
    float step = 0.0f;
    float angle, sine, cosine;

    if (index != *(int *)((char *)this + 0x1d0))
        step = keys[index * 3 + 2] - keys[index * 3 - 1];
    angle = GH_FROUND(degrees * *(double *)d_00608528);
    sine = GH_FROUND(decomp_CIsin(angle));
    out[0] = sine * step;
    cosine = GH_FROUND(decomp_CIcos(angle));
    out[1] = cosine * step;
    return out;
}
