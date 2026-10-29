/* 0x0044EA20: game start-up (EBX passed through to 0x004A9650): the LocalTexts, Config and Serialize scripts are
 * loaded (0x00432620) with Config's ScreenWidth / ScreenHeight / GamePath set; the Lua C functions _PlayMovie,
 * _PlaySound, _StopSound, ExitGame, ChangeContinent, ChangeSettings, the tree distance, menu music, texture quality
 * and gamma functions and IsShiftDown are registered; the settings (+0x54) go to GUIScene.Options.Param (Grass,
 * Shadow, Reflection, AutoCamera, Grid, Shadow_Units, IsFullScreen, Resolution 0..4, Gamma); the music manager (+4,
 * "Continent0" + "MusicManager", the MainMenu theme at volume +0x88), the sound manager (+8, +0x8C) and the ambient
 * sounds (+0xC, "Continent0AmbientSoundCfg", +0x90) are made and started */
/* @conv ECX,EBX 0 */
/* @func 0044EA20 custom */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_44EA20;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_44EA20;                 /* nScript::Table */
typedef struct { unsigned int w[0x40 / 4]; } Obj_44EA20;
DECOMP_C void __cdecl sub_0044AD30(void);
DECOMP_C void __thiscall sub_00432620(void *self, const char *name);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C char *__cdecl sub_00427990(void);
DECOMP_C void __thiscall sub_0057BDF0(void *t, const char *key, const char *v);
DECOMP_C void __cdecl sub_004031F0(void *L, void *fn, int n);      /* lua_pushcclosure */
DECOMP_C void __cdecl sub_004034F0(void *L, int idx, const char *k);   /* lua_setfield */
DECOMP_C void __thiscall sub_004B6390(void *self);
DECOMP_C void *__cdecl sub_0044AC90(void);
DECOMP_C void __cdecl sub_00432EA0(void *eax);
DECOMP_C void __thiscall sub_00563C90(void *self);
DECOMP_C void __thiscall sub_0056FE20(void *self);
DECOMP_C void __thiscall sub_00563CB0(void *self);
DECOMP_C void *__cdecl sub_0044AE70(void);
DECOMP_C void __cdecl sub_004A9650(void *self, unsigned int ebx);
DECOMP_C void *__thiscall sub_0044D030(void *self, void *out, const void *key);
DECOMP_C void __thiscall sub_0044C0E0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void __thiscall sub_0057BB20(void *t, const char *key, int v);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void __cdecl sub_0044AF10(void);
DECOMP_C void __thiscall sub_0047F0E0(void *self, void *name);
DECOMP_C void __thiscall sub_0047D5C0(void *self, void *name, int vol);
DECOMP_C int __thiscall sub_0047DFD0(void *self);
DECOMP_C void __cdecl sub_0047D410(void *self, unsigned int eax, float v);
DECOMP_C void __cdecl sub_0044AF80(void);
DECOMP_C void __thiscall sub_004EE620(void *self);
DECOMP_C void __thiscall sub_004EDD60(void *self, float v);
DECOMP_C void __cdecl sub_0044AE00(void);
DECOMP_C void __thiscall sub_004299E0(void *self, float *range, void *name);
DECOMP_C void __cdecl sub_00427D70(void *self, unsigned int eax, float v);
DECOMP_C void __thiscall sub_00428A10(void *self);
DECOMP_C char d_006C88D4[], d_0060AFFC[], d_0060AFF4[], d_006C895C[], d_0060AFE8[], d_006C8958[], d_0060AFD8[],
    d_0060AFCC[], d_0060ACB4[], d_0044B260[], d_0060AFC0[], d_0044E830[], d_0060AFB4[], d_0044E8E0[], d_0060AFA8[],
    d_006C88BC[], d_008D122C[], d_0044B1F0[], d_0060AF9C[], d_0044B2F0[], d_0060AF8C[], d_0044D9D0[], d_0060AF7C[],
    d_0044C5A0[], d_0060AF6C[], d_0044C840[], d_0060AF58[], d_0044B480[], d_0060AF48[], d_0044CAE0[], d_0060AF38[],
    d_0044B510[], d_0060AF28[], d_0044B610[], d_0060AF18[], d_0044CCF0[], d_0060AF08[], d_0044B700[], d_0060AEF8[],
    d_0044B810[], d_0060AEE8[], d_0044B3E0[], d_0060AED8[], d_0044CE50[], d_0060AECC[], d_0044B6A0[], d_0060AEC0[],
    d_0060AEB4[], d_0060AD08[], d_0060ADC0[], d_0060AD00[], d_0060ADB8[], d_0060ADB0[], d_0060AD94[], d_0060AD80[],
    d_0060AD8C[], d_0060ADA0[], d_0060AD64[], d_0060AD74[], d_0060AEAC[], d_006C8C38[], d_0060AEA0[], d_0060AE90[],
    d_0060ACC8[], d_006C8C3C[], d_006C8C30[], d_0060AE74[], d_0060AE70[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");

#define F(a) (*(float *)(a))
#define GLOBALS (-10002)

static void reg_44EA20(void *L, void *fn, const char *name)
{
    sub_004031F0(L, fn, 0);
    sub_004034F0(L, GLOBALS, name);
}

static void cfgnum_44EA20(const char *key, float v)
{
    Tbl_44EA20 t;
    sub_0057BC80(sub_004323E0(&t, d_0060AFF4), key, v);
    sub_004220A0(&t);
}

DECOMP(0044EA20)
void __cdecl f_0044EA20(char *this, unsigned int ebx)
{
    static const struct { char *fn, *name; } fns[] = {
        { d_0044B1F0, d_0060AF9C }, { d_0044B2F0, d_0060AF8C }, { d_0044D9D0, d_0060AF7C }, { d_0044C5A0, d_0060AF6C },
        { d_0044C840, d_0060AF58 }, { d_0044B480, d_0060AF48 }, { d_0044CAE0, d_0060AF38 }, { d_0044B510, d_0060AF28 },
        { d_0044B610, d_0060AF18 }, { d_0044CCF0, d_0060AF08 }, { d_0044B700, d_0060AEF8 }, { d_0044B810, d_0060AEE8 },
        { d_0044B3E0, d_0060AED8 }, { d_0044CE50, d_0060AECC }, { d_0044B6A0, d_0060AEC0 },
    };
    static const struct { short off; char *key; } opts[] = {
        { 0x6a, d_0060ADB8 }, { 0x6b, d_0060ADB0 }, { 0x6c, d_0060AD94 }, { 0x6e, d_0060AD80 }, { 0x6d, d_0060AD8C },
        { 0x6f, d_0060ADA0 }, { 0x3c, d_0060AD64 },
    };
    Obj_44EA20 obj;
    Tbl_44EA20 param;
    char *cfg;
    unsigned int k;

    sub_0044AD30();
    sub_00432620(*(void **)d_006C88D4, d_0060AFFC);
    sub_00432620(*(void **)d_006C88D4, d_0060AFF4);
    cfgnum_44EA20(d_0060AFE8, F(d_006C895C));
    cfgnum_44EA20(d_0060AFD8, F(d_006C8958));
    {
        Tbl_44EA20 t;
        void *c = sub_004323E0(&t, d_0060AFF4);
        sub_0057BDF0(c, d_0060AFCC, imp_0060732C(sub_00427990() + 0x20));
        sub_004220A0(&t);
    }
    sub_00432620(*(void **)d_006C88D4, d_0060ACB4);
    reg_44EA20(*(void **)(*(char **)d_006C88D4 + 4), d_0044B260, d_0060AFC0);
    reg_44EA20(*(void **)(*(char **)d_006C88D4 + 4), d_0044E830, d_0060AFB4);
    reg_44EA20(*(void **)(*(char **)d_006C88D4 + 4), d_0044E8E0, d_0060AFA8);
    sub_004B6390(*(void **)d_006C88BC);
    sub_00432EA0(sub_0044AC90());
    sub_00563C90(&obj);
    sub_0056FE20(&obj);
    for (k = 0; k < sizeof fns / sizeof fns[0]; k++)
        reg_44EA20(*(void **)d_008D122C, fns[k].fn, fns[k].name);

    *(void **)(this + 0x64) = sub_0044AE70();
    sub_004A9650(*(void **)(this + 0x64), ebx);
    sub_00432620(*(void **)d_006C88D4, d_0060AEB4);
    {
        Tbl_44EA20 gs, o, t;
        struct { void *t; const char *k; } ref;
        ref.t = sub_004323E0(&gs, d_0060AD08);
        ref.k = d_0060AD00;
        sub_0044C0E0(sub_0044D030(&ref, &o, d_0060ADC0), &t);
        sub_00435D90(&param, &t);
        sub_004220A0(&t);
        sub_004220A0(&o);
        sub_004220A0(&gs);
    }
    cfg = *(char **)(this + 0x54);
    for (k = 0; k < sizeof opts / sizeof opts[0]; k++) {
        cfg = *(char **)(this + 0x54);
        sub_0057BB20(&param, opts[k].key, (unsigned char)cfg[opts[k].off]);
    }
    {
        Tbl_44EA20 gs, t;
        struct { void *t; const char *k; } ref;
        ref.t = sub_004323E0(&gs, d_0060AD08);
        ref.k = d_0060AD00;
        sub_004369F0(&ref, &t);
        sub_0057A860(&param, &t);
        sub_004220A0(&t);
        sub_004220A0(&gs);
    }
    cfg = *(char **)(this + 0x54);
    *(int *)(this + 0x50) = *(int *)(cfg + 0x64);
    this[0xa5] = cfg[0x3c];
    if (*(int *)(cfg + 0x40) == 0x320)
        *(int *)(this + 0x4c) = 0;
    if (*(int *)(cfg + 0x40) == 0x400)
        *(int *)(this + 0x4c) = 1;
    if (*(int *)(cfg + 0x40) == 0x500)
        *(int *)(this + 0x4c) = 2;
    if (*(int *)(cfg + 0x40) == 0x500 && *(int *)(cfg + 0x44) == 0x400)
        *(int *)(this + 0x4c) = 3;
    if (*(int *)(cfg + 0x40) == 0x640)
        *(int *)(this + 0x4c) = 4;
    sub_0057BC80(&param, d_0060AD74, (float)*(int *)(this + 0x4c));
    sub_0057BC80(&param, d_0060AEAC, (float)*(double *)(*(char **)(this + 0x54) + 0x80));

    if (!*(void **)(this + 4)) {
        Str_44EA20 a, b;
        sub_0044AF10();
        *(void **)(this + 4) = *(void **)d_006C8C38;
        imp_00607324(&a, d_0060AEA0);
        imp_006071DC(&b, &a, d_0060AE90);
        imp_00607330(&a);
        sub_0047F0E0(*(void **)(this + 4), &b);
        imp_00607324(&a, d_0060ACC8);
        sub_0047D5C0(*(void **)(this + 4), &a, 100);
        imp_00607330(&a);
        imp_00607330(&b);
    }
    sub_0047D410(*(void **)(this + 4), (unsigned int)sub_0047DFD0(*(void **)(this + 4)),
                 F(*(char **)(this + 0x54) + 0x88));
    if (!*(void **)(this + 8)) {
        sub_0044AF80();
        *(void **)(this + 8) = *(void **)d_006C8C3C;
    }
    sub_004EE620(*(void **)(this + 8));
    if (*(void **)(this + 8))
        sub_004EDD60(*(void **)(this + 8), F(*(char **)(this + 0x54) + 0x8c));
    if (!*(void **)(this + 0xc)) {
        Str_44EA20 a;
        float range[2];
        sub_0044AE00();
        *(void **)(this + 0xc) = *(void **)d_006C8C30;
        imp_00607324(&a, d_0060AE74);
        range[0] = F(d_0060AE70);
        range[1] = F(d_0060AE70);
        sub_004299E0(*(void **)(this + 0xc), range, &a);
        imp_00607330(&a);
        sub_00427D70(*(void **)(this + 0xc), 0, F(*(char **)(this + 0x54) + 0x90));
    }
    sub_00428A10(*(void **)(this + 0xc));
    sub_004220A0(&param);
    sub_00563CB0(&obj);
}
