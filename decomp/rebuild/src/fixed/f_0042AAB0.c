/* 0x0042AAB0: the turned motion of the current animation segment: the horizontal step (the keys' x difference) and
 * the vertical step (z of the next key minus z of the previous one) are rotated by the angle into (x, y); a
 * single-key animation yields (0, 0). */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C double decomp_CIcos(double);
DECOMP_C double decomp_CIsin(double);
DECOMP_C char d_00608528[];
/* @func 0042AAB0 */
#define sub_005E4058 decomp_CIcos
#define sub_005E405E decomp_CIsin
#define GV_00608528_8 (*(double *)d_00608528)
DECOMP(0042AAB0)
undefined4 __thiscall f_0042AAB0(void *this, float *param_1, float param_2)
{
  float *pfVar1;
  float fVar2;
  float fVar3;
  int iVar4;
  float fVar5;
  float fVar6;
  float10 fVar7;
  float10 fVar8;

  iVar4 = *(int *)((int)this + 0x1cc);
  if (iVar4 != *(int *)((int)this + 0x1d0)) {
    pfVar1 = (float *)(*(int *)((int)this + 0x1d8) + -0xc + iVar4 * 0xc);
    fVar5 = *(float *)(*(int *)((int)this + 0x1d8) + iVar4 * 0xc) - *pfVar1;
    fVar2 = pfVar1[5];
    fVar3 = pfVar1[2];
    fVar6 = GV_00608528_8;
    fVar7 = sub_005E405E((float10)GH_FROUND((param_2 * fVar6)));
    fVar8 = sub_005E4058((float10)GH_FROUND((param_2 * fVar6)));
    *param_1 = (fVar2 - fVar3) * (float)fVar7 + fVar5 * (float)fVar8;
    param_1[1] = (float)fVar8 * (fVar2 - fVar3) - (float)fVar7 * fVar5;
    return param_1;
  }
  *param_1 = 0.0;
  param_1[1] = 0.0;
  return param_1;
}
#undef sub_005E4058
#undef sub_005E405E
#undef GV_00608528_8
