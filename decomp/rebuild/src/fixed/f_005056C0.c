/* 0x005056C0: places the troops of slots 11..20 (EBX passed through to 0x0057AFB0 as the original leaves it; the stack
 * argument is unused): each slot's name in TacticLevel.OrderPlace (0x0057AFB0) picks its TacticLevel.PlaceTroop entry
 * (0x00437870) whose "uiTroop" below 900 is the army (+8's +0x10: 0xC8-byte entries, number uiTroop - 1); the name's
 * first character goes to 0x0051D460, more than 10 creatures (+0x5C) throws ("more than 10 units in the troop",
 * PlacingTroop.cpp:435); from the entry's "headPos" cell (row 0x006CA8C0 - y times 0x006CA8C4 plus x plus 0x006CA8BC)
 * each creature (+0x58, up to the first missing one) stands at the level's offset (+0x624 by number: x, y) mirrored
 * (-x, and -y or -1 - y on odd x; 0x004FCB40, 0x00511B30) */
/* @conv ECX,EBX 4 */
/* @func 005056C0 custom */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Tbl_5056C0;                 /* nScript::Table */
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__cdecl sub_0057AFB0(void *self, unsigned int ebx, void *out, int i);
DECOMP_C void *__thiscall sub_00437870(void *self, Tbl_5056C0 *out, void *name);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C void __thiscall sub_0051D460(void *self, unsigned int c);
DECOMP_C void __thiscall sub_0045CE60(void *self, void *out);
DECOMP_C void __thiscall sub_004FCB40(void *self, unsigned int *out, const int *pos);   /* fills out only */
DECOMP_C void __thiscall sub_00511B30(void *self, unsigned int cell);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C int __cdecl sub_00402190(void *L, int t);                  /* luaL_ref */
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C char d_0060AB58[], d_00613734[], d_00613728[], d_00613720[], d_006136CC[], d_006CA8C0[], d_006CA8C4[],
    d_006CA8BC[], d_008D122C[], d_00607CC4[], d_00613704[], d_006136F0[], d_0069916C[];
DECOMP_C char *(__thiscall *imp_00607208)(void *, unsigned int) __asm__("__imp_??A?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAADU_Size_type_nosscl@01@@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");

#define ARMY(k) (*(char **)(*(char **)(s + 8) + 0x10) + (k) * 0xc8)
#define LS (*(void **)d_008D122C)

static void entry_5056C0(Tbl_5056C0 *out, const char *field)
{
    struct { void *t; const char *k; } key;
    Tbl_5056C0 t, tmp;
    key.t = sub_004323E0(&t, d_0060AB58);
    key.k = field;
    sub_004369F0(&key, &tmp);
    sub_00435D90(out, &tmp);
    sub_004220A0(&tmp);
    sub_004220A0(&t);
}

DECOMP(005056C0)
void __cdecl f_005056C0(void *this, unsigned int ebx, unsigned int unused)
{
    char *s = (char *)this;
    Tbl_5056C0 place, order;
    int i;
    entry_5056C0(&place, d_00613734);
    entry_5056C0(&order, d_00613728);
    for (i = 11; i <= 20; i++) {
        unsigned int name[7], j;
        Tbl_5056C0 u;
        int k;
        sub_0057AFB0(&order, ebx, name, i);
        k = (int)(long long)sub_0057AD40(sub_00437870(&place, &u, name), d_00613720);
        sub_004220A0(&u);
        if (k < 900) {
            k--;
            sub_0051D460(ARMY(k), (unsigned char)*imp_00607208(name, 0));
            if (*(unsigned int *)(ARMY(k) + 0x5c) > 10) {
                unsigned int msg[7], thrown[7];
                imp_00607324(msg, d_00613704);
                sub_00421220(thrown, msg, d_006136F0, 0x1b3);
                sub_005E3EC0(thrown, d_0069916C);
            }
            for (j = 0; j < *(unsigned int *)(ARMY(k) + 0x5c);) {
                struct { void *t; const char *k; } hk;
                struct { void *t; int k; } pk;
                Tbl_5056C0 a, p, hp, pos;
                unsigned int base, cell;
                int y, x, off[2];
                char *c;
                ebx = 0;
                hk.k = d_006136CC;
                hk.t = sub_00437870(&place, &a, name);
                sub_004369F0(&hk, &p);
                hp.w[1] = 0;
                sub_00403390(LS, -10000, p.w[2]);
                hp.w[0] = (unsigned int)d_00607CC4;
                hp.w[2] = sub_00402190(LS, -10000);
                sub_004220A0(&p);
                sub_004220A0(&a);
                y = (int)(long long)sub_0057AC90(&hp, 2);
                ebx = y;
                x = (int)(long long)sub_0057AC90(&hp, 1);
                base = (*(int *)d_006CA8C0 - y) * *(int *)d_006CA8C4 + x + *(int *)d_006CA8BC;
                if (!(*(char ***)(ARMY(k) + 0x58))[j]) {
                    sub_004220A0(&hp);
                    break;
                }
                pk.t = s + 0x624;
                pk.k = ++j;
                sub_0045CE60(&pk, &pos);
                x = (int)(long long)sub_0057AC90(&pos, 1);
                y = (int)(long long)sub_0057AC90(&pos, 2);
                off[1] = x % 2 == 0 ? -y : -1 - y;
                off[0] = -x;
                ebx = -x;
                c = (*(char ***)(ARMY(k) + 0x58))[j - 1];
                sub_004FCB40(&base, &cell, off);
                sub_00511B30(c, cell);
                sub_004220A0(&pos);
                sub_004220A0(&hp);
            }
        }
        imp_00607330(name);
    }
    sub_004220A0(&order);
    sub_004220A0(&place);
}
