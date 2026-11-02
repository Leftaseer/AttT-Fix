/* 0x0043F260: shortest angular difference atan2(param_4, param_3) - atan2(param_2, param_1) as a float: above
 * pi one 2*pi is subtracted, below -pi one is added. Each step of the original stores and reloads the value
 * (fstps/flds), so every comparison and result is float-rounded; in the generated C clang kept the intermediates
 * in x87 registers and the extended values reached the result (case 3 of the sweep: -3.1385693550 against
 * -3.1385693009). The volatile floats below are that store/reload */
#include "auto_pre.h"

DECOMP_C double decomp_CIatan2(double y, double x);
DECOMP_C char d_0060A228[], d_006095F0[], d_0060A220[];

#define GV_0060A228_8 (*(double *)d_0060A228)
#define GV_006095F0_8 (*(double *)d_006095F0)
#define GV_0060A220_8 (*(double *)d_0060A220)

DECOMP(0043F260)
double __cdecl f_0043F260(float param_1, float param_2, float param_3, float param_4)
{
    volatile float fVar1, fVar2, fVar3;

    fVar2 = (float)decomp_CIatan2(param_4, param_3);
    fVar3 = (float)decomp_CIatan2(param_2, param_1);
    fVar1 = fVar2 - fVar3;
    while (GV_0060A228_8 < fVar1)
        fVar1 = fVar1 - GV_006095F0_8;
    while (fVar1 < GV_0060A220_8)
        fVar1 = fVar1 + GV_006095F0_8;
    return (double)fVar1;
}
