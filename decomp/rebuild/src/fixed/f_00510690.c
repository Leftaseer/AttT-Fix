/* 0x00510690: tactical battle, the enemy's move: with the script's isEnemyTurn set, TacticAI.EnemyTurn(this object,
 * troop count, index of the acting troop + 1) answers a table {w, num, t}; w 0 or num 0 ends the move (0x0050B9A0);
 * t "magic" casts the spell "name" (0x004C73E0 / 0x00575400, +0x1C0) at troop num: every caster object pays its
 * cost from its Intelligence, the spell is aimed (vf68, 0x0051F5F0, selectedTroop, 0x00512970), the action starts
 * (0x00508BA0) and the spell (vf70); "attack" / "shoot" mark the reach (0x0051D6D0) and attack troop num (0x00504400,
 * 0x0050E2D0, 0x00508BA0, 0x00504B40 / 0x00503D20, 0x0050E2D0, 0x00508BA0, 0x00504D70) or, out of reach, move
 * towards it (0x0050C2D0) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_510690;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_510690;                 /* nScript::Table */
typedef struct { unsigned int w[0x30 / 4]; } Tmp_510690;
DECOMP_C void __thiscall sub_0057BB20(void *t, const char *key, int v);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C unsigned int *__thiscall sub_0057D070(void *self, void *obj);
DECOMP_C void __cdecl sub_004030A0(void *L, float n);               /* lua_pushnumber */
DECOMP_C void *__thiscall sub_0057A230(void *f, void *out, void *arg, int n);
DECOMP_C void *__thiscall sub_0046AAA0(void *self, Tbl_510690 *out, int i);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C int __thiscall sub_00422000(void *self);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void *__cdecl sub_004638C0(void *self, unsigned int ebx, void *out);
DECOMP_C void *__cdecl sub_004C73E0(void);
DECOMP_C void *__thiscall sub_00575400(void *self, void *name);
DECOMP_C void __thiscall sub_00508770(void *self, void *out);
DECOMP_C int __thiscall sub_005088D0(void *self);
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C void __thiscall sub_0051F5F0(void *self, void *obj);
DECOMP_C unsigned int __thiscall sub_0051DAA0(void *self);
DECOMP_C void __thiscall sub_00512970(void *self, void *pos);
DECOMP_C void __stdcall sub_00508BA0(void *unit, void *troop, int a, Str_510690 s, int b);
DECOMP_C void __thiscall sub_0051D6D0(void *self, int a, int b);
DECOMP_C unsigned char __thiscall sub_0051DBF0(void *self, int i, int a);
DECOMP_C void __thiscall sub_00504400(void *self, void *unit, void *obj);
DECOMP_C void __thiscall sub_0050E2D0(void *self, void *unit, void *obj, int a, int b);
DECOMP_C void __thiscall sub_00504B40(void *self, void *unit, void *obj);
DECOMP_C void __thiscall sub_0050C2D0(void *self, int i);
DECOMP_C void __thiscall sub_00503D20(void *self, void *unit, void *obj);
DECOMP_C void __thiscall sub_00504D70(void *self, void *unit, void *obj);
DECOMP_C void __thiscall sub_0050B9A0(void *self);
DECOMP_C char d_00613A9C[], d_0060826C[], d_006131F8[], d_00613BBC[], d_008D122C[], d_00607CB8[], d_0068A734[],
    d_00613BB8[], d_0060CBFC[], d_00613BB0[], d_00689F04[], d_00613960[], d_00613BA0[], d_0060FA8B[], d_0061320C[],
    d_00613204[];
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef void (__thiscall *vf1_510690)(void *self, void *a);
typedef void *(__thiscall *vfp_510690)(void *self);
typedef void (__thiscall *vf0_510690)(void *self);

#define LS (*(void **)d_008D122C)
#define FIRST(u) (**(void ***)((char *)(u) + 0x58))

/* string field key of the answer */
static void field_510690(Tbl_510690 *out, const char *key, Str_510690 *dst)
{
    struct { Tbl_510690 *t; const char *k; } ref;
    Str_510690 tmp;
    ref.t = out;
    ref.k = key;
    sub_004638C0(&ref, 6, &tmp);
    imp_00607334(dst, &tmp);
    imp_00607330(&tmp);
}

static void act_510690(char *this, char *troop, int a, int b)
{
    Str_510690 s;
    imp_00607324(&s, d_0060FA8B);
    sub_00508BA0(*(void **)(this + 0x64), troop, a, s, b);
}

DECOMP(00510690)
void __thiscall f_00510690(char *this)
{
    void *script = this + 0x220;
    unsigned int idx = 0;
    int k, num, i;
    struct { void *vt; void *child; int n; } o;
    Tbl_510690 tb, out;
    Tmp_510690 fn, res;
    unsigned int *arg;
    float w;
    Str_510690 act;

    sub_0057BB20(script, d_00613A9C, 1);
    for (k = 0; k < 2; k++) {
        int cnt = *(int *)(this + 0x54 + k * 0xc), j;
        char *u = *(char **)(this + 0x50 + k * 0xc);
        for (j = 0; j < cnt; j++, idx++, u += 0xc8)
            if (u == *(char **)(this + 0x64))
                break;
    }

    o.child = 0;
    o.vt = d_0060826C;
    o.n = 0;
    {
        void *f = sub_0057B770(sub_004323E0(&tb, d_006131F8), &fn, d_00613BBC);
        int n1 = *(int *)(this + 0x60), n0 = *(int *)(this + 0x54);
        arg = sub_0057D070(&o, this + 0x38);
        sub_004030A0(LS, (float)(n1 + n0));
        arg[2]++;
        sub_004030A0(LS, (float)(int)(idx + 1));
        arg[2]++;
        sub_0046AAA0(sub_0057A230(f, &res, arg, -1), &out, 1);
    }
    sub_00427820(&res);
    sub_004378D0(&fn);
    sub_004220A0(&tb);
    o.vt = d_00607CB8;
    sub_00422000(&o);

    w = sub_0057AD40(&out, d_0068A734);
    num = (int)sub_0057AD40(&out, d_00613BB8);
    field_510690(&out, d_0060CBFC, &act);
    num -= 1;
    if (w == 0.0f || num == -1) {
        sub_0050B9A0(this);
    } else if (imp_006071E4(&act, d_00613BB0)) {
        Str_510690 name;
        char *unit = *(char **)(this + 0x64), *troop;
        field_510690(&out, d_00689F04, &name);
        *(void **)(this + 0x1c0) = sub_00575400(sub_004C73E0(), &name);
        for (i = 0; (unsigned int)i < *(unsigned int *)(unit + 0x5c); i++) {
            Tbl_510690 t;
            double intel;
            float v;
            sub_00508770((*(void ***)(unit + 0x58))[i], &t);
            intel = sub_0057AD40(&t, d_00613960);
            v = (float)(intel - (double)sub_005088D0(*(void **)(this + 0x1c0)));
            sub_0057BC80(&t, d_00613960, v);
            sub_004220A0(&t);
        }
        if (num < *(int *)(this + 0x54))
            troop = *(char **)(this + 0x50) + num * 0xc8;
        else
            troop = *(char **)(this + 0x5c) + (num - *(int *)(this + 0x54)) * 0xc8;
        {
            void *sp = *(void **)(this + 0x1c0);
            ((vf1_510690)(*(void ***)sp)[0x68 / 4])(sp, FIRST(troop));
        }
        sub_0051F5F0(troop, FIRST(troop));
        sub_0057BC80(script, d_00613BA0, (float)*(int *)(troop + 0x98));
        for (i = 0; (unsigned int)i < sub_0051DAA0(*(void **)(this + 0x64)); i++) {
            void *obj = (*(void ***)(*(char **)(this + 0x64) + 0x58))[i], *f = FIRST(troop);
            sub_00512970(obj, ((vfp_510690)(*(void ***)f)[0x68 / 4])(f));
        }
        act_510690(this, troop, 0, 1);
        {
            void *sp = *(void **)(this + 0x1c0);
            ((vf0_510690)(*(void ***)sp)[0x70 / 4])(sp);
        }
        *(void **)(this + 0xbc) = FIRST(troop);
        *(int *)(this + 0x98) = 10;
        imp_00607330(&name);
    } else if (imp_006071E4(&act, d_0061320C)) {
        sub_0051D6D0(*(void **)(this + 0x64), 0, 0);
        if (sub_0051DBF0(*(void **)(this + 0x64), num, 0)) {
            char *troop = *(char **)(this + 0x50) + num * 0xc8;
            sub_00504400(*(void **)(this + 0xd8), *(void **)(this + 0x64), FIRST(troop));
            sub_0050E2D0(this, *(void **)(this + 0x64), FIRST(*(char **)(this + 0x50) + num * 0xc8), 1, 0);
            act_510690(this, *(char **)(this + 0x50) + num * 0xc8, 0, 0);
            sub_00504B40(*(void **)(this + 0xd8), *(void **)(this + 0x64),
                         FIRST(*(char **)(this + 0x50) + num * 0xc8));
            *(int *)(this + 0xb0) = 0;
            *(int *)(this + 0x98) = 6;
        } else
            sub_0050C2D0(this, num);
    } else if (imp_006071E4(&act, d_00613204)) {
        sub_0051D6D0(*(void **)(this + 0x64), 1, 0);
        if (!(*(unsigned char **)(*(char **)(this + 0x64) + 0x7c))[num]) {
            sub_0050C2D0(this, num);
        } else {
            sub_00503D20(*(void **)(this + 0xd8), *(void **)(this + 0x64),
                         FIRST(*(char **)(this + 0x50) + num * 0xc8));
            sub_0050E2D0(this, *(void **)(this + 0x64), FIRST(*(char **)(this + 0x50) + num * 0xc8), 0, 0);
            act_510690(this, *(char **)(this + 0x50) + num * 0xc8, 1, 0);
            sub_00504D70(*(void **)(this + 0xd8), *(void **)(this + 0x64),
                         FIRST(*(char **)(this + 0x50) + num * 0xc8));
            *(int *)(this + 0xb0) = 0;
            *(int *)(this + 0x98) = 6;
        }
    }
    sub_0057BB20(script, d_00613A9C, 0);
    imp_00607330(&act);
    sub_004220A0(&out);
}
