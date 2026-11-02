/* 0x004FCCB0: triangular-grid cell lookup, actual ABI (this, out_cell, x, z).
 * All three conversions call _ftol2_sse (0x5e3fa0): round to double, then
 * cvttsd2si to a SIGNED 32-bit result, even though the column is used as uint.
 * A C unsigned cast uses a wider conversion and changes overflow/NaN results.
 * SSE2 is enabled by the game CRT; use the same memory-operand instruction.
 * The typed output pointer and z float still occupy the same three stack dwords. */
#include "auto_pre.h"
DECOMP_C char d_00608B50[], d_0060A308[];
/* @func 004FCCB0 */
#define GV_00608B50_8 (*(double *)d_00608B50)
#define GV_0060A308_8 (*(double *)d_0060A308)
DECOMP(004FCCB0)
uint *__thiscall f_004FCCB0(void *this, uint *param_1, float param_2, float param_3)
{
  float fVar1;
  float fVar2;
  float fVar3;
  double fVar4;
  float *pfVar5;
  int iVar6;
  uint uVar7;
  uint uVar8;

  fVar2 = GH_FROUND(param_2 - *(float *)((int)this + 0x84));
  fVar3 = GH_FROUND(param_3 - *(float *)((int)this + 0x8c));
  fVar1 = *(float *)((int)this + 100);
  uVar8 = (uint)GH_FTOL32(fVar2 / (GV_00608B50_8 * fVar1));
  if (fVar2 < 0.0) {
    uVar8 = uVar8 - 1;
  }
  uVar7 = uVar8 & 0x80000001;
  if ((int)uVar7 < 0) {
    uVar7 = (uVar7 - 1 | 0xfffffffe) + 1;
  }
  if (uVar7 == 0) {
    iVar6 = GH_FTOL32(fVar3 / (*(float *)((int)this + 0x60) * GV_0060A308_8));
    if (fVar3 < 0.0) {
      iVar6 = iVar6 + -1;
    }
  }
  else {
    fVar3 = fVar3 - *(float *)((int)this + 0x60);
    iVar6 = GH_FTOL32(fVar3 / (*(float *)((int)this + 0x60) * GV_0060A308_8));
    if (fVar3 < 0.0) {
      iVar6 = iVar6 + -1;
    }
  }
  iVar6 = (*(int *)((int)this + 0x70) - iVar6) * (*(int *)((int)this + 0x6c) * 2 + 1) +
          *(int *)((int)this + 0x6c) + uVar8;
  pfVar5 = (float *)(iVar6 * 0x10 + *(int *)((int)this + 0x68));
  fVar2 = GH_FROUND(param_2 - *pfVar5);
  fVar3 = GH_FROUND(param_3 - pfVar5[1]);
  if ((0.0 <= (fVar2 * *(float *)((int)this + 0x60) * GV_0060A308_8) / fVar1 - fVar3) &&
     (fVar4 = *(float *)((int)this + 0x60) * GV_0060A308_8,
     fVar4 - (fVar3 + (fVar2 * fVar4) / fVar1) <= 0.0)) {
    if (uVar7 == 0) {
      *(int *)param_1 = iVar6 + 1;
      return param_1;
    }
    *(int *)param_1 = iVar6 + (1 - *(int *)((int)this + 0x80));
    return param_1;
  }
  if (*(float *)((int)this + 0x60) < fVar3) {
    iVar6 = iVar6 - *(int *)((int)this + 0x80);
  }
  *(int *)param_1 = iVar6;
  return param_1;
}
#undef GV_00608B50_8
#undef GV_0060A308_8
