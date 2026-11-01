/* 0x00424A60: the squared length of a 3D vector, as the original adds it: (y*y + x*x) + z*z, rounded to float */
#include "auto_pre.h"

DECOMP(00424A60)
float __cdecl f_00424A60(float *param_1)
{
    volatile float r = (param_1[1] * param_1[1] + *param_1 * *param_1) + param_1[2] * param_1[2];

    return r;
}
