#include "auto_pre.h"
DECOMP_C double decomp_CIsqrt(double);
DECOMP_C char d_0060F710[], d_0060F714[], d_0060F718[], d_0060F720[], d_0060F728[], d_006092E8[];
/* @func 00485DD0 */
#define sub_005E406A decomp_CIsqrt
#define G_006092E8 (*(float *)d_006092E8)
#define G_0060F710 (*(float *)d_0060F710)
#define G_0060F714 (*(float *)d_0060F714)
#define G_0060F718 (*(float *)d_0060F718)
#define GV_0060F720_8 (*(double *)d_0060F720)
#define GV_0060F728_8 (*(double *)d_0060F728)
DECOMP(00485DD0)
undefined4 __fastcall f_00485DD0(int *param_1)
{
#define local_2c (*(float *)(gh_frame + 0))
#define local_28 (*(float *)(gh_frame + 4))
#define local_24 (*(float **)(gh_frame + 8))
#define local_1c (*(uint *)(gh_frame + 16))
#define local_18 (*(float *)(gh_frame + 20))
#define local_10 (*(float *)(gh_frame + 28))
  unsigned char gh_frame[44] __attribute__((aligned(16)));
  float *pfVar1;
  float fVar2;
  float fVar3;
  float fVar4;
  float fVar5;
  float fVar6;
  float fVar7;
  float fVar8;
  float fVar9;
  uint uVar10;
  float *pfVar11;
  float10 fVar12;
  float fVar13;
  
  fVar8 = BITCAST(float, (param_1[7]));
  pfVar11 = (float *)param_1[9];
  uVar10 = 0;
  local_24 = (float *)0x0;
  fVar9 = (BITCAST(float, (param_1[8])) - BITCAST(float, (param_1[8]))) * pfVar11[1] -
          (BITCAST(float, (param_1[6])) - BITCAST(float, (param_1[6]))) * *pfVar11;
  fVar2 = BITCAST(float, (param_1[7]));
  local_28 = G_0060F714;
  if ((short)param_1[2] != 0) {
    do {
      pfVar11 = (float *)(((uint)local_24 & 0xffff) * 0x10 + *param_1);
      local_2c = G_0060F710;
      local_18 = local_28;
      local_10 = local_28;
      if (*(ushort *)((int)param_1 + 10) != 0) {
        local_1c = (uint)*(ushort *)((int)param_1 + 10);
        do {
          pfVar1 = (float *)(param_1[1] + (uVar10 & 0xffff) * 0x14);
          if (pfVar1[4] < local_28) {
            local_28 = pfVar1[4];
          }
          if (local_2c < pfVar1[3]) {
            local_18 = *pfVar1;
            local_10 = pfVar1[2];
            local_2c = pfVar1[3];
          }
          uVar10 = uVar10 + 1;
          local_1c = local_1c - 1;
        } while (local_1c != 0);
      }
      fVar12 = sub_005E406A((float10)GH_FROUND(local_2c));
      fVar4 = G_0060F718;
      fVar3 = GH_FROUND((float)fVar12);
      if ((fVar3 == GV_0060F728_8) && (local_28 / fVar3 == GV_0060F720_8)) {
        *pfVar11 = 0.0;
        pfVar11[2] = 0.0;
        fVar13 = G_0060F714;
        pfVar11[1] = fVar4;
        pfVar11[3] = fVar13;
      }
      else {
        fVar4 = BITCAST(float, (param_1[7]));
        pfVar1 = (float *)(param_1[9] + ((uint)local_24 & 0xffff) * 8);
        fVar5 = BITCAST(float, (param_1[8]));
        fVar13 = pfVar1[1];
        fVar6 = BITCAST(float, (param_1[6]));
        fVar7 = *pfVar1;
        pfVar11[1] = G_006092E8;
        fVar5 = GH_FROUND((local_10 - fVar5) * fVar13 - (local_18 - fVar6) * fVar7);
        pfVar11[3] = fVar5;
        fVar13 = G_0060F714;
        fVar3 = GH_FROUND((GH_FROUND(GH_FROUND(fVar4 + GH_FROUND(local_28 / fVar3) * fVar3) - fVar4) -
                  (fVar8 - fVar2)) / (fVar5 - fVar9));
        *pfVar11 = fVar3;
        pfVar11[2] = (1.0 - fVar3) * fVar9;
      }
      pfVar11 = (float *)((int)local_24 + 1);
      local_28 = fVar13;
      local_24 = pfVar11;
    } while ((ushort)pfVar11 < *(ushort *)(param_1 + 2));
  }
  return pfVar11;
}
