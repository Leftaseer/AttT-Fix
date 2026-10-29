/* 0x00527ED0: CClouds::RenderShadowPass (out tilt, out heading): keeps the camera (0x006CA2C4, 0x00435550) and ends the
 * scene, then draws the clouds (+0x274, 0x004B6E70) into the shadow texture (+0x27C: its level 0 through the
 * RenderToSurface +0x2C0, cleared to opaque black) as the sun sees them: the camera looks at the centre of the cloud
 * tile (size +0x5C / +0x60, origin +0x70 / +0x78 of +0x218's +8) under it from 2000 along the light's (GetLight 0)
 * reversed direction, at least 1414.2135 high, through an orthographic window of three tiles (D3DXMatrixOrthoLH,
 * 0x00435610). The camera is restored (0x004354C0) and the scene begun again; out: the sun's |dy| / distance and
 * its heading atan2(dx, dz) in 0..2pi */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_00435550(void *self, void *out);
DECOMP_C void __thiscall sub_00435610(void *self, const void *m);
DECOMP_C void __thiscall sub_004B6E70(void *self);
DECOMP_C void __thiscall sub_004354C0(void *self, const void *m);
DECOMP_C float *__stdcall sub_005B8062(float *out, float w, float h, float zn, float zf);   /* D3DXMatrixOrthoLH */
DECOMP_C double decomp_CIsqrt(double), decomp_CIatan2(double y, double x);
DECOMP_C char d_006CA2C4[], d_006C8C10[], d_00607CE0[], d_00608088[], d_00614F80[], d_00614F78[], d_00614F70[],
    d_0068AE18[], d_0060ACC0[], d_006097E0[], d_006095F0[];
typedef int (__stdcall *dev0_527ED0)(void *dev);
typedef void *(__thiscall *tex_527ED0)(void *self);
typedef int (__stdcall *surf_527ED0)(void *tex, unsigned int level, void **out);
typedef int (__stdcall *begin_527ED0)(void *rts, void *surf, void *vp);
typedef int (__stdcall *end_527ED0)(void *rts, unsigned int filter);
typedef int (__stdcall *clear_527ED0)(void *dev, unsigned int n, void *r, unsigned int fl, unsigned int c, float z,
                                      unsigned int s);
typedef int (__stdcall *light_527ED0)(void *dev, unsigned int i, void *out);
typedef int (__stdcall *rel_527ED0)(void *o);
typedef void (__thiscall *upd_527ED0)(void *self, int a);
typedef void (__thiscall *vf_527ED0)(void *self);

#define VT(o) (*(void ***)(o))
#define CAM (*(char **)d_006CA2C4)
#define DEV (*(char **)d_006C8C10)
#define F(p, o) (*(float *)((char *)(p) + (o)))

DECOMP(00527ED0)
void __thiscall f_00527ED0(void *this, float *tilt, float *heading)
{
    char *s = (char *)this, *q, *t;
    unsigned int saved[0x44 / 4];
    float light[0x68 / 4], m[16], p0[3], e[3], l[3], d[3], cx, cz, w, len, ady, a;
    void *surf;
    int n;
    sub_00435550(CAM, saved);
    ((dev0_527ED0)VT(DEV)[0xa8 / 4])(DEV);
    t = *(char **)(s + 0x27c);
    t = (char *)((tex_527ED0)VT(t)[0x2c / 4])(t);
    ((surf_527ED0)VT(t)[0x48 / 4])(t, 0, &surf);
    t = *(char **)(s + 0x2c0);
    ((begin_527ED0)VT(t)[0x14 / 4])(t, surf, 0);
    ((clear_527ED0)VT(DEV)[0xac / 4])(DEV, 0, 0, 1, 0xff000000, 1.0f, 0);
    cx = F(CAM, 0x44);
    cz = F(CAM, 0x4c);
    q = *(char **)(*(char **)(s + 0x218) + 8);
    n = (int)(long long)((cx - F(q, 0x70)) / F(q, 0x5c));
    p0[0] = (float)(F(q, 0x70) + F(q, 0x5c) * (n + *(double *)d_00607CE0));
    p0[1] = 0.0f;
    n = (int)(long long)((F(q, 0x78) - cz) / F(q, 0x60));
    p0[2] = (float)(F(q, 0x78) - (n + *(double *)d_00607CE0) * F(q, 0x60));
    ((light_527ED0)VT(DEV)[0xd0 / 4])(DEV, 0, light);
    d[0] = -light[0x40 / 4];
    d[1] = *(float *)d_00608088 - light[0x44 / 4];
    d[2] = *(float *)d_00608088 - light[0x48 / 4];
    l[0] = (float)(d[0] * *(double *)d_00614F80);
    l[1] = (float)(d[1] * *(double *)d_00614F80);
    l[2] = (float)(*(double *)d_00614F80 * d[2]);
    if (*(double *)d_00614F78 > l[1])
        l[1] = *(float *)d_00614F70;
    e[0] = l[0] + p0[0];
    F(CAM, 0x50) = p0[0];
    F(CAM, 0x54) = p0[1];
    e[1] = (float)(l[1] + *(double *)d_0068AE18);
    F(CAM, 0x58) = p0[2];
    e[2] = l[2] + p0[2];
    F(CAM, 0x44) = e[0];
    F(CAM, 0x48) = e[1];
    F(CAM, 0x4c) = e[2];
    w = (float)(F(q, 0x60) * *(double *)d_0060ACC0);
    CAM[0x71] = 1;
    sub_005B8062(m, w, w, 1.0f, *(float *)d_006097E0);
    sub_00435610(CAM, m);
    CAM[0x211] = 0;
    F(CAM, 0x214) = 0;
    CAM[0x218] = 0;
    ((upd_527ED0)VT(CAM)[1])(CAM, 0);
    sub_004B6E70(*(void **)(s + 0x274));
    t = *(char **)(s + 0x2c0);
    ((end_527ED0)VT(t)[0x18 / 4])(t, 1);
    ((rel_527ED0)VT(surf)[2])(surf);
    ((dev0_527ED0)VT(DEV)[0xa4 / 4])(DEV);
    sub_004354C0(CAM, saved);
    t = CAM + 4;
    ((vf_527ED0)VT(t)[0x18 / 4])(t);
    d[0] = e[0] - p0[0];
    d[1] = (float)(e[1] - *(double *)d_0068AE18);
    d[2] = e[2] - p0[2];
    ady = __builtin_fabsf(d[1]);
    len = d[0] * d[0] + d[1] * d[1] + d[2] * d[2];
    len = (float)decomp_CIsqrt(len);
    *tilt = ady / len;
    a = (float)decomp_CIatan2(d[0], d[2]);
    if (0.0f > d[0])
        a = (float)(a + *(double *)d_006095F0);
    *heading = a;
}
