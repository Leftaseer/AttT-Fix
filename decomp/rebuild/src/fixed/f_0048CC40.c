/* 0x0048CC40: insertion sort of (x, y) float pairs by key = atan2(x, y) rounded to float. The two guards are x87
 * 'fcomip; jbe', and jbe is true when the comparison is unordered, so a NaN key goes down the scan-left path; the
 * generated C compared with '<=' (false on unordered) and inserted the NaN as a minimum instead */
#include "auto_pre.h"

DECOMP_C double decomp_CIatan2(double y, double x);

typedef struct {
    float x, y;
} vec2_0048CC40;

DECOMP(0048CC40)
void __cdecl f_0048CC40(vec2_0048CC40 *param_1, vec2_0048CC40 *param_2, int param_3)
{
    vec2_0048CC40 *pfVar3, *pfVar4;
    float fVar1, fVar2;
    float fVar5, fVar6;

    (void)param_3;
    if (param_1 == param_2)
        return;
    for (pfVar4 = param_1 + 1; pfVar4 != param_2; pfVar4++) {
        fVar1 = pfVar4->x;
        fVar2 = pfVar4->y;
        fVar5 = (float)decomp_CIatan2(pfVar4->x, pfVar4->y);
        fVar6 = (float)decomp_CIatan2(param_1->x, param_1->y);
        pfVar3 = pfVar4;
        if (!(fVar6 > fVar5)) {
            for (;;) {
                fVar6 = (float)decomp_CIatan2(pfVar3[-1].x, pfVar3[-1].y);
                if (!(fVar6 > fVar5))
                    break;
                *pfVar3 = pfVar3[-1];
                pfVar3--;
            }
            pfVar3->x = fVar1;
            pfVar3->y = fVar2;
        } else {
            for (; param_1 != pfVar3; pfVar3--)
                *pfVar3 = pfVar3[-1];
            param_1->x = fVar1;
            param_1->y = fVar2;
        }
    }
}
