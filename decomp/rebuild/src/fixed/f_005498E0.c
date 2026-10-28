/* 0x005498E0: a world creature's Tick (a pet: EAX passes on as the result while it is frozen, +0x2FC): keeps the
 * time (vf80 at +0x300), the base tick (0x004AC690, its EAX input only passed through, approximated), then while
 * following (+0x318) turns (0x004ACB80, speed 10) to face away from the hero (0x00425F60, vf68; the angle of the
 * offset by 0x005202B0 times 0x00609628, normalised by 0x004F6470); otherwise around its home (+0x22C/+0x230): beyond
 * the radius (+0x234 squared) or too near its scarer (+0x308: 0x00547760 against its +0x70 squared) it flees
 * (0x005495D0), else turns away from home. It moves by the model's step (+0x1F8: 0x0042AAB0 at the speed +0x78,
 * scaled by +0x228, to 0x004ACAC0), animates (vf14, 0x004CB070 on +0x1FC) and, in view (0x00458120 on +0x258) with a
 * sound (+0x310), plays it (0x0043D8E0 on +0x314); returns what the original leaves in EAX */
/* @conv ECX,EAX 0 */
/* @func 005498E0 custom */
#include "auto_pre.h"
DECOMP_C int __cdecl sub_004AC690(void *self, unsigned int eax);
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C double __cdecl sub_005202B0(float *v);
DECOMP_C void __cdecl sub_004F6470(float *angle);
DECOMP_C void __thiscall sub_004ACB80(void *self, float angle, int speed);
DECOMP_C void __thiscall sub_005495D0(void *self);
DECOMP_C float __thiscall sub_00547760(void *self, void *pos);
DECOMP_C float *__thiscall sub_0042AAB0(void *self, void *out, float speed);
DECOMP_C int __thiscall sub_004ACAC0(void *self, void *step);
DECOMP_C void __thiscall sub_004CB070(void *self);
DECOMP_C unsigned int __cdecl sub_00458120(void *self, void *eax, void *pos);
DECOMP_C unsigned int __thiscall sub_0043D8E0(void *self, void *snd);
DECOMP_C char d_00609628[], d_006CA2C8[];
typedef double (__thiscall *vft_5498E0)(void *self);
typedef float *(__thiscall *vfp_5498E0)(void *self);
typedef void (__thiscall *vf_5498E0)(void *self);

static void face_5498E0(char *s, float *d)
{
    float a = (float)(sub_005202B0(d) * *(double *)d_00609628);
    sub_004F6470(&a);
    sub_004ACB80(s, a, 10);
}

DECOMP(005498E0)
unsigned int __cdecl f_005498E0(void *this, unsigned int eax)
{
    char *s = (char *)this;
    float d[2], x, z, r, v, step[2], k, *p;
    void **o1, **o2;
    char *m;
    unsigned int res;
    if (s[0x2fc])
        return eax;
    *(float *)(s + 0x300) = (float)((vft_5498E0)(*(void ***)this)[0x80 / 4])(this);
    sub_004AC690(this, eax);
    if (s[0x318]) {
        o1 = (void **)sub_00425F60();
        o2 = (void **)sub_00425F60();
        x = ((vfp_5498E0)(*(void ***)o2)[0x68 / 4])(o2)[0];
        z = ((vfp_5498E0)(*(void ***)o1)[0x68 / 4])(o1)[2];
        d[0] = *(float *)(s + 0x64) - x;
        d[1] = *(float *)(s + 0x6c) - z;
        face_5498E0(s, d);
    } else {
        d[0] = *(float *)(s + 0x64) - *(float *)(s + 0x22c);
        d[1] = *(float *)(s + 0x6c) - *(float *)(s + 0x230);
        r = d[0] * d[0] + d[1] * d[1];
        if (*(float *)(s + 0x234) > r)
            sub_005495D0(this);
        else {
            m = *(char **)(s + 0x308);
            v = *(float *)(m + 0x70);
            r = sub_00547760(m, s + 0x64);
            k = v * v;
            if (r > k)
                sub_005495D0(this);
            else
                face_5498E0(s, d);
        }
    }
    k = *(float *)(s + 0x228);
    p = sub_0042AAB0(*(void **)(s + 0x1f8), step, *(float *)(s + 0x78));
    {
        float st[2];
        float y = p[1] * k;
        st[0] = k * p[0];
        st[1] = y;
        sub_004ACAC0(this, st);
    }
    o1 = *(void ***)(s + 0x1f8);
    ((vf_5498E0)(*(void ***)o1)[0x14 / 4])(o1);
    sub_004CB070(*(void **)(s + 0x1fc));
    res = sub_00458120(*(void **)d_006CA2C8, s + 0x258, s + 0x258);
    if (!(char)res)
        return res;
    if (!*(void **)(s + 0x310))
        return 0;
    return sub_0043D8E0(*(void **)(s + 0x314), *(void **)(s + 0x310));
}
