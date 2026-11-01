/* 0x0054AF30: CParticle::update - positions the particle's box (0x4..0x18) and the per-axis scale
 * products (0x28..0x30, 0x34) from the emitter's sizes (0x1c..0x24) and centers (0x98..0xac), the ramp
 * parameters (0x3c..0x64) with the lifetime fraction d = param_3 - 0xbc, then floor()s d * 0x94 into the
 * word at 0x68 and adds the size/center interpolation at 0x6c/0x70/0x40/0x74.  Every intermediate in the
 * original is stored through a dword stack slot (fstp dword), so each product/sum below is rounded to
 * float before the next one; the decompiler's single expressions kept them in extended precision (1 ulp).
 * The final truncation is fistp dword (0x80000000 out of int range), not the 64-bit TRUNC the generated
 * code used; d is the rounded float, reloaded from its slot after floor() for the 0x74 term. */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

DECOMP_C double __cdecl sub_005E420E(double p0);
DECOMP_C char d_0068AE40[];

/* @func 0054AF30 custom */
DECOMP(0054AF30)
undefined4 __cdecl f_0054AF30(_NParticleSystem_CParticle *gh_arg0, uint gh_arg1, float gh_arg2)
{
    char *s = (char *)gh_arg0;
    uint in_eax = gh_arg1;
    float param_3 = gh_arg2;
    volatile float d, a, b, c, s3, s5, s4, P1, P2, P3, g1, g2, g3, F4, F5, F6, t, pu1, tmp;
    float m24, p3v;
    int iv;

    if (*(unsigned char *)(s + 0x38) == 0)
        return in_eax;
    d = param_3 - *(float *)(s + 0xbc);
    if (d >= *(float *)(s + 0x3c)) {
        *(unsigned char *)(s + 0x38) = 0;
        return in_eax;
    }

    a = *(float *)(s + 0x1c) * d;
    b = *(float *)(s + 0x20) * d;
    c = *(float *)(s + 0x24) * d;
    s3 = a * 0.5f;
    s5 = b * 0.5f;
    s4 = 0.5f * c;

    P1 = *(float *)(s + 0xa4) + s3;
    P2 = *(float *)(s + 0xa8) + s5;
    P3 = *(float *)(s + 0xac) + s4;
    g1 = P1 * d;
    g2 = P2 * d;
    g3 = P3 * d;

    *(float *)(s + 0x4) = g1 + *(float *)(s + 0x98);
    *(float *)(s + 0x8) = *(float *)(s + 0x9c) + g2;
    *(float *)(s + 0xc) = *(float *)(s + 0xa0) + g3;

    F4 = *(float *)(s + 0xa4) + s3;
    *(float *)(s + 0x10) = s3 + F4;
    F5 = *(float *)(s + 0xa8) + s5;
    *(float *)(s + 0x14) = s5 + F5;
    F6 = *(float *)(s + 0xac) + s4;
    *(float *)(s + 0x18) = s4 + F6;

    t = *(float *)(s + 0x3c) - d;
    m24 = *(float *)d_0068AE40;
    p3v = m24;
    if (t <= *(float *)(s + 0x48))
        m24 = *(float *)(s + 0x58) * t;
    if (t <= *(float *)(s + 0x4c))
        p3v = t * *(float *)(s + 0x5c);
    if (d < *(float *)(s + 0x50) && m24 == *(float *)d_0068AE40)
        *(float *)(s + 0x88) = *(float *)(s + 0x60) * d;
    if (d < *(float *)(s + 0x54) && p3v == *(float *)d_0068AE40)
        *(float *)(s + 0x8c) = *(float *)(s + 0x64) * d;

    *(float *)(s + 0x34) = *(float *)(s + 0xcc) * *(float *)(s + 0x8c) * p3v;
    pu1 = *(float *)(s + 0x88);
    *(float *)(s + 0x28) = *(float *)(s + 0xc0) * pu1 * m24;
    *(float *)(s + 0x2c) = *(float *)(s + 0xc4) * pu1 * m24;
    *(float *)(s + 0x30) = pu1 * *(float *)(s + 0xc8) * m24;

    iv = (int)sub_005E420E((double)GH_FROUND(d * *(float *)(s + 0x94)));
    *(unsigned short *)(s + 0x68) = (unsigned short)iv;
    in_eax = (uint)iv & 0xffffu;

    tmp = *(float *)(s + 0x40) * (*(float *)(s + 0x70) - *(float *)(s + 0x6c));
    *(float *)(s + 0x74) = *(float *)(s + 0x6c) + tmp * d;
    return in_eax;
}
