/* 0x00537B70: builds a town's animations: for each entry of its script's "Anim" table (+0x1E8; iterated with
 * lua_next, the value read by 0x0045C850, the iterator closed by 0x0045C920) the unit (entry[1]) and animation
 * (entry[2]) name pick Unit[unit].Animation[animation] (0x0045C740, 0x004648E0, 0x00464970, 0x004491F0, a fresh
 * reference kept); a table of tables (0x0057C5B0 type 5 at [1]) adds each of its tables, anything else is added
 * itself (0x00537080). The model's (+0x200, its +0x14's vf EC) 0x60-byte box is kept at +0x264 and the model reset
 * (0x004CAFE0(1)) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_537B70;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_537B70;                 /* nScript::Table */
typedef struct { void *tbl; Str_537B70 key; } Ref_537B70;
typedef struct { Tbl_537B70 t; const char *k; } RefC_537B70;
typedef struct { Tbl_537B70 t; Str_537B70 k; } RefS_537B70;
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C void __cdecl sub_00403080(void *L);                        /* lua_pushnil */
DECOMP_C int __cdecl sub_00403B00(void *L, int idx);                /* lua_next */
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C int __cdecl sub_00402190(void *L, int t);                  /* luaL_ref */
DECOMP_C Tbl_537B70 *__stdcall sub_0045C850(Tbl_537B70 *out);
DECOMP_C void __thiscall sub_0045C920(void *self);
DECOMP_C void *__cdecl sub_0045BB70(void *self, unsigned int ebx, Str_537B70 *out);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_537B70 *__thiscall sub_0045C740(void *self, Ref_537B70 *out, Str_537B70 key);
DECOMP_C RefC_537B70 *__thiscall sub_004648E0(void *self, RefC_537B70 *out, const char *key);
DECOMP_C RefS_537B70 *__thiscall sub_00464970(void *self, RefS_537B70 *out, Str_537B70 key);
DECOMP_C void __thiscall sub_004491F0(void *self, void *out);
DECOMP_C int __thiscall sub_0057C5B0(void *self, int i);
DECOMP_C void __thiscall sub_00537080(void *self, void *anim);
DECOMP_C void __thiscall sub_004CAFE0(void *self, int a);
DECOMP_C char d_00615C0C[], d_008D122C[], d_0060B97C[], d_00607CC4[], d_0060C138[], d_0060C088[];
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void *(__thiscall *box_537B70)(void *self);

#define LS (*(void **)d_008D122C)
#define REG (-10000)

static void begin_537B70(unsigned int *it, int ref)
{
    sub_00403390(LS, REG, ref);
    it[1] = 0;
    it[0] = (unsigned int)d_0060B97C;
    sub_00403080(LS);
    *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
}

static void next_537B70(unsigned int *it)
{
    sub_00402A70(LS, -2);
    *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
}

DECOMP(00537B70)
void __thiscall f_00537B70(void *this)
{
    char *s = (char *)this, *o;
    struct { void *t; const char *k; } key;
    Tbl_537B70 tmp, anim;
    unsigned int it[3];
    key.t = s + 0x1e8;
    key.k = d_00615C0C;
    sub_004369F0(&key, &tmp);
    sub_00435D90(&anim, &tmp);
    sub_004220A0(&tmp);
    begin_537B70(it, anim.w[2]);
    while (!*(unsigned char *)&it[2]) {
        Tbl_537B70 val, unit, t, tc;
        struct { void *t; int i; } k1, k2;
        Str_537B70 s1, s2;
        Ref_537B70 r1;
        RefC_537B70 r2;
        RefS_537B70 r3;
        sub_0045C850(&val);
        k1.t = &val;
        k1.i = 2;
        sub_0045BB70(&k1, 0, &s1);
        k2.t = &val;
        k2.i = 1;
        sub_0045BB70(&k2, 0, &s2);
        sub_004491F0(sub_00464970(sub_004648E0(sub_0045C740(sub_004323E0(&unit, d_0060C088), &r1, s2), &r2,
                                               d_0060C138), &r3, s1), &t);
        tc.w[1] = 0;
        sub_00403390(LS, REG, t.w[2]);
        tc.w[0] = (unsigned int)d_00607CC4;
        tc.w[2] = sub_00402190(LS, REG);
        sub_004220A0(&t);
        imp_00607330(&r3.k);
        sub_004220A0(&r3.t);
        sub_004220A0(&r2.t);
        imp_00607330(&r1.key);
        sub_004220A0(&unit);
        if (sub_0057C5B0(&tc, 1) == 5) {
            unsigned int it2[3];
            begin_537B70(it2, tc.w[2]);
            while (!*(unsigned char *)&it2[2]) {
                Tbl_537B70 v2;
                sub_00537080(this, sub_0045C850(&v2));
                sub_004220A0(&v2);
                next_537B70(it2);
            }
            sub_0045C920(it2);
        } else
            sub_00537080(this, &tc);
        sub_004220A0(&tc);
        sub_004220A0(&val);
        next_537B70(it);
    }
    sub_0045C920(it);
    o = *(char **)(*(char **)(s + 0x200) + 0x14);
    __builtin_memcpy(s + 0x264, ((box_537B70)(*(void ***)o)[0xec / 4])(o), 0x60);
    sub_004CAFE0(*(void **)(s + 0x200), 1);
    sub_004220A0(&anim);
}
