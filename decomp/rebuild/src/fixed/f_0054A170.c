/* 0x0054A170: a world creature's reset (the argument is unused): clears its flags (+0x305, +0x2FC) and turn (+0x74,
 * +0x7C), updates (vf18), resets the path (0x00548AC0 on +0x204) and its 9 slots to +0x208 (0x004EF350 on +0x210),
 * the counters (+0x220, +0x224 = 1, +0x2D4 = 10), registers once with the world 0x006C8C3C (0x004EF750, +0x304), clears
 * the text (+0x1D0) and sets +0x2B8. With a model (+0x2F0) but no mesh yet (+0x2D8): the template of the name +0x2DC
 * (0x0042A330 in 0x006CAADC) gives a new 0x21C-byte mesh (0x0042AF50 on {the name, 0, 0, its frame count - 2, - 1})
 * held by reference in +0x2D8 (the old one released), scaled to 0x00608A70, on a random frame (vfF4; +0x1CC and its
 * +0x1C4's +0x1D8); 0x005483D0 when 0x006CAAE4 equals 0x0060FAC0. Returns 0 (the original frees the mesh if its
 * construction throws; this C does not) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00548AC0(void *self);
DECOMP_C void __thiscall sub_004EF350(void *self, unsigned int n, void *val);
DECOMP_C void __thiscall sub_004EF750(void *self, void *obj, int a, int b);
DECOMP_C char *__cdecl sub_0042A330(void *name, void *list, int a);
DECOMP_C char *__thiscall sub_0042AF50(void *self, void *desc, void *tmpl, int a);
DECOMP_C void __thiscall sub_005483D0(void *self);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_006C8C3C[], d_0060FA8B[], d_006CAADC[], d_00608A70[], d_006CAAE4[], d_0060FAC0[];
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
typedef void (__thiscall *vf_54A170)(void *self);
typedef void (__thiscall *del_54A170)(void *self, int flags);
typedef unsigned int (__thiscall *vfu_54A170)(void *self);

DECOMP(0054A170)
int __thiscall f_0054A170(void *this, int unused)
{
    char *s = (char *)this;
    unsigned int v, k, n;
    char *t, *m, *o;
    s[0x305] = 0;
    s[0x2fc] = 0;
    *(float *)(s + 0x74) = 0.0f;
    *(float *)(s + 0x7c) = 0.0f;
    s[0x80] = 1;
    ((vf_54A170)(*(void ***)this)[0x18 / 4])(this);
    sub_00548AC0(s + 0x204);
    v = *(unsigned int *)(s + 0x208);
    sub_004EF350(s + 0x210, 9, &v);
    *(int *)(s + 0x220) = 1;
    *(int *)(s + 0x224) = 1;
    *(int *)(s + 0x2d4) = 10;
    if (!s[0x304]) {
        sub_004EF750(*(void **)d_006C8C3C, this, 0, 0);
        s[0x304] = 1;
    }
    imp_006072F8(s + 0x1d0, d_0060FA8B);
    s[0x2b8] = 1;
    if (*(void **)(s + 0x2f0) && !*(void **)(s + 0x2d8)) {
        struct { unsigned int name[7]; int a, b, c, d; } desc;
        t = sub_0042A330(s + 0x2dc, *(void **)d_006CAADC, 1);
        imp_00607334(desc.name, s + 0x2dc);
        desc.a = 0;
        desc.b = 0;
        desc.c = *(int *)(t + 0x1c8) - 2;
        desc.d = *(int *)(t + 0x1c8) - 1;
        m = sub_005E3EAE(0x21c);
        m = m ? sub_0042AF50(m, &desc, t, 1) : 0;
        if (m)
            ((int *)m)[1]++;
        o = *(char **)(s + 0x2d8);
        if (o && !--((int *)o)[1])
            ((del_54A170)(*(void ***)o)[0])(o, 1);
        *(char **)(s + 0x2d8) = m;
        k = *(unsigned int *)d_00608A70;
        *(unsigned int *)(m + 0x98) = k;
        *(unsigned int *)(m + 0x9c) = k;
        *(unsigned int *)(m + 0xa0) = k;
        m[0xa4] = 1;
        o = *(char **)(s + 0x2d8);
        n = ((vfu_54A170)(*(void ***)o)[0xf4 / 4])(o);
        n = (unsigned int)imp_00607400() % n;
        *(unsigned int *)(o + 0x1cc) = n;
        *(unsigned int *)(*(char **)(o + 0x1c4) + 0x1d8) = n;
        if (*(float *)d_006CAAE4 == *(float *)d_0060FAC0)
            sub_005483D0(this);
        imp_00607330(desc.name);
    }
    return 0;
}
