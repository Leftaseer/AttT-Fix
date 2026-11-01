/* 0x0047FB90: length of a 2D vector: x*x + y*y rounded to float, _CIsqrt of it, rounded to float */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C double decomp_CIsqrt(double);

DECOMP(0047FB90)
float __thiscall f_0047FB90(float *param_1)
{
    volatile float s = *param_1 * *param_1 + param_1[1] * param_1[1];
    volatile float r = (float)decomp_CIsqrt(s);

    return r;
}
