/* 0x00456A00: dot product, added as the original does: (y*y' + x*x') + z*z', rounded to float */
#include "auto_pre.h"

DECOMP(00456A00)
float __cdecl f_00456A00(float *param_1, float *param_2)
{
    volatile float r = (param_1[1] * param_2[1] + *param_1 * *param_2) + param_1[2] * param_2[2];

    return r;
}
