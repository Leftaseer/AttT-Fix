/* 0x0054B8D0 (ECX = the particle system, arg = the particle to initialize, ret 4): sets one particle up from the
 * system's ranges.  The position +0x2CC is rotated by yaw/pitch/roll jitter (each uniform in -phase..+phase, with
 * phase = +0x23C, over rand()/32767.0 and divided by 1000.0 for radians; the range is built from [0x608088] =
 * -0.0f minus the phase) through D3DXMatrixRotationYawPitchRoll (0x005B802C) and D3DXVec3TransformCoord
 * (0x005B8026), then scaled by a random factor in +0x2FC..+0x30C.  Five more random ranges, each rounded to a
 * float before use, are +0x3B8..+0x3C8, +0x338..+0x348, +0x358..+0x368, +0x378..+0x388 and +0x398..+0x3A8.
 * A lifetime is drawn between 1000*[+0x450] and 1000*[+0x460] milliseconds and divided by 1000; scaling it by
 * +0x430 and +0x440 gives the last two arguments.  The provider at +0x59C (slot +0x04, thiscall with
 * (this, &out, &pos)) fills a 12-byte vector that 0x0054B2D0 writes to the particle together with the position,
 * the scale triple [+0x3F0]*([+0x3D8], [+0x3DC], [+0x3E0]), the four dwords at +0x31C, the five ranges, the
 * current time +0x5E4, the u16 at +0x4D0 and the two lifetime values.  All arithmetic is x87 extended precision
 * rounded to a float wherever the original stores a dword. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
DECOMP_C char d_0068AE10[], d_0068AE28[];
DECOMP_C void *__stdcall sub_005B802C(float *m, float yaw, float pitch, float roll);  /* D3DXMatrixRotationYawPitchRoll */
DECOMP_C void *__stdcall sub_005B8026(float *v, const float *in, const float *m);     /* D3DXVec3TransformCoord */
DECOMP_C void __thiscall sub_0054B2D0(void *self, unsigned int *p1, unsigned int *p2, unsigned int *p3,
                                      unsigned int *p4, float f5, float f6, float f7, float f8, float f9,
                                      float f10, unsigned short u11, float f12, float f13);

typedef void (__thiscall *provider_54B8D0)(void *self, void *owner, void *out, void *vec);

#define F_54B8D0(o) (*(float *)(s + (o)))
#define RAND_MAX_54B8D0 (*(double *)d_0068AE28)
#define JITTER_54B8D0(lo, hi) ((lo) + ((double)(hi) - (double)(lo)) * (double)imp_00607400() / RAND_MAX_54B8D0)

DECOMP(0054B8D0)
void __thiscall f_0054B8D0(void *this, void *particle)
{
    char *s = (char *)this;
    void *provider = *(void **)(s + 0x59c);
    float phase = F_54B8D0(0x23c), m[16], v[3], sc[3];
    float j, j1s, j2s, j3s, k, j5, j6, j7, j8, j9, sec, r430, r440, a;
    unsigned int out[3];

    v[0] = F_54B8D0(0x2cc);
    v[1] = F_54B8D0(0x2d0);
    v[2] = F_54B8D0(0x2d4);
    j = (float)JITTER_54B8D0(-phase, phase);
    j1s = (float)((double)j / 1000.0);
    j = (float)JITTER_54B8D0(-phase, phase);
    j2s = (float)((double)j / 1000.0);
    j = (float)JITTER_54B8D0(-phase, phase);
    j3s = (float)((double)j / 1000.0);
    sub_005B802C(m, j1s, j2s, j3s);
    sub_005B8026(v, v, m);
    k = (float)JITTER_54B8D0(F_54B8D0(0x2fc), F_54B8D0(0x30c));
    v[0] = (float)((double)v[0] * (double)k);
    v[1] = (float)((double)v[1] * (double)k);
    v[2] = (float)((double)v[2] * (double)k);
    j5 = (float)JITTER_54B8D0(F_54B8D0(0x3b8), F_54B8D0(0x3c8));
    j6 = (float)JITTER_54B8D0(F_54B8D0(0x338), F_54B8D0(0x348));
    j7 = (float)JITTER_54B8D0(F_54B8D0(0x358), F_54B8D0(0x368));
    j8 = (float)JITTER_54B8D0(F_54B8D0(0x378), F_54B8D0(0x388));
    j9 = (float)JITTER_54B8D0(F_54B8D0(0x398), F_54B8D0(0x3a8));
    {
        float d = F_54B8D0(0x450);
        float lo = (float)((double)d * (*(double *)d_0068AE10));
        float hi = (float)((*(double *)d_0068AE10) * (double)F_54B8D0(0x460));
        j = (float)JITTER_54B8D0(lo, hi);
        sec = (float)((double)j / (*(double *)d_0068AE10));
    }
    r430 = (float)((double)F_54B8D0(0x430) * (double)sec);
    r440 = (float)((double)sec * (double)F_54B8D0(0x440));
    ((provider_54B8D0)(*(void ***)provider)[0x04 / 4])(provider, this, out, v);
    a = F_54B8D0(0x3f0);
    sc[0] = (float)((double)a * (double)F_54B8D0(0x3d8));
    sc[1] = (float)((double)F_54B8D0(0x3dc) * (double)a);
    sc[2] = (float)((double)a * (double)F_54B8D0(0x3e0));
    sub_0054B2D0(particle, out, (unsigned int *)v, (unsigned int *)sc, (unsigned int *)(s + 0x31c),
                 j5, j6, j7, j8, j9, F_54B8D0(0x5e4), *(unsigned short *)(s + 0x4d0), r430, r440);
}
