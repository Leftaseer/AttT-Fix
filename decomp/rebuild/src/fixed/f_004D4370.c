/* 0x004D4370: the centroid of a triangle - the sum of its three 32-byte vertices (indices param_2[0..2] into the
 * array at [this+0x3C]+4) times the double at 0x6121D0, written to param_1. The original keeps the sums in stack
 * temporaries: the sum of the first two vertices is rounded to float, the sum with the third is rounded to float
 * again, and only then multiplied by the double. The temporaries are volatile here so that clang keeps the same
 * rounding points (with plain floats the whole sum stays in an x87 register). */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C char d_006121D0[];

DECOMP(004D4370)
undefined4 __thiscall f_004D4370(void *this, float *param_1, ushort *param_2)
{
    int base = *(int *)(*(int *)((int)this + 0x3c) + 4);
    const float *v2 = (const float *)((unsigned int)param_2[2] * 0x20 + base);
    const float *v1 = (const float *)((unsigned int)param_2[1] * 0x20 + base);
    const float *v0 = (const float *)((unsigned int)param_2[0] * 0x20 + base);
    double k = *(double *)d_006121D0;
    volatile float sum01x = v0[0] + v1[0];
    volatile float sum01y = v0[1] + v1[1];
    volatile float sum01z = v0[2] + v1[2];
    volatile float sx = v2[0] + sum01x;
    volatile float sy = v2[1] + sum01y;
    volatile float sz = v2[2] + sum01z;

    param_1[0] = sx * k;
    param_1[1] = sy * k;
    param_1[2] = sz * k;
    return (undefined4)param_1;
}
