/* 0x004802D0: 2D line/ray intersection parameter of param_1[0..1] direction against the edge
 * param_1[2..3]-param_1[0..1]? No: n = (p1-p2, p0-p2) built against this[0..3]; returns 2 with *param_2 =
 * -n.(this-p) / n.dir, or, when n.dir is exactly zero, defers to 0x480020 and returns 1 unless it answers
 * outside {0,1}. All deltas, the numerator, the denominator and the quotient are rounded to float through
 * stack slots in the original (fucomi + lahf/jp means an unordered denominator takes the division path). */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP_C int __thiscall sub_00480020(void *, float *, float *);

DECOMP(004802D0)
undefined4 __thiscall f_004802D0(void *this, float *param_1, float *param_2)
{
    float *q = (float *)this;
    volatile float u, v, w, z, sum, da, db, D, out;
    float p0 = param_1[0], p1 = param_1[1], p2 = param_1[2], p3 = param_1[3];

    u = p3 - p1;
    v = p0 - p2;
    w = q[2] - q[0];
    z = q[3] - q[1];
    sum = z * v + w * u;
    if (sum == 0.0f) {
        int r = sub_00480020(this, param_1, param_1 + 2);
        return (r == 0 || r == 1) ? 1 : 0;
    }
    da = q[0] - p0;
    db = q[1] - p1;
    D = v * db + da * u;
    out = -D / sum;
    *param_2 = out;
    return 2;
}
