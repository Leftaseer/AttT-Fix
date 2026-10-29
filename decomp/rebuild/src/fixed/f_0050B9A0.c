/* 0x0050B9A0: tactical battle, next move: the move ends (0x005083E0, 0x00503B80 / 0x00503B40 on +0xD8); a dead
 * hero (0x00511E00 of the first troop's first creature) shows "scrYouAreDead.tga" (0x00519990); no enemy creature
 * alive means victory: the troop sizes are kept by name (+0x160 / +0x188, 0x005542E0), 0x00513CA0, state 11;
 * otherwise the next troop that has not moved (+0x270 list of {troop, state}, 0x0051DAA0 creatures) moves (state 2,
 * +0x27C, +0x64, _IsWaitMove on the second search); when none is left a new round starts (+0x1C4, SetNumTurn, the
 * round listeners 0x006CA8E0 get an event); the turn caption "tTurnT N. tTurnEnemyT / tTurnFriendT" (0x004AF480 on
 * 0x006CA8DC) is shown, the troop's script hook +0x244 gets its name and size; then an AI troop (+0xB4) plays
 * (0x00509F00), a player troop waits (state 1) or the reach of all troops is marked (0x0051D6D0) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_50B9A0;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_50B9A0;                 /* nScript::Table */
typedef struct { unsigned int w[0x30 / 4]; } Tmp_50B9A0;
typedef struct { char *troop; int state; } Ent_50B9A0;
DECOMP_C int __cdecl sub_005083E0(void *self, unsigned int eax);
DECOMP_C void __thiscall sub_00503B80(void *self);
DECOMP_C void __thiscall sub_00503B40(void *self);
DECOMP_C int __thiscall sub_00511E00(void *self);
DECOMP_C void __thiscall sub_00519990(void *self, void *name);
DECOMP_C int *__thiscall sub_005542E0(void *self, void *key);
DECOMP_C void __thiscall sub_00513CA0(void *self);
DECOMP_C void __thiscall sub_0051DB90(void *self);
DECOMP_C unsigned int __thiscall sub_0051DAA0(void *self);
DECOMP_C void *__thiscall sub_0057B770(void *self, void *out, const char *name);
DECOMP_C void __cdecl sub_004030A0(void *L, float n);               /* lua_pushnumber */
DECOMP_C void __cdecl sub_00403120(void *L, const char *s);         /* lua_pushstring */
DECOMP_C void *__thiscall sub_0057A230(void *f, void *out, void *arg, int n);
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);  /* _CxxThrowException */
DECOMP_C void __thiscall sub_0057BB20(void *t, const char *key, int v);
DECOMP_C void __thiscall sub_0051F950(void *self);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__cdecl sub_004638C0(void *self, unsigned int ebx, void *out);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __thiscall sub_004AF480(void *self, void *text, int a);
DECOMP_C void __thiscall sub_004AD550(void *self, void *s);
DECOMP_C unsigned char __cdecl sub_00508120(void *self, unsigned int eax, void *unit);
DECOMP_C void __stdcall sub_00508BA0(void *unit, void *troop, int a, Str_50B9A0 s, int b);
DECOMP_C void __thiscall sub_00509F00(void *self);
DECOMP_C void __thiscall sub_0051D6D0(void *self, int a, int b);
DECOMP_C char d_00613A40[], d_0060826C[], d_00613908[], d_008D122C[], d_00607C98[], d_0069916C[], d_006CA8E0[],
    d_006CA8E4[], d_0060AC14[], d_00613914[], d_00613A34[], d_00613A2C[], d_00613A20[], d_00613A14[], d_006CA8DC[],
    d_0060B7B8[], d_00613A04[], d_00608A88[], d_0060FA8B[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C int (__cdecl *imp_006073D0)(char *, const char *, ...) __asm__("__imp__sprintf");
typedef void (__thiscall *vf1_50B9A0)(void *self, void *a);

#define VT(o) (*(void ***)(o))
#define LS (*(void **)d_008D122C)

/* the ScriptResult argument object's destructor: a child left throws */
static void done_50B9A0(void **o)
{
    if (o[1]) {
        unsigned int msg[7], exc[12];
        imp_00607324(msg, d_00607C98);
        imp_00607334(exc, msg);
        sub_005E3EC0(exc, d_0069916C);
    }
}

/* LocalText[key] */
static void text_50B9A0(Tbl_50B9A0 *lt, const char *key, Str_50B9A0 *out)
{
    struct { Tbl_50B9A0 *t; const char *k; } ref;
    Str_50B9A0 tmp;
    ref.t = lt;
    ref.k = key;
    sub_004638C0(&ref, 0, &tmp);
    imp_00607334(out, &tmp);
    imp_00607330(&tmp);
}

/* "turn N" caption in the colour */
static void caption_50B9A0(char *this, const char *who, const char *color)
{
    Tbl_50B9A0 lt;
    Str_50B9A0 a, b, s;
    char buf[0x100];
    sub_004323E0(&lt, d_00613A34);
    text_50B9A0(&lt, d_00613A2C, &a);
    text_50B9A0(&lt, who, &b);
    imp_006073D0(buf, d_00613A14, imp_0060732C(&a), *(int *)(this + 0x1c4), imp_0060732C(&b));
    imp_00607324(&s, buf);
    sub_004AF480(*(void **)d_006CA8DC, &s, 0);
    imp_00607330(&s);
    imp_00607324(&s, color);
    sub_004AD550(*(void **)d_006CA8DC, &s);
    imp_00607330(&s);
    imp_00607330(&b);
    imp_00607330(&a);
    sub_004220A0(&lt);
}

DECOMP(0050B9A0)
int __thiscall f_0050B9A0(char *this)
{
    Ent_50B9A0 *e;
    int pass, i, j, found;

    sub_005083E0(this, 0);
    sub_00503B80(*(void **)(this + 0xd8));
    sub_00503B40(*(void **)(this + 0xd8));
    if (sub_00511E00(**(void ***)(*(char **)(this + 0x50) + 0x58)) == 0) {
        Str_50B9A0 s;
        void *c = *(void **)(this + 0x70);
        ((vf1_50B9A0)VT(c)[0xe8 / 4])(c, *(void **)(this + 0x1e4));
        (*(char **)(this + 0x70))[0x228] = 1;
        imp_00607324(&s, d_00613A40);
        sub_00519990(*(void **)(this + 0x48), &s);
        imp_00607330(&s);
        return 0;
    }
    found = 0;
    for (i = 0; (unsigned int)i < *(unsigned int *)(this + 0x60) && !found; i++) {
        char *t = *(char **)(this + 0x5c) + i * 200;
        for (j = 0; (unsigned int)j < *(unsigned int *)(t + 0x5c); j++)
            if (sub_00511E00((*(void ***)(t + 0x58))[j])) {
                found = 1;
                break;
            }
    }
    if (!found) {
        for (i = 0; (unsigned int)i < *(unsigned int *)(this + 0x54); i++) {
            char *t = *(char **)(this + 0x50) + i * 200;
            int n = *(int *)(t + 0x5c);
            *sub_005542E0(this + 0x160, t + 0x2c) = n;
        }
        for (i = 0; (unsigned int)i < *(unsigned int *)(this + 0x60); i++) {
            char *t = *(char **)(this + 0x5c) + i * 200;
            int n = *(int *)(t + 0x5c);
            *sub_005542E0(this + 0x188, t + 0x2c) = n;
        }
        sub_00513CA0(*(void **)(this + 0x15c));
        *(int *)(this + 0x98) = 0xb;
        return 0;
    }

    sub_0051DB90(*(void **)(this + 0x64));
    pass = 0;
    for (;;) {
        for (e = *(Ent_50B9A0 **)(this + 0x270); e != *(Ent_50B9A0 **)(this + 0x274); e++)
            if (e->state == 0 && sub_0051DAA0(e->troop) > 0)
                goto next;
        if (pass == 0) {
            pass = 1;
            continue;
        }
        for (i = 0; *(Ent_50B9A0 **)(this + 0x270) &&
                    (unsigned int)i < (unsigned int)(*(Ent_50B9A0 **)(this + 0x274) - *(Ent_50B9A0 **)(this + 0x270));
             i++)
            (*(Ent_50B9A0 **)(this + 0x270))[i].state = 0;
        (*(int *)(this + 0x1c4))++;
        pass = 0;
        {
            void *o[3];
            Tmp_50B9A0 fn, res;
            void *f;
            o[1] = 0;
            o[0] = d_0060826C;
            o[2] = 0;
            f = sub_0057B770(this + 0x220, &fn, d_00613908);
            sub_004030A0(LS, (float)*(int *)(this + 0x1c4));
            o[2] = (void *)((size_t)o[2] + 1);
            sub_0057A230(f, &res, o, -1);
            sub_00427820(&res);
            sub_004378D0(&fn);
            done_50B9A0(o);
        }
        {
            void *ev = d_0060AC14;
            void **n = *(void ***)d_006CA8E0;
            while (n) {
                *(void **)d_006CA8E4 = n[1];
                ((vf1_50B9A0)VT(n)[4 / 4])(n, &ev);
                n = *(void ***)d_006CA8E4;
            }
        }
    }
next:
    e->state = 2;
    *(Ent_50B9A0 **)(this + 0x27c) = e;
    sub_0057BB20(this + 0x220, d_00613914, pass == 1);
    *(char **)(this + 0x64) = (*(Ent_50B9A0 **)(this + 0x27c))->troop;
    sub_0051F950(*(void **)(this + 0x64));
    {
        int side = *(int *)(*(char **)(this + 0x64) + 0x94);
        if (side == 1)
            caption_50B9A0(this, d_00613A20, d_0060B7B8);
        else if (side == 0) {
            caption_50B9A0(this, d_00613A04, d_00608A88);
            if ((*(char **)(this + 0x64))[0x48])
                this[0x1c8] = sub_00508120(this, (unsigned int)(size_t)*(void **)(this + 0x64),
                                           *(void **)(this + 0x64));
            {
                Str_50B9A0 s;
                imp_00607324(&s, d_0060FA8B);
                sub_00508BA0(*(void **)(this + 0x64), 0, 0, s, 0);
            }
        }
    }
    {
        void *o[3];
        Tmp_50B9A0 res;
        o[1] = 0;
        o[0] = d_0060826C;
        o[2] = 0;
        sub_00403120(LS, imp_0060732C(*(char **)(this + 0x64) + 0x2c));
        o[2] = (void *)((size_t)o[2] + 1);
        sub_004030A0(LS, (float)(int)sub_0051DAA0(*(void **)(this + 0x64)));
        o[2] = (void *)((size_t)o[2] + 1);
        sub_0057A230(this + 0x244, &res, o, 0);
        sub_00427820(&res);
        done_50B9A0(o);
    }
    {
        char *t = *(char **)(this + 0x64);
        if (*(int *)(t + 0xb4)) {
            *(void **)(this + 0x2a4) = **(void ***)(t + 0xb0);
            sub_00509F00(this);
        } else if (*(int *)(t + 0x94) == 1) {
            *(int *)(this + 0x98) = 1;
            sub_0051D6D0(*(void **)(this + 0x64), 1, 1);
        } else if (*(int *)(t + 0x94) == 0) {
            for (e = *(Ent_50B9A0 **)(this + 0x270); e != *(Ent_50B9A0 **)(this + 0x274); e++)
                sub_0051D6D0(e->troop, sub_00508120(this, (unsigned int)(size_t)e, e->troop), 0);
            sub_0051D6D0(*(void **)(this + 0x64), sub_00508120(this, (unsigned int)(size_t)*(void **)(this + 0x64),
                                                               *(void **)(this + 0x64)), 0);
            *(int *)(this + 0x98) = 0;
        }
    }
    return 0;
}
