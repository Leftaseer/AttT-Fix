/* 0x0048B3D0: returns param_2 when its float is ordered-greater than param_1's (fcomi + ja), otherwise
 * param_1; an unordered compare falls through to param_1, which the C <= form did not reproduce */
/* @conv - 0 */
#include "auto_pre.h"

DECOMP(0048B3D0)
float *__cdecl f_0048B3D0(float *param_1, float *param_2)
{
    return (*param_2 > *param_1) ? param_2 : param_1;
}
