/* 0x0047FA00: 2D dot product, rounded to float */
#include "auto_pre.h"

DECOMP(0047FA00)
float __cdecl f_0047FA00(float *param_1, float *param_2)
{
    volatile float r = *param_1 * *param_2 + param_1[1] * param_2[1];

    return r;
}
