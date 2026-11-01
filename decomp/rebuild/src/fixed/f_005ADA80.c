#include "auto_pre.h"
/* @func 005ADA80 custom */
DECOMP(005ADA80)
void __cdecl f_005ADA80(undefined4 in_eax, float *param_2, float *param_3, undefined4 param_4)
{
  float fVar1;
  float fVar2;
  float *pfVar3;
  float *pfVar4;

  if (param_2 != param_3) {
    for (pfVar4 = param_2 + 2; pfVar4 != param_3; pfVar4 = pfVar4 + 2) {
      fVar1 = *pfVar4;
      fVar2 = pfVar4[1];
      pfVar3 = pfVar4;
      if (!(*param_2 > fVar1)) {
        while (fVar1 < pfVar3[-2]) {
          *pfVar3 = pfVar3[-2];
          pfVar3[1] = pfVar3[-1];
          pfVar3 = pfVar3 + -2;
        }
        *pfVar3 = fVar1;
        pfVar3[1] = fVar2;
      }
      else {
        for (; param_2 != pfVar3; pfVar3 = pfVar3 + -2) {
          *pfVar3 = pfVar3[-2];
          pfVar3[1] = pfVar3[-1];
        }
        *param_2 = fVar1;
        param_2[1] = fVar2;
      }
    }
  }
  return;
}
