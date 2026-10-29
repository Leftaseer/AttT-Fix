/* 0x0054EC00: NParticleSystem::COriginFilledCircle::vf1 (desc, out): as COriginCircle (0x0054EC00), but the point's
 * distance from the centre is random: radius (+0x18) times K (0x0068AE10), times rand() / RAND_MAX, over K */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_00433620(void);
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C void *__stdcall sub_005B80DA(void *out, const float *light, const float *plane);    /* D3DXMatrixShadow */
DECOMP_C void *__stdcall sub_005B8056(void *out, const float *axis, float angle);            /* D3DXMatrixRotationAxis */
DECOMP_C void *__stdcall sub_005B8020(void *out, const void *a, const void *b);              /* D3DXMatrixMultiply */
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C float *__stdcall sub_005B8074(float *out, const float *v);                  /* D3DXVec3Normalize */
DECOMP_C char d_00614F80[], d_0068AE28[], d_0068AE10[], d_0068AE40[], d_0061B560[];
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
typedef unsigned int *(__thiscall *pos_54EC00)(void *ctx, void *out, void *d);
typedef char (__thiscall *flag_54EC00)(void *ctx, void *d);

#define VEC(p, out) ((pos_54EC00)((void **)(p))[3])(((void **)(p))[5], out, p)
#define RM (*(double *)d_0068AE28)
#define K (*(double *)d_0068AE10)

static float rnd_54EC00(void)
{
    int r = imp_00607400();
    return (float)(r * *(double *)d_00614F80 / RM - K);
}

DECOMP(0054EC00)
unsigned int __thiscall f_0054EC00(void *this, char *o, float *out, unsigned int unused)
{
    char *s = (char *)this, *e, *d;
    unsigned int tmp[3], *v;
    float p[3], f1, f2, f3, ang, sc;
    float m1[16], m2[16];
    double h;
    v = VEC(o + 0x2cc, tmp);
    ((unsigned int *)p)[0] = v[0];
    ((unsigned int *)p)[1] = v[1];
    ((unsigned int *)p)[2] = v[2];
    f1 = rnd_54EC00();
    f2 = rnd_54EC00();
    f3 = rnd_54EC00();
    out[0] = f3;
    out[1] = f2;
    out[2] = f1;
    if (*(char **)(s + 0x28) != o) {
        float light[4], plane[4];
        light[0] = p[0]; light[1] = p[1]; light[2] = p[2]; light[3] = *(float *)d_0068AE40;
        plane[0] = p[0]; plane[1] = p[1]; plane[2] = p[2]; plane[3] = 0;
        sub_005B80DA(s + 0x2c, light, plane);
        *(char **)(s + 0x28) = o;
    }
    {
        int r = imp_00607400();
        ang = (float)(r * (*(double *)d_0061B560 - 0.0) / RM + 0.0);
        ang = (float)(ang / K);
    }
    sub_005B8056(m1, p, ang);
    sub_005B8020(m2, s + 0x2c, m1);
    sub_005B8026(out, out, m2);
    sub_005B8074(out, out);
    sc = (float)(*(float *)(s + 0x18) * K);
    {
        int r = imp_00607400();
        sc = (float)(r * (sc - 0.0) / RM + 0.0);
        sc = (float)(sc / K);
    }
    out[0] = sc * out[0];
    out[1] = sc * out[1];
    out[2] = sc * out[2];
    e = *(char **)(s + 0x28);
    d = o + 0x584;
    if (((flag_54EC00)*(void **)(e + 0x5b0))(*(void **)(e + 0x5b8), e + 0x5ac)) {
        unsigned int a[3], b[3];
        v = VEC(d, tmp);
        out[0] = out[0] + ((float *)v)[0];
        out[1] = ((float *)v)[1] + out[1];
        out[2] = out[2] + ((float *)v)[2];
        v = VEC(d, tmp);
        a[0] = v[0]; a[1] = v[1]; a[2] = v[2];
        v = VEC(d, tmp);
        b[0] = v[0]; b[1] = v[1]; b[2] = v[2];
        h = sub_00473110(sub_00433620(), out[0], out[2]);
        out[1] = (float)(h - sub_00473110(sub_00433620(), ((float *)b)[0], ((float *)a)[2]) + out[1]);
        return (unsigned int)v;
    }
    v = VEC(d, tmp);
    out[0] = out[0] + ((float *)v)[0];
    out[1] = ((float *)v)[1] + out[1];
    out[2] = out[2] + ((float *)v)[2];
    return (unsigned int)v;
}
