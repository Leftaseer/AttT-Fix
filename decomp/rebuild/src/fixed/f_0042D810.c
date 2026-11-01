/* 0x0042D810: length of a 3D vector: the squared length is rounded to float, _CIsqrt of it, rounded to float */
#include "auto_pre.h"
DECOMP_C double decomp_CIsqrt(double);

DECOMP(0042D810)
float __cdecl f_0042D810(float *param_1)
{
    volatile float s = (param_1[1] * param_1[1] + *param_1 * *param_1) + param_1[2] * param_1[2];
    volatile float r = (float)decomp_CIsqrt(s);

    return r;
}
