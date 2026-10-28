/* 0x0051E780: the spells as a Lua array (the table at +0xBC, copied to out): for each spell of the list at +0xB0 a
 * new table (nScript::Table: lua_createtable, luaL_ref in the registry) with "name" (its string at +8), "qnturn"
 * (vf7C) and "castValue" (vf84) as numbers, stored at 1, 2, ... (0x0057BEA0); the count by 0x0057C180 */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_004033D0(void *L, int narr, int nrec);       /* lua_createtable */
DECOMP_C int __cdecl sub_00402190(void *L, int t);                    /* luaL_ref */
DECOMP_C void __thiscall sub_0057BDF0(void *t, const char *key, const char *v);
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C void __thiscall sub_0057BEA0(void *t, int i, void *v);
DECOMP_C void __thiscall sub_0057C180(void *t, int n);
DECOMP_C void __thiscall sub_00435D90(void *self, void *t);
DECOMP_C void __thiscall sub_004220A0(void *self);
DECOMP_C char d_008D122C[], d_00607CC4[], d_00689F04[], d_006143D8[], d_006143CC[];
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
typedef int (__thiscall *vf_51E780)(void *self);

DECOMP(0051E780)
void *__thiscall f_0051E780(void *this, void *out)
{
    char *s = (char *)this;
    char **n;
    int i = 1;
    for (n = **(char ****)(s + 0xb0); n != *(char ***)(s + 0xb0); n = (char **)*n, i++) {
        unsigned int t[3];
        void **o;
        t[1] = 0;
        t[0] = (unsigned int)d_00607CC4;
        sub_004033D0(*(void **)d_008D122C, 0, 0);
        t[2] = sub_00402190(*(void **)d_008D122C, -10000);
        sub_0057BDF0(t, d_00689F04, imp_0060732C(n[2] + 8));
        o = (void **)n[2];
        sub_0057BC80(t, d_006143D8, (float)((vf_51E780)(*(void ***)o)[0x7c / 4])(o));
        o = (void **)n[2];
        sub_0057BC80(t, d_006143CC, (float)((vf_51E780)(*(void ***)o)[0x84 / 4])(o));
        sub_0057BEA0(s + 0xbc, i, t);
        sub_004220A0(t);
    }
    sub_0057C180(s + 0xbc, i);
    sub_00435D90(out, s + 0xbc);
    return out;
}
