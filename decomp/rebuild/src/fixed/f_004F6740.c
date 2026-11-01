#include "auto_pre.h"
DECOMP_C char d_0060A0D8[];
/* @func 004F6740 */
#define GV_0060A0D8_8 (*(double *)d_0060A0D8)
DECOMP(004F6740)
undefined4 __cdecl f_004F6740(float *param_1, float *param_2, float *param_3, float *param_4, float *param_5)
{
  float fVar1;
  float fVar2;
  float fVar3;
  float fVar4;
  float fVar5;
  float fVar6;
  float fVar7;
  float fVar8;
  float fVar9;
  float fVar10;
  float fVar11;
  undefined4 uVar13;
  float *pfVar12;
  double dVar12;
  float fVar13, fVar14, fVar15;
  
  fVar1 = *param_3;
  fVar3 = *param_4 - fVar1;
  fVar4 = param_4[1] - param_3[1];
  fVar6 = param_4[2] - param_3[2];
  fVar5 = param_5[1] - param_3[1];
  fVar7 = param_5[2] - param_3[2];
  fVar8 = (float)((double)fVar7 * param_2[1] - (double)fVar5 * param_2[2]);
  fVar2 = *param_2;
  fVar7 = (float)((double)(*param_5 - fVar1) * param_2[2] - (double)fVar2 * fVar7);
  fVar5 = (float)((double)fVar2 * fVar5 - (double)param_2[1] * (*param_5 - fVar1));
  /* the original sums the three products in x87 extended precision and rounds once */
  dVar12 = (double)fVar3 * fVar8 + (double)fVar4 * fVar7 + (double)fVar6 * fVar5;
  fVar9 = (float)dVar12;
  pfVar12 = param_5;
  if (0.0 < fVar9) {
    fVar1 = *param_1 - fVar1;
    fVar10 = param_1[1] - param_3[1];
    fVar11 = param_1[2] - param_3[2];
    uVar13 = (undefined4)((uint)param_1 >> 8);
    if (fVar9 < GV_0060A0D8_8) {
LLAB_004f687e:
      return (uint)uVar13 << 8;
    }
    dVar12 = (double)fVar11 * fVar5 + (double)fVar1 * fVar8 + (double)fVar10 * fVar7;
    fVar5 = (float)dVar12;
    pfVar12 = param_1;
    if (!(0.0 > fVar5)) {
      if (fVar9 < fVar5) goto LLAB_004f687e;
      fVar13 = (float)((double)fVar1 * fVar4 - (double)fVar3 * fVar10);
      fVar14 = (float)((double)fVar11 * fVar3 - (double)fVar1 * fVar6);
      fVar15 = (float)((double)fVar10 * fVar6 - (double)fVar11 * fVar4);
      dVar12 = (double)param_2[2] * fVar13 + (double)param_2[1] * fVar14 + (double)fVar2 * fVar15;
      fVar1 = (float)dVar12;
      if ((!(0.0 > fVar1)) && (!(fVar1 + fVar5 > fVar9))) {
        return CONCAT31(uVar13,1);
      }
    }
  }
  return (uint)pfVar12 & 0xffffff00;
}
