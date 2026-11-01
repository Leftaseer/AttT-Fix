/* 0x00463E20: sqrt(x) of a screen-space ratio: S = (dy1^2 + dz1^2) scaled by tan(angle/2)^2 divided by the
 * squared horizontal spread of the box, times 4; the x87 code rounds S, tan(angle)^2, their product, the
 * spread and the quotient to float (each is stored to a stack slot) before the CRT square root, and the caller
 * only uses the ftol2 result. The generated form kept all intermediates extended. */
/* @conv - 0 */
#include "auto_pre.h"

DECOMP_C char d_00607CE0[], d_00608528[], d_00609B68[];
DECOMP_C double decomp_CIsqrt(double), decomp_CItan(double);
DECOMP_C undefined4 __stdcall sub_00424E70(void);

DECOMP(00463E20)
ulonglong __cdecl f_00463E20(float *param_1, float *param_2, float *param_3)
{
    volatile float dx, dy, dz;
    volatile float t1, t2, t3;
    volatile float a, b;
    volatile float ang, tanv, S, T2, X, sum, q, r;
    undefined4 o;

    dx = *(float *)((int)param_2 + 0x54) - param_2[0];
    dy = *(float *)((int)param_2 + 0x58) - param_2[1];
    dz = *(float *)((int)param_2 + 0x5c) - param_2[2];
    t1 = param_3[0] * dx;
    t2 = param_3[1] * dy;
    t3 = param_3[2] * dz;

    o = sub_00424E70();
    a = *(float *)(o + 0x44) - param_1[0];
    b = *(float *)(o + 0x4c) - param_1[2];
    o = sub_00424E70();
    ang = *(float *)(o + 0x74) * *(double *)d_00607CE0 * *(double *)d_00608528;
    tanv = (float)decomp_CItan(ang);

    S = a * a + b * b;
    T2 = tanv * tanv;
    X = S * T2;
    sum = (t1 * t1 + t2 * t2) + t3 * t3;
    q = X / (sum * *(double *)d_00609B68);
    r = (float)decomp_CIsqrt(q);
    return (ulonglong)(longlong)r;
}
