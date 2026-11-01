/* 0x0043FE30: direction from this (+0x3fc) to param_2 (+0x3fc), scaled by (sum of +0x410 - length + 0.011) /
 * length; the x87 code rounds each delta, the squared length, the square root and the scale to float and adds
 * the double 0.011 in extended precision, while the decompiler kept the deltas extended */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP_C char d_0060A248[];
DECOMP_C double decomp_CIsqrt(double);

DECOMP(0043FE30)
void __thiscall f_0043FE30(void *this, float *param_1, int param_2)
{
    volatile float dx = *(float *)(param_2 + 0x3fc) - *(float *)((int)this + 0x3fc);
    volatile float dy = *(float *)(param_2 + 0x400) - *(float *)((int)this + 0x400);
    volatile float dz = *(float *)(param_2 + 0x404) - *(float *)((int)this + 0x404);
    volatile float l2 = (dx * dx + dy * dy) + dz * dz;
    volatile float s = (float)decomp_CIsqrt(l2);
    volatile float f = (((*(float *)(param_2 + 0x410) + *(float *)((int)this + 0x410)) - s) +
                       *(double *)d_0060A248) / s;

    param_1[0] = dx * f;
    param_1[1] = dy * f;
    param_1[2] = dz * f;
}
