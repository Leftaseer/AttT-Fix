#include "auto_pre.h"
/* @func 0047F980 */
DECOMP(0047F980)
undefined4 __thiscall f_0047F980(void *this, float *param_1, float param_2)
{
  float fVar1;
  float fVar2;
  
                    /* WARNING: Load size is inaccurate */
  fVar1 = *(float *)((int)this + 4);
  fVar2 = *(float *)((int)this + 0xc);
  *param_1 = GH_FROUND(param_2 * GH_FROUND(*(float *)((int)this + 8) - *(float *)this)) + *(float *)this;
  param_1[1] = fVar1 + GH_FROUND(param_2 * GH_FROUND(fVar2 - fVar1));
  return param_1;
}
