#include "auto_pre.h"
DECOMP_C float __fastcall sub_0043F6C0(undefined4 p0);
DECOMP_C undefined4 __thiscall sub_0043F7E0(void * p0, undefined4 * p1);
DECOMP_C undefined4 __cdecl sub_0043BC20(void * p0, void * p1);
DECOMP_C undefined4 __fastcall sub_0043F710(int p0);
DECOMP_C undefined4 __thiscall sub_0043F770(void * p0, float * p1);
DECOMP_C double decomp_CIsqrt(double);
DECOMP_C char d_00608088[], d_006095F8[];
/* @func 0043C0D0 */
#define sub_005E406A decomp_CIsqrt
#define G_00608088 (*(float *)d_00608088)
#define GV_006095F8_8 (*(double *)d_006095F8)
DECOMP(0043C0D0)
undefined4 __stdcall f_0043C0D0(void *param_1, void *param_2)
{
#define local_24 (*(float *)(gh_frame + 0))
#define local_20 (*(float *)(gh_frame + 4))
#define local_1c (*(float *)(gh_frame + 8))
#define local_18 (*(float *)(gh_frame + 12))
#define fStack_14 (*(float *)(gh_frame + 16))
#define fStack_10 (*(float *)(gh_frame + 20))
#define local_c (*(float *)(gh_frame + 24))
#define fStack_8 (*(float *)(gh_frame + 28))
#define fStack_4 (*(float *)(gh_frame + 32))
  unsigned char gh_frame[36] __attribute__((aligned(16)));
  float fVar1;
  undefined4 uVar2;
  float *pfVar3;
  float *pfVar4;
  int iVar5;
  int iVar6;
  float10 fVar7;
  float fVar8;
  float fVar9;
  
  uVar2 = sub_0043BC20(param_1,param_2);
  if ((char)uVar2 == '\0') {
    return uVar2;
  }
  pfVar3 = (float *)sub_0043F7E0(param_1,&local_c);
  pfVar4 = (float *)sub_0043F7E0(param_2,&local_18);
  local_1c = GH_FROUND(pfVar4[2] - pfVar3[2]);
  local_24 = GH_FROUND(*pfVar4 - *pfVar3);
  local_20 = 0.0;
  fVar7 = sub_005E406A((float10)GH_FROUND((local_24 * local_24 + 0.0 + local_1c * local_1c)));
  fVar8 = sub_0043F6C0(param_1);
  fVar9 = sub_0043F6C0(param_2);
  fStack_10 = GH_FROUND(1.0 / GH_FROUND((float)fVar7));
  local_18 = GH_FROUND(fStack_10 * local_24);
  fStack_14 = GH_FROUND(fStack_10 * local_20);
  fStack_10 = GH_FROUND(fStack_10 * local_1c);
  local_1c = GH_FROUND(((fVar9 + fVar8) - GH_FROUND((float)fVar7)) + GV_006095F8_8);
  local_24 = GH_FROUND(local_1c * GH_FROUND(local_18));
  local_20 = GH_FROUND(GH_FROUND(fStack_14) * local_1c);
  local_1c = GH_FROUND(local_1c * GH_FROUND(fStack_10));
  local_c = local_24;
  fStack_8 = local_20;
  fStack_4 = local_1c;
  iVar5 = sub_0043F710((int)param_1);
  iVar6 = sub_0043F710((int)param_2);
  if (iVar6 == iVar5) {
    fVar1 = 1.0 / GH_FROUND_D(fVar9 + fVar8);
    fVar8 = GH_FROUND(fVar1 * fVar8);
    local_c = fVar8 * local_24;
    fStack_8 = fVar8 * local_20;
    fStack_4 = fVar8 * local_1c;
    sub_0043F770(param_2,&local_c);
    local_c = -local_24;
    fStack_8 = -local_20;
    fStack_4 = -local_1c;
    fVar1 = GH_FROUND(fVar1 * fVar9);
    local_18 = fVar1 * local_c;
    fStack_14 = fStack_8 * fVar1;
    fStack_10 = fVar1 * fStack_4;
    uVar2 = sub_0043F770(param_1,&local_18);
    return CONCAT31((undefined4)((uint)uVar2 >> 8),1);
  }
  iVar5 = sub_0043F710((int)param_1);
  iVar6 = sub_0043F710((int)param_2);
  if (iVar6 < iVar5) {
    uVar2 = sub_0043F770(param_2,&local_24);
    return CONCAT31((undefined4)((uint)uVar2 >> 8),1);
  }
  iVar5 = sub_0043F710((int)param_1);
  iVar6 = sub_0043F710((int)param_2);
  if (iVar5 < iVar6) {
    local_c = G_00608088 - local_24;
    fStack_8 = G_00608088 - local_20;
    fStack_4 = G_00608088 - local_1c;
    iVar6 = sub_0043F770(param_1,&local_c);
  }
  return CONCAT31((undefined4)((uint)iVar6 >> 8),1);
}
