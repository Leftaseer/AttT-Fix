/* 0x0042ADB0: the horizontal motion (x, z) of key `index` turned by the angle: z*sin + x*cos in x and
 * cos*z - sin*x in z.  The first key has no step and yields (0, 0). */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C double decomp_CIcos(double);
DECOMP_C double decomp_CIsin(double);
DECOMP_C char d_00608528[];

DECOMP(0042ADB0)
void __thiscall f_0042ADB0(void *this, float *out, float degrees, int index)
{
    const float *keys = *(const float **)((char *)this + 0x1d8);
    float dx = 0.0f, dz = 0.0f;
    float angle, sine, cosine;

    if (index != *(int *)((char *)this + 0x1d0)) {
        dx = keys[index * 3] - keys[index * 3 - 3];
        dz = keys[index * 3 + 2] - keys[index * 3 - 1];
    }
    angle = GH_FROUND(degrees * *(double *)d_00608528);
    sine = GH_FROUND(decomp_CIsin(angle));
    cosine = GH_FROUND(decomp_CIcos(angle));
    out[0] = dz * sine + dx * cosine;
    out[1] = cosine * dz - sine * dx;
    return;
}
