#include "auto_pre.h"
DECOMP_C double decomp_CIsqrt(double);
/* @func 00538A60 */
#define sub_005E406A decomp_CIsqrt
DECOMP(00538A60)
float __stdcall f_00538A60(float param_1, float param_2, float param_3, float param_4, float param_5, float param_6)
{
  float fVar1;
  float fVar2;
  float10 fVar3;
  
  fVar2 = param_5 - param_3;
  fVar1 = param_4 - param_6;
  fVar3 = sub_005E406A((float10)GH_FROUND((fVar1 * fVar1 + fVar2 * fVar2)));
  { volatile float gh_ret = ABS(GH_FROUND((param_3 * param_6 - param_4 * param_5) + fVar1 * param_1 + param_2 * fVar2)) /
         GH_FROUND((float)fVar3); return gh_ret; }
}
