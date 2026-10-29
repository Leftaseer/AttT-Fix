/* 0x004CFC30: the point of the plane through A (a1, a2, a3), B (a4, a5, a6) and C (a7, a8, a9) above p (x, z):
 * out = (p.x, y, p.z). The machine code's x87 order: every product and difference paired as the original pairs
 * them (single precision rounds each step; the doubles it spills to are exact) */
/* @conv - 44 */
#include "auto_pre.h"

DECOMP(004CFC30)
void __stdcall f_004CFC30(float *out, float a1, float a2, float a3, float a4, float a5, float a6, float a7, float a8,
                          float a9, const float *p)
{
    float px = p[0], pz = p[1];
    long double dx = (long double)px - a1, dz = (long double)pz - a3;
    long double ba1 = (long double)a4 - a1, ba2 = (long double)a5 - a2, ba3 = (long double)a6 - a3;
    long double ca1 = (long double)a7 - a1, ca2 = (long double)a8 - a2, ca3 = (long double)a9 - a3;
    long double num, den;
    out[0] = px;
    out[2] = pz;
    num = ba2 * ca1 * dz + dx * ca2 * ba3;
    num = num - dx * ba2 * ca3;
    num = num - dz * (ca2 * ba1);
    den = ba3 * ca1 - ca3 * ba1;
    out[1] = (float)(num / den + a2);
}
