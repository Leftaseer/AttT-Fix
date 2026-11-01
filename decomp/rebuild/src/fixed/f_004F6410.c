/* 0x004F6410: param_1 with its low byte set to 1 when the triangle (param_1, param_2, param_3) has a non-positive
 * doubled area, 0 otherwise; the area (the cross product with the y components, x and z read as the 2D coordinates)
 * is kept in the float at 0x6CA848. The original stores it to the global and compares the reloaded float, so a tiny
 * positive area that rounds to 0.0f counts as 0 <= area; volatile keeps that rounding (clang otherwise compares the
 * unrounded x87 value, and the emitted code then returned the opposite tag for such areas). */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C char d_006CA848[];

DECOMP(004F6410)
undefined4 __cdecl f_004F6410(float *param_1, float *param_2, float *param_3)
{
    volatile float *area = (volatile float *)d_006CA848;

    *area = (param_1[2] - param_2[2]) * (*param_3 - *param_2) -
            (param_3[2] - param_2[2]) * (*param_1 - *param_2);
    return ((unsigned int)param_1 & 0xFFFFFF00u) | (0.0f < *area ? 0u : 1u);
}
