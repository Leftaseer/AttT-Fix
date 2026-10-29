/* 0x00580750: GUI button constructor from a script call (base 0x00582350): its position (arguments 1, 2; +0x2C4),
 * the parameter table (argument 4) with the Normal picture (texture [5], size [1]..[4], effect [6]; 0x00585360), the
 * name (argument 3, lower-cased; "alpha" buttons take their alpha mask 0x00580450), the Selected, Disabled and
 * Contured pictures (+0x294, +0x29C, +0x2A0, 0x00585680; their sizes, effects and [7] flags +0x298, +0x2A4,
 * +0x2A5), the press / release sounds (Sounds [1], [2] or press1.wav; +0x2A8, +0x2AC) and the click handler
 * (arguments 5 / 6, +0x218); unless argument 7 is true each picture joins the current world (0x008D1230).
 * Returns this */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_580750;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_580750;                 /* nScript::Table */
DECOMP_C void *__thiscall sub_00582350(void *self);
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);              /* lua_tonumber */
DECOMP_C int __cdecl sub_00402C20(void *L, int idx);
DECOMP_C int __cdecl sub_00402EA0(void *L, int idx);                 /* lua_toboolean */
DECOMP_C void __thiscall sub_0046ACB0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const void *key);
DECOMP_C void *__cdecl sub_0045BA50(void *self, unsigned int ebx, void *out);
DECOMP_C int __thiscall sub_0057C5B0(void *self, int i);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C void __thiscall sub_00585360(void *self, float a, float b, float c, float d, void *tex, void *shader);
DECOMP_C void *__cdecl sub_0057AFB0(void *self, unsigned int ebx, void *out, int i);
DECOMP_C void __cdecl sub_00449100(void *self, unsigned int ebx, void *out);
DECOMP_C void __thiscall sub_00580450(void *self);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_00585680(void *self, float a, float b, float c, float d, void *tex, void *shader);
DECOMP_C int __thiscall sub_0057C660(void *t, const char *key);
DECOMP_C unsigned char __thiscall sub_0057A970(void *self, int i);
DECOMP_C void *__cdecl sub_005806C0(void *name);
DECOMP_C void *__thiscall sub_0046F810(void *self, void *out, int idx);
DECOMP_C void __thiscall sub_0057FF30(void *self, void *src);
DECOMP_C void *__thiscall sub_00512E90(void *self, void *out, int idx, void *args);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C char d_0061DD3C[], d_0061DD30[], d_008D122C[], d_008D1230[], d_0061DE84[], d_0060891C[], d_0061DE7C[],
    d_0061C9D8[], d_0061DE70[], d_0061CA54[], d_00612CB4[], d_0061DE64[], d_0060A1F8[], d_00607F84[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C char *(__thiscall *imp_00607208)(void *, unsigned int) __asm__("__imp_??A?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAADU_Size_type_nosscl@01@@Z");
DECOMP_C char *(__cdecl *imp_strlwr)(char *) __asm__("__imp___strlwr");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef void (__thiscall *vfp_580750)(void *self, void *p);
typedef void (__thiscall *vfe_580750)(void *self, void *name, int a);
typedef float *(__thiscall *vfv_580750)(void *self);
typedef void (__thiscall *vf0_580750)(void *self);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define LS (*(void **)d_008D122C)
#define WORLD (*(char **)d_008D1230)

/* the world's scene list (+4 vf10) and draw list (+0x54 vf4) take o */
static void join_580750(void *o)
{
    char *w = WORLD + 4;
    ((vfp_580750)VF(w, 0x10))(w, o);
    w = WORLD + 0x54;
    ((vfp_580750)VF(w, 4))(w, o);
}

/* t[i] when present, else 0 */
static float opt_580750(Tbl_580750 *t, int i)
{
    return sub_0057C5B0(t, i) ? sub_0057AC90(t, i) : 0.0f;
}

/* the effect t[6] on picture o when present */
static void effect_580750(void *o, Tbl_580750 *t)
{
    if (sub_0057C5B0(t, 6)) {
        Str_580750 s;
        ((vfe_580750)VF(o, 0x2c))(o, sub_0057AFB0(t, 0, &s, 6), 0);
        imp_00607330(&s);
    }
}

/* the picture of state key: cfg[key] into t, the picture at slot, its size at pos and its flag */
static void state_580750(char *this, Tbl_580750 *cfg, Tbl_580750 *t, const char *key, int slot, int pos, int flag,
                         unsigned char alone, unsigned int ebx)
{
    void *mem, *o;
    float *p;
    {
        Tbl_580750 r;
        sub_0057A860(t, sub_0057B4E0(cfg, &r, key));
        sub_004220A0(&r);
    }
    mem = sub_005E3EAE(0x294);
    if (mem) {
        Str_580750 shader, tex;
        struct { void *t; int i; } k;
        float a, b, c, d;
        imp_00607324(&shader, d_0060891C);
        k.t = t;
        k.i = 5;
        sub_0045BA50(&k, ebx, &tex);
        d = opt_580750(t, 4);
        c = opt_580750(t, 3);
        b = sub_0057AC90(t, 2);
        a = sub_0057AC90(t, 1);
        o = sub_00585680(mem, a, b, c, d, &tex, &shader);
        *(void **)(this + slot) = o;
        imp_00607330(&tex);
        imp_00607330(&shader);
    } else
        *(void **)(this + slot) = 0;
    if (!alone)
        join_580750(*(void **)(this + slot));
    effect_580750(*(void **)(this + slot), t);
    o = *(void **)(this + slot);
    p = ((vfv_580750)VF(o, 0x88))(o);
    *(float *)(this + pos) = p[0];
    *(float *)(this + pos + 4) = p[1];
    this[flag] = sub_0057A970(t, 7);
    o = *(void **)(this + slot);
    ((vf0_580750)VF(o, 0x50))(o);
}

DECOMP(00580750)
void *__thiscall f_00580750(void *self, char *ctx)
{
    char *this = (char *)self;
    Tbl_580750 cfg, t;
    Str_580750 name;
    unsigned char alone;

    sub_00582350(this);
    *(void **)this = d_0061DD3C;
    *(void **)(this + 0x214) = d_0061DD30;
    *(int *)(this + 0x294) = 0;
    *(int *)(this + 0x29c) = 0;
    *(int *)(this + 0x2a0) = 0;
    *(int *)(this + 0x2b4) = 0;
    *(int *)(this + 0x2b8) = 0;
    *(int *)(this + 0x2bc) = 0;
    {
        float x = (float)sub_00402DE0(LS, *(int *)(ctx + 0x10) + 1);
        float y = (float)sub_00402DE0(LS, *(int *)(ctx + 0x10) + 2);
        struct { void *c; int i; } a;
        Tbl_580750 r;
        *(int *)(this + 0x2a8) = 0;
        *(int *)(this + 0x2ac) = 0;
        *(float *)(this + 0x2c4) = x;
        *(float *)(this + 0x2c8) = y;
        a.c = ctx;
        a.i = 4;
        sub_0046ACB0(&a, &r);
        sub_00435D90(&cfg, &r);
        sub_004220A0(&r);
    }
    if (*(int *)(ctx + 0xc) >= 7 && sub_00402C20(LS, *(int *)(ctx + 0x10) + 7))
        alone = sub_00402EA0(LS, *(int *)(ctx + 0x10) + 7) != 0;
    else
        alone = 0;
    if (!alone && WORLD)
        join_580750(this);
    sub_0057B4E0(&cfg, &t, d_0061DE84);
    {
        Str_580750 shader, tex;
        struct { void *t; int i; } k;
        float a, b, c, d;
        imp_00607324(&shader, d_0060891C);
        k.t = &t;
        k.i = 5;
        sub_0045BA50(&k, 0, &tex);
        d = opt_580750(&t, 4);
        c = opt_580750(&t, 3);
        b = sub_0057AC90(&t, 2);
        a = sub_0057AC90(&t, 1);
        sub_00585360(this, a, b, c, d, &tex, &shader);
        imp_00607330(&tex);
        imp_00607330(&shader);
    }
    effect_580750(this, &t);
    *(int *)(this + 0x2cc) = *(int *)(this + 0x58);
    *(int *)(this + 0x2d0) = *(int *)(this + 0x5c);
    {
        struct { void *c; int i; } a;
        Str_580750 s;
        a.c = ctx;
        a.i = 3;
        sub_00449100(&a, 0, &s);
        imp_00607334(&name, &s);
        imp_00607330(&s);
    }
    imp_strlwr(imp_00607208(&name, 0));
    if (imp_006071E4(&name, d_0061DE7C))
        sub_00580450(this);
    state_580750(this, &cfg, &t, d_0061C9D8, 0x294, 0x2d4, 0x298, alone, 0);
    if (sub_0057C660(&cfg, d_0061DE70))
        state_580750(this, &cfg, &t, d_0061DE70, 0x29c, 0x2dc, 0x2a4, alone, 4);
    if (sub_0057C660(&cfg, d_0061CA54))
        state_580750(this, &cfg, &t, d_0061CA54, 0x2a0, 0x2e4, 0x2a5, alone, 0x10);
    if (sub_0057C660(&cfg, d_00612CB4)) {
        Str_580750 s1, s2, o;
        struct { void *t; int i; } k;
        {
            Tbl_580750 r;
            sub_0057A860(&t, sub_0057B4E0(&cfg, &r, d_00612CB4));
            sub_004220A0(&r);
        }
        k.t = &t;
        k.i = 1;
        sub_0045BA50(&k, 0, &o);
        imp_00607334(&s1, &o);
        imp_00607330(&o);
        k.t = &t;
        k.i = 2;
        sub_0045BA50(&k, 0x24, &o);
        imp_00607334(&s2, &o);
        imp_00607330(&o);
        if (s1.w[5])
            *(void **)(this + 0x2a8) = sub_005806C0(&s1);
        if (s2.w[5])
            *(void **)(this + 0x2ac) = sub_005806C0(&s2);
        imp_00607330(&s2);
        imp_00607330(&s1);
    } else {
        Str_580750 s;
        imp_00607324(&s, d_0061DE64);
        *(void **)(this + 0x2a8) = sub_005806C0(&s);
        imp_00607330(&s);
    }
    {
        int n = *(int *)(ctx + 0xc), base = *(int *)(ctx + 0x10);
        if ((n >= 5 && sub_00402C20(LS, base + 5)) || (n >= 6 && sub_00402C20(LS, base + 6))) {
            unsigned int f[8];
            if (*(int *)(ctx + 0xc) >= 5 && sub_00402C20(LS, *(int *)(ctx + 0x10) + 5)) {
                struct { void *c; int i; } a;
                Tbl_580750 r;
                a.c = ctx;
                a.i = 5;
                sub_0046ACB0(&a, &r);
                sub_0057FF30(this + 0x218, sub_00512E90(ctx, f, 6, &r));
                sub_004378D0(f);
                sub_004220A0(&r);
            } else {
                sub_0057FF30(this + 0x218, sub_0046F810(ctx, f, 6));
                sub_004378D0(f);
            }
        }
    }
    ((vfp_580750)VF(this, 0x6c))(this, this + 0x2c4);
    *(float *)(this + 0x2ec) = 0.0f;
    *(float *)(this + 0x2fc) = *(float *)d_0060A1F8;
    *(float *)(this + 0x2f4) = *(float *)d_00607F84;
    *(float *)(this + 0x2f8) = *(float *)d_00607F84;
    this[0x2c0] = 1;
    this[0x2f0] = 0;
    this[0x2a6] = 0;
    ((vf0_580750)VF(this, 0xd4))(this);
    imp_00607330(&name);
    sub_004220A0(&t);
    sub_004220A0(&cfg);
    return this;
}
