/* 0x0043BE40: pick the point where two 2D segments cross (p[i] = 2 points of 2 floats each), or reject.
 * r = 480410(p1, p2, &s1): 0/1 is returned as is, s1 is the crossing parameter along segment 1.
 * a = |p1[2..3]-p1[0..1]| (float); reject when -1e-12*a > s1 or s1 > 1 + a*1e-12 (eps is the double
 * constant 1e-12, products stay in extended precision, and a*1e-12 is kept as the rounded double D for the
 * later tests).  Then 480410(p2, p1, &s2) (status ignored) and b = |p2[0..1]-p2[2..3]|: reject unless
 * b-1e-12 <= s2 <= 1+b*1e-12.  b*1e-12 < s2 (x87 jb) picks the branch that returns a point:
 *   s2 < 1-b*1e-12      -> D < s1 ? (s1 < 1-D ? lerp(p2, s2) : p1[2..3]) : p1[0..1]
 *   otherwise           -> p2[2..3]
 * and the other side of b*1e-12 < s2 gives p2[0..1].  The x87 `jb` (CF) treats unordered as less, and the
 * sums/differences (1+a*1e-12, b-1e-12, 1-b*1e-12, 1-D) are unrounded extended values. */
/* @conv - 0 */
#include "auto_pre.h"

DECOMP_C int __thiscall sub_00480410(float *this, float *arg1, float *arg2);
DECOMP_C float *__thiscall sub_0047F390(float *this, float *out, float *param_3);
DECOMP_C float __thiscall sub_0047FB90(float *this);
DECOMP_C float *__thiscall sub_0047F980(float *this, float *out, float param_3);

DECOMP(0043BE40)
int __cdecl f_0043BE40(float *param_1, float *param_2, float *param_3)
{
    float tmp[2], pt[2];
    volatile float s1, s2, a, b;
    volatile double D;
    int r = sub_00480410(param_1, param_2, (float *)&s1);

    if (r == 0 || r == 1)
        return r;
    sub_0047F390(param_1 + 2, tmp, param_1);
    a = sub_0047FB90(tmp);
    if (-1e-12 * (double)a > (double)s1)
        return 4;
    if ((double)s1 > 1.0 + (double)a * 1e-12)
        return 4;
    D = (double)a * 1e-12;
    sub_00480410(param_2, param_1, (float *)&s2);
    sub_0047F390(param_2, tmp, param_2 + 2);
    b = sub_0047FB90(tmp);
    if (!((double)s2 >= (double)b - 1e-12))
        return 4;
    if (!(1.0 + (double)b * 1e-12 >= (double)s2))
        return 4;
    if (!((double)b * 1e-12 >= (double)s2)) {
        if (!((double)s2 >= 1.0 - (double)b * 1e-12)) {
            if (!(D >= (double)s1)) {
                if (!((double)s1 >= 1.0 - D)) {
                    sub_0047F980(param_2, pt, s2);
                    param_3[0] = pt[0];
                    param_3[1] = pt[1];
                    return 3;
                }
                param_3[0] = param_1[2];
                param_3[1] = param_1[3];
                return 3;
            }
            param_3[0] = param_1[0];
            param_3[1] = param_1[1];
            return 3;
        }
        param_3[0] = param_2[2];
        param_3[1] = param_2[3];
        return 3;
    }
    param_3[0] = param_2[0];
    param_3[1] = param_2[1];
    return 3;
}
