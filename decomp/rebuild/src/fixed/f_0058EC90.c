/* 0x0058EC90: dot(c, cross(a, b)).  MSVC rounds each cross-product component to float (fstp dword) and only
 * then multiplies by c, summing in x87 extended precision in the order (c1*y + c0*x) + c2*z, with a single
 * rounding of the sum.  The generated expression kept the whole product in extended precision, which changes
 * the low bits of the result (1 ulp observed).  The volatile float components pin the rounding points. */
#include "auto_pre.h"
/* @func 0058EC90 */

DECOMP(0058EC90)
float __stdcall f_0058EC90(float *param_1, float *param_2, float *param_3)
{
  volatile float x = param_1[1] * param_2[2] - param_1[2] * param_2[1];
  volatile float y = param_1[2] * param_2[0] - param_1[0] * param_2[2];
  volatile float z = param_1[0] * param_2[1] - param_1[1] * param_2[0];
  { volatile float gh_ret = param_3[1] * y + param_3[0] * x + param_3[2] * z; return gh_ret; }
}
