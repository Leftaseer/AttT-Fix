/* 0x0047FCC0: normalizes the 2D vector p in place: p *= 1/sqrt(x*x + y*y).  The original rounds the sum to
 * float before the sqrt, the root to float before the division and the reciprocal to float before the products
 * (an fstp dword [esp+0xc] between each); the generated code kept all three in extended precision. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C double decomp_CIsqrt(double);

DECOMP(0047FCC0)
float *__fastcall f_0047FCC0(float *param_1)
{
    float x = param_1[0], y = param_1[1];
    volatile float s = (float)decomp_CIsqrt(GH_FROUND(x * x + y * y));
    volatile float inv = 1.0 / s;

    param_1[0] = inv * x;
    param_1[1] = inv * y;
    return param_1;
}
