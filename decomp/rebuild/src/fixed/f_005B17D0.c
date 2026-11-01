#include "auto_pre.h"
DECOMP_C undefined4 __cdecl sub_005AD9F0(float *p0, float *p1, float *p2);
/* x87 'ja' after 'fcomi': the guard is true on unordered, so !(a > b), not a <= b */
DECOMP(005B17D0)
void __cdecl f_005B17D0(undefined4 *param_1, float *param_2, float *param_3)
{
  float fVar1;
  float fVar2;
  float *pfVar3;
  float *pfVar4;
  float *pfVar5;
  float *pfVar6;
  float *pfVar7;
  float *pfVar8;

  pfVar3 = param_2 + (((int)param_3 - (int)param_2 >> 3) - ((int)param_3 - (int)param_2 >> 0x1f) >>
                     1) * 2;
  sub_005AD9F0(param_2,pfVar3,param_3 + -2);
  pfVar6 = pfVar3 + 2;
  for (; param_2 < pfVar3; pfVar3 = pfVar3 + -2) {
    if ((pfVar3[-2] < *pfVar3) || (*pfVar3 < pfVar3[-2])) break;
  }
  pfVar7 = pfVar6;
  pfVar4 = pfVar3;
  if (pfVar6 < param_3) {
    do {
      pfVar7 = pfVar6;
      if ((*pfVar6 < *pfVar3) || (*pfVar3 < *pfVar6)) break;
      pfVar6 = pfVar6 + 2;
      pfVar7 = pfVar6;
    } while (pfVar6 < param_3);
  }
joined_r0x005b185c:
  do {
    pfVar5 = pfVar3;
    if (param_3 <= pfVar6) {
joined_r0x005b18a6:
      for (; param_2 < pfVar3; pfVar3 = pfVar3 + -2) {
        pfVar8 = pfVar5 + -2;
        if (!(*pfVar4 > *pfVar8)) {
          if (*pfVar4 < *pfVar8) break;
          fVar1 = pfVar4[-1];
          fVar2 = pfVar4[-2];
          pfVar4[-2] = *pfVar8;
          pfVar4[-1] = pfVar5[-1];
          *pfVar8 = fVar2;
          pfVar5[-1] = fVar1;
          pfVar4 = pfVar4 + -2;
        }
        pfVar5 = pfVar8;
      }
      if (pfVar3 == param_2) {
        if (pfVar6 == param_3) {
          param_1[1] = pfVar7;
          *param_1 = pfVar4;
          return;
        }
        if (pfVar7 != pfVar6) {
          fVar1 = *pfVar4;
          fVar2 = pfVar4[1];
          *pfVar4 = *pfVar7;
          pfVar4[1] = pfVar7[1];
          *pfVar7 = fVar1;
          pfVar7[1] = fVar2;
        }
        fVar1 = *pfVar4;
        fVar2 = pfVar4[1];
        *pfVar4 = *pfVar6;
        pfVar4[1] = pfVar6[1];
        *pfVar6 = fVar1;
        pfVar6[1] = fVar2;
        pfVar6 = pfVar6 + 2;
        pfVar7 = pfVar7 + 2;
        pfVar4 = pfVar4 + 2;
      }
      else {
        pfVar5 = pfVar3 + -2;
        if (pfVar6 == param_3) {
          pfVar8 = pfVar4 + -2;
          if (pfVar5 != pfVar8) {
            fVar1 = *pfVar5;
            fVar2 = pfVar3[-1];
            *pfVar5 = *pfVar8;
            pfVar3[-1] = pfVar4[-1];
            *pfVar8 = fVar1;
            pfVar4[-1] = fVar2;
          }
          fVar1 = *pfVar8;
          fVar2 = pfVar4[-1];
          *pfVar8 = pfVar7[-2];
          pfVar4[-1] = pfVar7[-1];
          pfVar7[-2] = fVar1;
          pfVar7[-1] = fVar2;
          pfVar7 = pfVar7 + -2;
          pfVar3 = pfVar5;
          pfVar4 = pfVar8;
        }
        else {
          fVar1 = pfVar6[1];
          fVar2 = *pfVar6;
          *pfVar6 = *pfVar5;
          pfVar6[1] = pfVar3[-1];
          pfVar6 = pfVar6 + 2;
          *pfVar5 = fVar2;
          pfVar3[-1] = fVar1;
          pfVar3 = pfVar5;
        }
      }
      goto joined_r0x005b185c;
    }
    if (!(*pfVar6 > *pfVar4)) {
      if (*pfVar6 < *pfVar4) goto joined_r0x005b18a6;
      fVar1 = pfVar7[1];
      fVar2 = *pfVar7;
      *pfVar7 = *pfVar6;
      pfVar7[1] = pfVar6[1];
      pfVar7 = pfVar7 + 2;
      *pfVar6 = fVar2;
      pfVar6[1] = fVar1;
    }
    pfVar6 = pfVar6 + 2;
  } while( true );
}
