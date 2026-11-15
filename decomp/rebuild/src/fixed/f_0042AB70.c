/* 0x0042AB70: the turned motion of the current animation segment into out (the angle is the first stack argument),
 * unless the segment is still (both steps 0): 1 when something was written, 0 otherwise. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C double decomp_CIcos(double);
DECOMP_C double decomp_CIsin(double);
DECOMP_C char d_00608528[], d_0060FAC0[];
/* @func 0042AB70 */
#define sub_005E4058 decomp_CIcos
#define sub_005E405E decomp_CIsin
#define GV_00608528_8 (*(double *)d_00608528)
#define GV_0060FAC0_4 (*(float *)d_0060FAC0)
DECOMP(0042AB70)
undefined4 __thiscall f_0042AB70(void *this, float angle, float *out)
{
  float *pfVar1;
  int iVar2;
  float fVar3;
  float fVar4;
  float fVar5;
  float10 fVar6;
  float10 fVar7;

  iVar2 = *(int *)((int)this + 0x1cc);
  if (iVar2 != *(int *)((int)this + 0x1d0)) {
    pfVar1 = (float *)(*(int *)((int)this + 0x1d8) + -0xc + iVar2 * 0xc);
    fVar3 = *(float *)(*(int *)((int)this + 0x1d8) + iVar2 * 0xc) - *pfVar1;
    fVar4 = pfVar1[5] - pfVar1[2];
    if ((fVar3 != 0.0) || (fVar4 != GV_0060FAC0_4)) {
      fVar5 = GV_00608528_8;
      fVar6 = sub_005E405E((float10)GH_FROUND((angle * fVar5)));
      fVar7 = sub_005E4058((float10)GH_FROUND((angle * fVar5)));
      *out = fVar4 * (float)fVar6 + fVar3 * (float)fVar7;
      out[1] = (float)fVar7 * fVar4 - (float)fVar6 * fVar3;
      return 1;
    }
  }
  return 0;
}
#undef sub_005E4058
#undef sub_005E405E
#undef GV_00608528_8
#undef GV_0060FAC0_4
