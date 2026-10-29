/* 0x0042DC20: sets up a thrown projectile's arc (from x, y, z (args 1-3) to x, y, z (args 4-6), arg 7 at +0x1C, the
 * arc's curvature arg 8 at +0x00): keeps the ends (+0x04.., +0x10..) and the distance (+0x20, _CIsqrt), and builds
 * the arc's matrix (+0x24, from identity): the parabola y = x * x / 0x00608B40 * curvature over x from -distance / 2
 * is lifted to start at 0 (D3DXMatrixTranslation), pitched to the ends' slope (D3DXMatrixRotationZ by _CIatan2 of the
 * height over the horizontal distance), turned to their heading (D3DXMatrixRotationY by _CIatan2(-dz, dx)) and moved
 * so its start lands on the start (its transformed start point, D3DXVec3TransformCoord). Arg 7's term is multiplied
 * by 0x0068AE18 (0) */
/* @conv ECX 32 */
#include "auto_pre.h"
DECOMP_C float *__stdcall sub_005B803E(float *out, float x, float y, float z);        /* D3DXMatrixTranslation */
DECOMP_C float *__stdcall sub_005B8038(float *out, float a);                          /* D3DXMatrixRotationZ */
DECOMP_C float *__stdcall sub_005B8032(float *out, float a);                          /* D3DXMatrixRotationY */
DECOMP_C float *__stdcall sub_005B8020(float *out, const void *a, const void *b);     /* D3DXMatrixMultiply */
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);    /* D3DXVec3TransformCoord */
DECOMP_C double decomp_CIsqrt(double), decomp_CIatan2(double y, double x);
DECOMP_C char d_0068AE40[], d_0068AE18[], d_00607CE0[], d_00608B40[];

#define F(o) (*(float *)(s + (o)))

DECOMP(0042DC20)
void __thiscall f_0042DC20(void *this, float x0, float y0, float z0, float x1, float y1, float z1, float a7, float k)
{
    char *s = (char *)this;
    float *m = (float *)(s + 0x24), m2[16], dx, dy, dz, l2, h, y, hd, ang, v[3];
    double dx2, dz2;
    int i;
    F(4) = x0, F(8) = y0, F(0xc) = z0;
    F(0x10) = x1, F(0x14) = y1, F(0x18) = z1;
    F(0x1c) = a7;
    F(0) = k;
    dx = F(0x10) - F(4);
    dy = F(0x14) - F(8);
    dz = F(0x18) - F(0xc);
    dx2 = dx * dx;
    dz2 = dz * dz;
    l2 = (float)(dx2 + dy * dy + dz2);
    F(0x20) = (float)decomp_CIsqrt(l2);
    for (i = 0; i < 16; i++)
        m[i] = 0.0f;
    m[0] = m[5] = m[10] = m[15] = *(float *)d_0068AE40;
    h = (float)(F(0x1c) * *(double *)d_0068AE18 - F(0x20) * *(double *)d_00607CE0);
    y = (float)(h * h / *(double *)d_00608B40 * F(0));
    sub_005B803E(m2, 0.0f, -y, 0.0f);
    sub_005B8020(m, m, m2);
    hd = (float)decomp_CIsqrt((float)(dz2 + dx2));
    ang = (float)decomp_CIatan2(dy, hd);
    sub_005B8038(m2, ang);
    sub_005B8020(m, m, m2);
    ang = (float)decomp_CIatan2(-dz, dx);
    sub_005B8032(m2, ang);
    sub_005B8020(m, m, m2);
    h = (float)(F(0x1c) * *(double *)d_0068AE18 - F(0x20) * *(double *)d_00607CE0);
    v[0] = h;
    v[1] = (float)(h * h / *(double *)d_00608B40 * F(0));
    v[2] = 0.0f;
    sub_005B8026(v, v, m);
    sub_005B803E(m2, F(4) - v[0], F(8) - v[1], F(0xc) - v[2]);
    sub_005B8020(m, m, m2);
}
