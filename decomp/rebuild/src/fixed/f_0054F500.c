/* 0x0054F500: a particle emitter's spawn (desc, out position, out velocity): the position is the desc's offset
 * (provider +0x2CC) turned by a random yaw / pitch / roll (rand over 0..0x0061B560 thousandths of a radian,
 * D3DXMatrixRotationYawPitchRoll, D3DXVec3TransformCoord), normalised and scaled by the emitter's radius (+0x18); the
 * velocity is its direction (D3DXVec3Normalize) times a random speed between providers +0x2FC and +0x30C, reversed
 * unless provider +0x4E0 says outward; the desc's origin (provider +0x584) is added to the position. The providers
 * call their function (+0x0C / +0x04) on their object (+0x14 / +0x0C) */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void *__stdcall sub_005B802C(void *out, float yaw, float pitch, float roll);   /* D3DXMatrixRotationYawPitchRoll */
DECOMP_C float *__stdcall sub_005B8026(float *out, const float *v, const void *m);   /* D3DXVec3TransformCoord */
DECOMP_C float *__stdcall sub_005B8074(float *out, const float *v);                  /* D3DXVec3Normalize */
DECOMP_C char d_0061B560[], d_0068AE18[], d_0068AE28[], d_0068AE10[], d_0061BA00[];
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
typedef unsigned int *(__thiscall *vec_54F500)(void *obj, void *out, void *self);
typedef float (__thiscall *num_54F500)(void *obj, void *self);
typedef char (__thiscall *flag_54F500)(void *obj, void *self);

#define VEC(p, out) ((vec_54F500)((void **)(p))[3])(((void **)(p))[5], out, p)
#define NUM(p) ((num_54F500)((void **)(p))[1])(((void **)(p))[3], p)
#define LO (*(double *)d_0068AE18)
#define RM (*(double *)d_0068AE28)
#define K (*(double *)d_0068AE10)

DECOMP(0054F500)
void __thiscall f_0054F500(void *this, char *desc, float *pos, float *vel)
{
    unsigned int tmp[3], *v;
    float m[16], a, b, c, ra, rb, sc, lo, hi, sp;
    double d;
    char *p;
    v = VEC(desc + 0x2cc, tmp);
    ((unsigned int *)pos)[0] = v[0];
    ((unsigned int *)pos)[1] = v[1];
    ((unsigned int *)pos)[2] = v[2];
    d = *(double *)d_0061B560 - LO;
    a = (float)((double)imp_00607400() * d / RM + LO);
    b = (float)((double)imp_00607400() * d / RM + LO);
    ra = (float)(a / K);
    rb = (float)(b / K);
    c = (float)((double)imp_00607400() * d / RM + LO);
    sub_005B802C(m, (float)(c / K), rb, ra);
    sub_005B8026(pos, pos, m);
    sub_005B8074(pos, pos);
    sc = *(float *)((char *)this + 0x18);
    pos[0] = pos[0] * sc;
    pos[1] = pos[1] * sc;
    pos[2] = sc * pos[2];
    ((unsigned int *)vel)[0] = ((unsigned int *)pos)[0];
    ((unsigned int *)vel)[1] = ((unsigned int *)pos)[1];
    ((unsigned int *)vel)[2] = ((unsigned int *)pos)[2];
    sub_005B8074(vel, vel);
    lo = NUM(desc + 0x30c);
    hi = NUM(desc + 0x2fc);
    sp = (float)(hi + (double)imp_00607400() * (lo - hi) / RM);
    vel[0] = vel[0] * sp;
    vel[1] = sp * vel[1];
    vel[2] = sp * vel[2];
    p = desc + 0x4e0;
    if (!((flag_54F500)((void **)p)[1])(((void **)p)[3], p)) {
        vel[0] = (float)(vel[0] * *(double *)d_0061BA00);
        vel[1] = (float)(vel[1] * *(double *)d_0061BA00);
        vel[2] = (float)(*(double *)d_0061BA00 * vel[2]);
    }
    v = VEC(desc + 0x584, tmp);
    {
        float t[3];
        ((unsigned int *)t)[0] = v[0];
        ((unsigned int *)t)[1] = v[1];
        ((unsigned int *)t)[2] = v[2];
        pos[0] = pos[0] + t[0];
        pos[1] = pos[1] + t[1];
        pos[2] = pos[2] + t[2];
    }
}
