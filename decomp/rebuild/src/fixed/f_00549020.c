#include "auto_pre.h"
DECOMP_C double decomp_CIsqrt(double);
DECOMP_C char d_00607CE0[];
/* @func 00549020 */
#define sub_005E406A decomp_CIsqrt
#define GV_00607CE0_8 (*(double *)d_00607CE0)
DECOMP(00549020)
float __thiscall f_00549020(_CWorldUnit *this)
{
  float fVar1;
  float fVar2;
  float fVar3;
  float10 fVar4;
  
  fVar1 = GH_FROUND(this->field17_0x258 - this->field26_0x27c);
  fVar2 = GH_FROUND(this->field18_0x25c - this->field27_0x280);
  fVar3 = GH_FROUND(this->field19_0x260 - this->field28_0x284);
  fVar4 = sub_005E406A((float10)GH_FROUND(((fVar1 * fVar1 + fVar2 * fVar2) + fVar3 * fVar3)));
  { volatile float gh_ret = GH_FROUND((float)fVar4) * GV_00607CE0_8; return gh_ret; }
}
