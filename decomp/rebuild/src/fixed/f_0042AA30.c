/* 0x0042AA30: the direction (x, y) of the current animation segment in the vertical plane, rotated by the angle
 * (sin in x, cos in y).  A single-key animation yields (0, 0). */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C double decomp_CIcos(double);
DECOMP_C double decomp_CIsin(double);
DECOMP_C char d_00608528[];
/* @func 0042AA30 */
#define sub_005E4058 decomp_CIcos
#define sub_005E405E decomp_CIsin
#define GV_00608528_8 (*(double *)d_00608528)
DECOMP(0042AA30)
float *__thiscall f_0042AA30(void *this, float *param_1, float param_2)
{
#define local_8 (*(float *)(gh_frame + 0))
  unsigned char gh_frame[8] __attribute__((aligned(16)));
  int iVar1;
  float fVar2;
  float10 fVar3;

  iVar1 = *(int *)((int)this + 0x1cc);
  if (iVar1 == *(int *)((int)this + 0x1d0)) {
    local_8 = 0.0;
  }
  else {
    local_8 = *(float *)(*(int *)((int)this + 0x1d8) + 8 + iVar1 * 0xc) -
              *(float *)(*(int *)((int)this + 0x1d8) + iVar1 * 0xc + -4);
  }
  fVar2 = GV_00608528_8;
  fVar3 = sub_005E405E((float10)GH_FROUND((param_2 * fVar2)));
  *param_1 = (float)fVar3 * local_8;
  fVar3 = sub_005E4058((float10)GH_FROUND((param_2 * fVar2)));
  param_1[1] = (float)fVar3 * local_8;
  return param_1;
}
#undef sub_005E4058
#undef sub_005E405E
#undef GV_00608528_8
#undef local_8
