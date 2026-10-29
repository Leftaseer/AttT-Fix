/* 0x00525070: AttackSphere's start (x, z, radius): keeps radius / x / z (+0x0C / +0x10 / +0x14), replaces its particle
 * system (+0x20, refcounted at +4: the old one is released through vf0(1)) with a new 0x690-byte one (0x00550420, empty
 * name) loaded from "AttackSphere.psp" (0x0054EA10), whose origin must be a COriginCircle (type 1, else it throws "the
 * particle system for AttackSphere must have a COriginCircle origin", AttackSphere.cpp:60); the system stands at
 * (x, terrain height (0x00473110 of 0x00433620), z) (provider +0x2E4) with its previous position its last one (+0x58 =
 * +0x64, +0x64 cleared, +0x70 set), the circle gets the radius (its provider +0x18), it is reset (0x0054FE30(0, 0) and
 * 0x0054D350 with 0x006149B4), its two particle counts (providers +0x26C / +0x27C, kept at +0x18 / +0x1C) are scaled by
 * radius / 0x00609648, and the system is registered with 0x006CA9BC (vf 0C). The providers call their getter (+4) or
 * setter (+8) on their object (+0x0C); the position and radius ones (+0x10 / +0x14, +0x20 / +0x24 of the origin) */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C void *__thiscall sub_00550420(void *self, void *name, int a, int b);
DECOMP_C int __thiscall sub_0054EA10(void *self, void *a);
DECOMP_C void *__cdecl sub_00433620(void);
DECOMP_C float __thiscall sub_00473110(void *self, float x, float z);
DECOMP_C int __thiscall sub_0054FE30(void *self, int a, float b);
DECOMP_C void __cdecl sub_0054D350(void *self, int eax, float rate);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C char d_0060FA8B[], d_00614A1C[], d_006149D0[], d_006149B8[], d_0069916C[], d_006149B4[], d_00609648[],
    d_0068AE08[], d_006CA9BC[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void *(__thiscall *get_525070)(void *obj, void *self);
typedef void (__thiscall *set_525070)(void *obj, void *self, const void *val);
typedef void (__thiscall *rel_525070)(void *self, int del);
typedef void (__thiscall *reg_525070)(void *self, void *sys);

#define GET(p) ((get_525070)((void **)(p))[1])(((void **)(p))[3], p)
#define SET(p, v) ((set_525070)((void **)(p))[2])(((void **)(p))[3], p, v)

static unsigned int scale_525070(unsigned int n, float f)
{
    float v = (float)(int)n;
    if ((int)n < 0)
        v += *(float *)d_0068AE08;
    return (unsigned int)(long long)(v * f);
}

DECOMP(00525070)
void __thiscall f_00525070(void *this, float x, float z, float radius)
{
    char *s = (char *)this, *sys, *old, *org, *p;
    unsigned int str[7], n;
    float pos[3], f;
    void *o;
    *(float *)(s + 0xc) = radius;
    *(float *)(s + 0x10) = x;
    *(float *)(s + 0x14) = z;
    o = sub_005E3EAE(0x690);
    if (o) {
        imp_00607324(str, d_0060FA8B);
        sys = (char *)sub_00550420(o, str, 0, 0);
    } else
        sys = 0;
    if (sys)
        *(int *)(sys + 4) += 1;
    old = *(char **)(s + 0x20);
    if (old && !(*(int *)(old + 4) -= 1))
        ((rel_525070)**(void ***)old)(old, 1);
    *(char **)(s + 0x20) = sys;
    if (o)
        imp_00607330(str);
    imp_00607324(str, d_00614A1C);
    sub_0054EA10(*(void **)(s + 0x20), str);
    imp_00607330(str);
    sys = *(char **)(s + 0x20);
    org = (char *)((get_525070)*(void **)(sys + 0x5a0))(*(void **)(sys + 0x5a8), sys + 0x59c);
    if ((int)(unsigned int)GET(org + 8) != 1) {
        unsigned int msg[7], thrown[7];
        imp_00607324(msg, d_006149D0);
        sub_00421220(thrown, msg, d_006149B8, 0x3c);
        sub_005E3EC0(thrown, d_0069916C);
    }
    pos[1] = sub_00473110(sub_00433620(), x, z);
    pos[0] = x;
    pos[2] = z;
    p = *(char **)(s + 0x20) + 0x2e4;
    ((set_525070)((void **)p)[4])(((void **)p)[5], p, pos);
    sys = *(char **)(s + 0x20);
    *(unsigned int *)(sys + 0x58) = *(unsigned int *)(sys + 0x64);
    *(unsigned int *)(sys + 0x5c) = *(unsigned int *)(sys + 0x68);
    *(unsigned int *)(sys + 0x60) = *(unsigned int *)(sys + 0x6c);
    *(float *)(sys + 0x64) = 0;
    *(float *)(sys + 0x68) = 0;
    *(float *)(sys + 0x6c) = 0;
    sys[0x70] = 1;
    sys = *(char **)(s + 0x20);
    org = (char *)((get_525070)*(void **)(sys + 0x5a0))(*(void **)(sys + 0x5a8), sys + 0x59c);
    p = org + 0x18;
    ((set_525070)((void **)p)[2])(((void **)p)[3], p, &radius);
    sub_0054D350(*(void **)(s + 0x20), sub_0054FE30(*(void **)(s + 0x20), 0, 0.0f), *(float *)d_006149B4);
    *(unsigned int *)(s + 0x18) = (unsigned int)GET(*(char **)(s + 0x20) + 0x26c);
    *(unsigned int *)(s + 0x1c) = (unsigned int)GET(*(char **)(s + 0x20) + 0x27c);
    f = (float)(radius / *(double *)d_00609648);
    n = scale_525070(*(unsigned int *)(s + 0x18), f);
    SET(*(char **)(s + 0x20) + 0x26c, &n);
    n = scale_525070(*(unsigned int *)(s + 0x1c), f);
    SET(*(char **)(s + 0x20) + 0x27c, &n);
    p = *(char **)d_006CA9BC;
    ((reg_525070)(*(void ***)p)[3])(p, *(void **)(s + 0x20));
}
