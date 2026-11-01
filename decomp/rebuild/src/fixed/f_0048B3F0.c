/* 0x0048B3F0: mirror of 0x48B3D0 with the arguments swapped: returns param_2 when param_1's float is
 * ordered-greater than param_2's (fcomi + ja), otherwise param_1; NaN falls through to param_1 */
/* @conv - 0 */
#include "auto_pre.h"

DECOMP(0048B3F0)
float *__cdecl f_0048B3F0(float *param_1, float *param_2)
{
    return (*param_1 > *param_2) ? param_2 : param_1;
}
