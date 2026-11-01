/* 0x0047FBC0: distance from a point to the line through param_1[0..1] / param_1[2..3]; the x87 code rounds
 * each direction and 1/length to float before the next product and adds the two terms in the opposite order to
 * the decompiler, and it returns 0 for a zero or unordered denominator */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP_C double decomp_CIsqrt(double);

DECOMP(0047FBC0)
double __thiscall f_0047FBC0(void *this, float *param_1)
{
    float p0 = param_1[0];
    float p1 = param_1[1];
    volatile float a = param_1[1] - param_1[3];
    volatile float b = param_1[2] - param_1[0];
    volatile float l2 = a * a + b * b;
    volatile float s = (float)decomp_CIsqrt(l2);
    volatile float inv = 1.0f / s;
    volatile float fa = a * inv;
    volatile float fb = b * inv;
    volatile float v = -a * fa + -b * fb;
    volatile float q;

    if (v == 0.0f || v != v) return 0.0;
    q = -((-a * (*(float *)this - p0) + -b * (*(float *)((int)this + 4) - p1)) / v);
    return q;
}
