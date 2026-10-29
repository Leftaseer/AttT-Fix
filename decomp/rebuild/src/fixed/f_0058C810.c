/* 0x0058C810: a two-state scripted 3D object's constructor (script table, key name, arg 3, name strings 4 and 5 by
 * value): the 3D object base with an empty name (0x004AD180), its vtable 0x0061F304; its table is the entry of the key
 * in the script table (0x0045C740 / 0x00464600); "addAngle" (0x0057AD40) is passed with both names and arg 3
 * to two new 0x338-byte parts (0x0058C2A0) built from the table's "Active" and "Inactive" subtables (0x0057B4E0),
 * which replace the refcounted +0x1C4 / +0x1C8 (released through vf0(1)); +0x1D0 = arg 3, +0x1D4 = 0x00448F10 of
 * 0x006C8714 by name 4, not active (+0x1CC), +0x24 = 0x0061F3C8. Destroys its by-value names; returns this */
/* @conv ECX 68 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_58C810;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_58C810;                 /* nScript::Table */
typedef struct { void *tbl; Str_58C810 key; } Ref_58C810;
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
DECOMP_C Ref_58C810 *__thiscall sub_0045C740(void *self, Ref_58C810 *out, Str_58C810 key);
DECOMP_C void *__thiscall sub_00464600(void *self, Tbl_58C810 *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, Tbl_58C810 *out, const char *key);
DECOMP_C void *__thiscall sub_0058C2A0(void *self, void *t, unsigned int a, Str_58C810 n4, Str_58C810 n5, float add);
DECOMP_C void *__thiscall sub_00448F10(void *self, void *name);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_0060FA8B[], d_0061F304[], d_0061F3CC[], d_00610920[], d_00610914[], d_006C8714[], d_0061F3C8[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
typedef void (__thiscall *rel_58C810)(void *self, int del);

static void part_58C810(void **slot, Tbl_58C810 *t, const char *state, unsigned int a, Str_58C810 *n4,
                        Str_58C810 *n5, float add)
{
    void *o = sub_005E3EAE(0x338), *p, *old;
    if (o) {
        Str_58C810 c4, c5;
        Tbl_58C810 sub;
        imp_00607334(&c5, n5);
        imp_00607334(&c4, n4);
        p = sub_0058C2A0(o, sub_0057B4E0(t, &sub, state), a, c4, c5, add);
        if (p)
            *(int *)((char *)p + 4) += 1;
        old = *slot;
        if (old && !(*(int *)((char *)old + 4) -= 1))
            ((rel_58C810)**(void ***)old)(old, 1);
        *slot = p;
        sub_004220A0(&sub);
        return;
    }
    old = *slot;
    if (old && !(*(int *)((char *)old + 4) -= 1))
        ((rel_58C810)**(void ***)old)(old, 1);
    *slot = 0;
}

DECOMP(0058C810)
void *__thiscall f_0058C810(void *this, void *tbl, const Str_58C810 *key, unsigned int a3, unsigned int n4w0,
                            unsigned int n4w1, unsigned int n4w2, unsigned int n4w3, unsigned int n4w4,
                            unsigned int n4w5, unsigned int n4w6, unsigned int n5w0, unsigned int n5w1,
                            unsigned int n5w2, unsigned int n5w3, unsigned int n5w4, unsigned int n5w5,
                            unsigned int n5w6)
{
    char *s = (char *)this;
    Str_58C810 *n4 = (Str_58C810 *)((char *)__builtin_frame_address(0) + 0x14);
    Str_58C810 *n5 = (Str_58C810 *)((char *)__builtin_frame_address(0) + 0x30);
    Str_58C810 str, k;
    Ref_58C810 r;
    Tbl_58C810 t, t1;
    float add;
    imp_00607324(&str, d_0060FA8B);
    sub_004AD180(this, &str, 0, 0);
    imp_00607330(&str);
    *(void **)s = d_0061F304;
    *(void **)(s + 0x1c4) = 0;
    *(void **)(s + 0x1c8) = 0;
    imp_00607334(&k, key);
    sub_00464600(sub_0045C740(tbl, &r, k), &t1);
    sub_00435D90(&t, &t1);
    sub_004220A0(&t1);
    imp_00607330(&r.key);
    add = sub_0057AD40(tbl, d_0061F3CC);
    part_58C810((void **)(s + 0x1c4), &t, d_00610920, a3, n4, n5, add);
    part_58C810((void **)(s + 0x1c8), &t, d_00610914, a3, n4, n5, add);
    *(unsigned int *)(s + 0x1d0) = a3;
    *(void **)(s + 0x1d4) = sub_00448F10(*(void **)d_006C8714, n4);
    s[0x1cc] = 0;
    *(unsigned int *)(s + 0x24) = *(unsigned int *)d_0061F3C8;
    sub_004220A0(&t);
    imp_00607330(n4);
    imp_00607330(n5);
    return this;
}
