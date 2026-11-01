/* 0x0058F400: where a ray crosses the plane through param_4 spanned by param_5/param_6; the parameter is
 * dot(w, u x v) / dot(param_3, u x v) with u = param_5 - param_4, v = param_6 - param_4, w = param_2 - param_4.
 * MSVC rounds the ratio to float (fstp dword) before scaling param_3, rounds each scaled component again, and
 * only then subtracts from param_2 in x87 extended precision.  The generated expression kept ratio and the
 * products in extended precision, which moves the stored floats by an ulp. */
#include "auto_pre.h"
/* @func 0058F400 */
#define GV_0060A218_4 (*(float *)d_0060A218)
DECOMP_C char d_0060A218[];
DECOMP_C float __stdcall sub_0058EC90(float *p0, float *p1, float *p2);

DECOMP(0058F400)
undefined4 __thiscall f_0058F400(void *this, float *param_1, float *param_2, float *param_3, float *param_4, float *param_5, float *param_6, undefined1 *param_7)
{
  float u[3];
  float v[3];
  float w[3];
  float dot_uv;
  float dot_wv;
  int i;

  *param_7 = 1;
  for (i = 0; i < 3; i++) {
    u[i] = param_5[i] - param_4[i];
    v[i] = param_6[i] - param_4[i];
  }
  dot_uv = sub_0058EC90(param_3, u, v);
  if (ABS(dot_uv) < GV_0060A218_4) {
    *param_7 = 0;
    param_1[0] = 0.0f;
    param_1[1] = 0.0f;
    param_1[2] = 0.0f;
    return (undefined4)param_1;
  }
  for (i = 0; i < 3; i++) {
    w[i] = param_2[i] - param_4[i];
  }
  dot_wv = sub_0058EC90(w, u, v);
  {
    volatile float ratio = dot_wv / dot_uv;
    for (i = 0; i < 3; i++) {
      volatile float scaled = ratio * param_3[i];
      param_1[i] = param_2[i] - scaled;
    }
  }
  return (undefined4)param_1;
}
#undef GV_0060A218_4
