/* 0x00505330: places the hero's troops: TacticLevel.PlacingHeroTroop is called for one result (0x0057B770 /
 * 0x0057A180); each army of the battle (+8: 0xC8-byte entries, count +8) with creatures (+0x5C) takes its entry by
 * number from the result's table (0x0046AAA0, 0x0045CE60): its "liter" (0x0057B080, its first character to 0x0051D460)
 * and "headPos", whose cell (row 0x006CA8C0 - y times width 0x006CA8C4 plus 0x006CA8BC plus x) is the base from which
 * each creature (+0x58) stands at its offset from the level's table (+0x624, by number: x, y; 0x004FCB40, 0x00511B30),
 * facing 0x00608974 (+0x78) and placed (+0x80). The results left on the Lua stack are dropped (+0x0C, owned +0x14) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_505330;                 /* nScript::Table */
typedef struct { unsigned int w[0x18 / 4]; } Res_505330;
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C void *__thiscall sub_0057A180(void *self, void *out, int a);
DECOMP_C void *__thiscall sub_0046AAA0(void *self, Tbl_505330 *out, int i);
DECOMP_C void __thiscall sub_0045CE60(void *self, void *out);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__cdecl sub_0057B080(void *self, unsigned int ebx, void *out, const char *key);
DECOMP_C void __thiscall sub_0051D460(void *self, unsigned int c);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C unsigned int *__thiscall sub_004FCB40(void *self, unsigned int *out, const int *pos);
DECOMP_C void __thiscall sub_00511B30(void *self, unsigned int cell);
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C char d_0060AB58[], d_006136DC[], d_006136D4[], d_006136CC[], d_006CA8C0[], d_006CA8C4[], d_006CA8BC[],
    d_00608974[], d_008D122C[];
DECOMP_C char *(__thiscall *imp_00607208)(void *, unsigned int) __asm__("__imp_??A?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAADU_Size_type_nosscl@01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

#define ARMY(i) (*(char **)(*(char **)(s + 8) + 4) + (i) * 0xc8)

DECOMP(00505330)
void __thiscall f_00505330(void *this)
{
    char *s = (char *)this;
    Tbl_505330 t;
    Res_505330 fn, res;
    unsigned int i, j;
    sub_0057B770(sub_004323E0(&t, d_0060AB58), &fn, d_006136DC);
    sub_004220A0(&t);
    sub_0057A180(&fn, &res, 1);
    for (i = 0; i < *(unsigned int *)(*(char **)(s + 8) + 8); i++) {
        Tbl_505330 r, a, army, hp, p;
        struct { void *t; int k; } key;
        struct { void *t; const char *k; } fld;
        unsigned int str[7], base;
        if (!*(unsigned int *)(ARMY(i) + 0x5c))
            continue;
        key.t = sub_0046AAA0(&res, &r, 1);
        key.k = i + 1;
        sub_0045CE60(&key, &a);
        sub_00435D90(&army, &a);
        sub_004220A0(&a);
        sub_004220A0(&r);
        sub_0051D460(ARMY(i), (unsigned char)*imp_00607208(sub_0057B080(&army, i, str, d_006136D4), 0));
        imp_00607330(str);
        fld.t = &army;
        fld.k = d_006136CC;
        sub_004369F0(&fld, &p);
        sub_00435D90(&hp, &p);
        sub_004220A0(&p);
        {
            int y = (int)(long long)sub_0057AC90(&hp, 2), x = (int)(long long)sub_0057AC90(&hp, 1);
            base = (*(int *)d_006CA8C0 - y) * *(int *)d_006CA8C4 + *(int *)d_006CA8BC + x;
        }
        for (j = 0; j < *(unsigned int *)(ARMY(i) + 0x5c); j++) {
            Tbl_505330 pos;
            struct { void *t; int k; } pk;
            int xy[2];
            unsigned int cell;
            char *c;
            pk.t = s + 0x624;
            pk.k = j + 1;
            sub_0045CE60(&pk, &pos);
            xy[0] = (int)(long long)sub_0057AC90(&pos, 1);
            xy[1] = (int)(long long)sub_0057AC90(&pos, 2);
            c = (*(char ***)(ARMY(i) + 0x58))[j];
            sub_00511B30(c, *sub_004FCB40(&base, &cell, xy));
            sub_004220A0(&pos);
            c = (*(char ***)(ARMY(i) + 0x58))[j];
            *(unsigned int *)(c + 0x78) = *(unsigned int *)d_00608974;
            c[0x80] = 1;
        }
        sub_004220A0(&hp);
        sub_004220A0(&army);
    }
    if ((int)res.w[3] > 0) {
        if (((unsigned char *)&res)[0x14])
            sub_00402A70(*(void **)d_008D122C, -1 - (int)res.w[3]);
        res.w[3] = 0;
    }
    sub_00427820(&res);
    sub_004378D0(&fn);
}
