/* 0x0048C980: quicksort partition (Bentley-McIlroy, equal elements to the edges) of (x, y) float pairs by
 * key = atan2(x, y) rounded to float. The original tests a pair of keys with two x87 'fcomi; ja' guards:
 * greater going one way, greater the other way, and anything else (equal, or unordered because a key is NaN)
 * counts as equal. The generated C wrote that as 'a <= b' (false on unordered), so NaN keys skipped the
 * equal-element swaps; the guards are '!(a > b)' here instead */
#include "auto_pre.h"

DECOMP_C double decomp_CIatan2(double y, double x);
DECOMP_C undefined4 __cdecl sub_0048C610(undefined4 *p0, undefined4 *p1, undefined4 *p2);

DECOMP(0048C980)
void __cdecl f_0048C980(undefined4 *param_1, undefined4 *param_2, undefined4 *param_3)
{
#define local_18 (*(float **)(gh_frame + 0))
  unsigned char gh_frame[24] __attribute__((aligned(16)));
  float fVar1;
  float fVar2;
  float *pfVar3;
  float *pfVar4;
  float *pfVar5;
  float *pfVar6;
  float *pfVar7;
  float *pfVar8;
  float *pfVar9;
  float10 fVar10;
  float10 fVar11;

  pfVar7 = (float *)(param_2 +
                    (((int)param_3 - (int)param_2 >> 3) - ((int)param_3 - (int)param_2 >> 0x1f) >> 1
                    ) * 2);
  sub_0048C610(param_2,pfVar7,param_3 + -2);
  pfVar5 = pfVar7 + 2;
  if (param_2 < pfVar7) {
    local_18 = pfVar7 + -1;
    do {
      fVar10 = decomp_CIatan2((float10)GH_FROUND(pfVar7[-2]),GH_FROUND((float10)*local_18));
      fVar11 = decomp_CIatan2((float10)GH_FROUND(*pfVar7),GH_FROUND((float10)pfVar7[1]));
      if (((float)fVar10 < (float)fVar11) || ((float)fVar11 < (float)fVar10)) break;
      local_18 = local_18 + -2;
      pfVar7 = pfVar7 + -2;
    } while (param_2 < pfVar7);
  }
  pfVar3 = pfVar5;
  local_18 = pfVar7;
  pfVar8 = pfVar7;
  if (pfVar5 < param_3) {
    fVar10 = decomp_CIatan2((float10)GH_FROUND(*pfVar7),GH_FROUND((float10)pfVar7[1]));
    do {
      fVar11 = decomp_CIatan2((float10)GH_FROUND(*pfVar5),GH_FROUND((float10)pfVar5[1]));
      pfVar3 = pfVar5;
      if (((float)fVar11 < (float)fVar10) || ((float)fVar10 < (float)fVar11)) break;
      pfVar5 = pfVar5 + 2;
      pfVar3 = pfVar5;
    } while (pfVar5 < param_3);
  }
joined_r0x0048ca59:
  do {
    pfVar9 = pfVar7;
    if (param_3 <= pfVar3) {
joined_r0x0048cac2:
      while (pfVar4 = pfVar7, param_2 < pfVar7) {
        pfVar6 = pfVar9 + -2;
        fVar10 = decomp_CIatan2((float10)GH_FROUND(*pfVar6),GH_FROUND((float10)pfVar9[-1]));
        fVar11 = decomp_CIatan2((float10)GH_FROUND(*pfVar8),GH_FROUND((float10)pfVar8[1]));
        if (!((float)fVar11 > (float)fVar10)) {
          pfVar4 = local_18;
          if ((float)fVar11 < (float)fVar10) break;
          fVar1 = pfVar8[-2];
          fVar2 = pfVar8[-1];
          pfVar8[-2] = *pfVar6;
          pfVar8[-1] = pfVar9[-1];
          *pfVar6 = fVar1;
          pfVar9[-1] = fVar2;
          pfVar8 = pfVar8 + -2;
        }
        local_18 = local_18 + -2;
        pfVar9 = pfVar6;
        pfVar7 = local_18;
      }
      if (pfVar4 == (float *)param_2) {
        if (pfVar3 == (float *)param_3) {
          *param_1 = pfVar8;
          param_1[1] = pfVar5;
          return;
        }
        if (pfVar5 != pfVar3) {
          fVar1 = *pfVar8;
          fVar2 = pfVar8[1];
          *pfVar8 = *pfVar5;
          pfVar8[1] = pfVar5[1];
          *pfVar5 = fVar1;
          pfVar5[1] = fVar2;
        }
        fVar1 = *pfVar8;
        fVar2 = pfVar8[1];
        *pfVar8 = *pfVar3;
        pfVar8[1] = pfVar3[1];
        *pfVar3 = fVar1;
        pfVar3[1] = fVar2;
        pfVar7 = pfVar4;
        pfVar5 = pfVar5 + 2;
        pfVar3 = pfVar3 + 2;
        pfVar8 = pfVar8 + 2;
      }
      else {
        pfVar7 = pfVar4 + -2;
        local_18 = pfVar7;
        if (pfVar3 == (float *)param_3) {
          pfVar9 = pfVar8 + -2;
          if (pfVar7 != pfVar9) {
            fVar1 = *pfVar7;
            fVar2 = pfVar4[-1];
            *pfVar7 = *pfVar9;
            pfVar4[-1] = pfVar8[-1];
            *pfVar9 = fVar1;
            pfVar8[-1] = fVar2;
          }
          fVar1 = *pfVar9;
          fVar2 = pfVar8[-1];
          *pfVar9 = pfVar5[-2];
          pfVar8[-1] = pfVar5[-1];
          pfVar5[-2] = fVar1;
          pfVar5[-1] = fVar2;
          pfVar5 = pfVar5 + -2;
          pfVar8 = pfVar9;
        }
        else {
          fVar1 = pfVar3[1];
          fVar2 = *pfVar3;
          *pfVar3 = *pfVar7;
          pfVar3[1] = pfVar4[-1];
          *pfVar7 = fVar2;
          pfVar4[-1] = fVar1;
          pfVar3 = pfVar3 + 2;
        }
      }
      goto joined_r0x0048ca59;
    }
    fVar10 = decomp_CIatan2((float10)GH_FROUND(*pfVar8),GH_FROUND((float10)pfVar8[1]));
    fVar11 = decomp_CIatan2((float10)GH_FROUND(*pfVar3),GH_FROUND((float10)pfVar3[1]));
    pfVar7 = local_18;
    if (!((float)fVar11 > (float)fVar10)) {
      pfVar9 = local_18;
      if ((float)fVar11 < (float)fVar10) goto joined_r0x0048cac2;
      fVar1 = *pfVar5;
      fVar2 = pfVar5[1];
      *pfVar5 = *pfVar3;
      pfVar5[1] = pfVar3[1];
      pfVar5 = pfVar5 + 2;
      *pfVar3 = fVar1;
      pfVar3[1] = fVar2;
    }
    pfVar3 = pfVar3 + 2;
  } while( true );
}
