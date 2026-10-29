/* 0x0058A560: GUI unit icon constructor from a script call (base 0x0046ACE0): "UnitIcon"; its parameter table
 * (argument 3) gives the effectBack effect, the size (size.sx / size.sy, zero meaning the current picture's
 * width / height) and the selection frame (sizeSelect: dx, dy, sx, sy; +0x2C4, 0x00585680 with the effectSelect
 * effect); argument 4 (+0x2D8) names the unit whose Unit table goes to +0x2CC and whose portrait camera
 * (+0x2C8, 0x0058C210 "ConversationCamera") fills viewPortD (dx, dy, dw, dh); arguments 5 / 6 give the click
 * handler (+0x218). Returns this */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_58A560;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_58A560;                 /* nScript::Table */
typedef struct { void *tbl; Str_58A560 key; } Ref_58A560;
typedef struct { Tbl_58A560 t; const char *k; } RefC_58A560;
DECOMP_C void *__cdecl sub_0046ACE0(void *self, unsigned int ebx, void *ctx);
DECOMP_C void __thiscall sub_0046ACB0(void *self, void *out);
DECOMP_C void *__cdecl sub_0057B080(void *self, unsigned int ebx, void *out, const char *key);
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);              /* lua_tonumber */
DECOMP_C RefC_58A560 *__thiscall sub_0044D030(void *self, RefC_58A560 *out, const void *key);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_00585680(void *self, float x, float y, float w, float h, void *effect, void *shader);
DECOMP_C void *__thiscall sub_00582F40(void *self, void *out, int idx, void *def);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_58A560 *__thiscall sub_0045C740(void *self, Ref_58A560 *out, Str_58A560 key);
DECOMP_C void *__thiscall sub_00464600(void *self, void *out);
DECOMP_C void *__cdecl sub_00463B40(void *self, unsigned int ebx, void *out);
DECOMP_C void *__thiscall sub_00437870(void *self, void *out, void *name);
DECOMP_C void *__thiscall sub_0058C210(void *self, float x, float y, float w, float h, void *unit, void *name);
DECOMP_C int __cdecl sub_00402C20(void *L, int idx);
DECOMP_C void *__thiscall sub_0046F810(void *self, void *out, int idx);
DECOMP_C void __thiscall sub_0057FF30(void *self, void *src);
DECOMP_C void *__thiscall sub_00512E90(void *self, void *out, int idx, void *args);
DECOMP_C void __thiscall sub_004378D0(void *self);
DECOMP_C char d_0061EE74[], d_0061EE6C[], d_00607CC4[], d_0061CD18[], d_0061E84C[], d_008D122C[], d_0061E840[],
    d_0061E844[], d_0061E83C[], d_0068AE08[], d_0060FAC0[], d_0061E830[], d_0061E82C[], d_0061E828[], d_0060891C[],
    d_0068A2D8[], d_0061E818[], d_0060C088[], d_0061F0C8[], d_006120A0[], d_0061E808[], d_0061E804[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
typedef void (__thiscall *vfe_58A560)(void *self, void *name, int a);
typedef void (__thiscall *vfs_58A560)(void *self, float w, float h);
typedef unsigned int (__thiscall *vfi_58A560)(void *self);
typedef void (__thiscall *vf0_58A560)(void *self);
typedef void (__thiscall *vfd_58A560)(void *self, int a);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define LS (*(void **)d_008D122C)

static void nil_58A560(void *t)
{
    unsigned int *w = (unsigned int *)t;
    w[1] = 0;
    w[0] = (unsigned int)(size_t)d_00607CC4;
    w[2] = 0xffffffffu;
}

/* the size field key of the parameter table's "size" */
static float size_58A560(Tbl_58A560 *cfg, const char *key)
{
    struct { void *t; const char *k; } ref;
    RefC_58A560 r, *p;
    float v;
    ref.t = cfg;
    ref.k = d_0061E844;
    p = sub_0044D030(&ref, &r, key);
    v = sub_0057AD40(p, p->k);
    sub_004220A0(&r);
    return v;
}

/* the field key of the parameter table as a table */
static void sub_58A560(Tbl_58A560 *cfg, const char *key, Tbl_58A560 *out)
{
    struct { void *t; const char *k; } ref;
    Tbl_58A560 t;
    ref.t = cfg;
    ref.k = key;
    sub_004369F0(&ref, &t);
    sub_00435D90(out, &t);
    sub_004220A0(&t);
}

/* a refcounted field takes o */
static void set_58A560(void **field, char *o)
{
    char *old;
    if (o)
        (*(int *)(o + 4))++;
    old = (char *)*field;
    if (old && --*(int *)(old + 4) == 0)
        ((vfd_58A560)VF(old, 0))(old, 1);
    *field = o;
}

/* the size of the picture shown (+0x44: the list +0x38 at +0x40) through vf */
static float picture_58A560(char *this, int vf)
{
    char *o = *(char **)(this + 0x44);
    void *e = (*(void ***)(o + 0x38))[*(int *)(o + 0x40)];
    return (float)((vfi_58A560)VF(e, vf))(e);
}

DECOMP(0058A560)
void *__thiscall f_0058A560(void *self, char *ctx)
{
    char *this = (char *)self;
    unsigned int ebx = (unsigned int)(size_t)(this + 0x2cc);
    Tbl_58A560 cfg, sel, vp, unit;
    float x, y, sx, sy;
    void *mem;

    sub_0046ACE0(this, 0, ctx);
    *(void **)this = d_0061EE74;
    *(void **)(this + 0x214) = d_0061EE6C;
    *(void **)(this + 0x2c4) = 0;
    *(void **)(this + 0x2c8) = 0;
    nil_58A560(this + 0x2cc);
    nil_58A560(this + 0x2d8);
    imp_006072F8(this + 0x238, d_0061CD18);
    {
        struct { void *c; int i; } a;
        Tbl_58A560 t;
        a.c = ctx;
        a.i = 3;
        sub_0046ACB0(&a, &t);
        sub_00435D90(&cfg, &t);
        sub_004220A0(&t);
    }
    {
        Str_58A560 s;
        ((vfe_58A560)VF(this, 0x2c))(this, sub_0057B080(&cfg, ebx, &s, d_0061E84C), 0);
        imp_00607330(&s);
    }
    x = (float)sub_00402DE0(LS, *(int *)(ctx + 0x10) + 1);
    y = (float)sub_00402DE0(LS, *(int *)(ctx + 0x10) + 2);
    sx = size_58A560(&cfg, d_0061E840);
    sy = size_58A560(&cfg, d_0061E83C);
    if (sy == 0.0f)
        sy = picture_58A560(this, 0x14);
    if (sx == *(float *)d_0060FAC0)
        sx = picture_58A560(this, 0x10);
    ((vfs_58A560)VF(this, 0x94))(this, sx, sy);
    sub_58A560(&cfg, d_0061E830, &sel);
    *(float *)(this + 0x2ec) = sub_0057AD40(&sel, d_0061E82C);
    *(float *)(this + 0x2f0) = sub_0057AD40(&sel, d_0061E828);
    mem = sub_005E3EAE(0x294);
    if (mem) {
        Str_58A560 shader, effect;
        void *e;
        float a, b;
        imp_00607324(&shader, d_0060891C);
        e = sub_0057B080(&cfg, ebx, &effect, d_0068A2D8);
        a = sub_0057AD40(&sel, d_0061E83C);
        b = sub_0057AD40(&sel, d_0061E840);
        set_58A560((void **)(this + 0x2c4),
                   sub_00585680(mem, *(float *)(this + 0x2ec) + x, *(float *)(this + 0x2f0) + y, b, a, e, &shader));
        imp_00607330(&effect);
        imp_00607330(&shader);
    } else
        set_58A560((void **)(this + 0x2c4), 0);
    {
        Str_58A560 s;
        void *o = *(void **)(this + 0x2c4);
        ((vfe_58A560)VF(o, 0x2c))(o, sub_0057B080(&cfg, ebx, &s, d_0061E818), 0);
        imp_00607330(&s);
    }
    ((vf0_58A560)VF(*(void **)(this + 0x2c4), 0x50))(*(void **)(this + 0x2c4));
    {
        Tbl_58A560 def, t;
        nil_58A560(&def);
        sub_0057A860(this + 0x2d8, sub_00582F40(ctx, &t, 4, &def));
        sub_004220A0(&t);
        sub_004220A0(&def);
    }
    if (*(int *)(this + 0x2e0) > 0) {
        Str_58A560 name;
        Tbl_58A560 u, t;
        Ref_58A560 r;
        sub_0057B080(this + 0x2d8, ebx, &name, d_0060C088);
        sub_00464600(sub_0045C740(sub_004323E0(&u, d_0060C088), &r, name), &t);
        sub_0057A860(this + 0x2cc, &t);
        sub_004220A0(&t);
        imp_00607330(&r.key);
        sub_004220A0(&u);
    }
    sub_58A560(&cfg, d_0061F0C8, &vp);
    {
        float dy = sub_0057AD40(&vp, d_0061E828);
        float dx = sub_0057AD40(&vp, d_0061E82C);
        *(float *)(this + 0x2e4) = dx;
        *(float *)(this + 0x2e8) = dy;
    }
    nil_58A560(&unit);
    if (*(int *)(this + 0x2e0) > 0) {
        struct { void *t; const char *k; } ref;
        Str_58A560 name;
        Tbl_58A560 u, t;
        void *n;
        ref.t = this + 0x2d8;
        ref.k = d_0060C088;
        n = sub_00463B40(&ref, ebx, &name);
        sub_0057A860(&unit, sub_00437870(sub_004323E0(&u, d_0060C088), &t, n));
        sub_004220A0(&t);
        sub_004220A0(&u);
        imp_00607330(&name);
    }
    mem = sub_005E3EAE(0x350);
    if (mem) {
        Str_58A560 s;
        float h, w, dh, dw;
        imp_00607324(&s, d_006120A0);
        h = *(float *)(this + 0x78);
        dh = sub_0057AD40(&vp, d_0061E808);
        w = *(float *)(this + 0x74);
        dw = sub_0057AD40(&vp, d_0061E804);
        h = h + dh;
        set_58A560((void **)(this + 0x2c8),
                   sub_0058C210(mem, *(float *)(this + 0x2e4) + x, *(float *)(this + 0x2e8) + y, w + dw, h, &unit,
                                &s));
        imp_00607330(&s);
    } else
        set_58A560((void **)(this + 0x2c8), 0);
    {
        int n = *(int *)(ctx + 0xc), base = *(int *)(ctx + 0x10);
        if ((n >= 5 && sub_00402C20(LS, base + 5)) || (n >= 6 && sub_00402C20(LS, base + 6))) {
            unsigned int f[8];
            if (*(int *)(ctx + 0xc) >= 5 && sub_00402C20(LS, *(int *)(ctx + 0x10) + 5)) {
                struct { void *c; int i; } a;
                Tbl_58A560 t;
                a.c = ctx;
                a.i = 5;
                sub_0046ACB0(&a, &t);
                sub_0057FF30(this + 0x218, sub_00512E90(ctx, f, 6, &t));
                sub_004378D0(f);
                sub_004220A0(&t);
            } else {
                sub_0057FF30(this + 0x218, sub_0046F810(ctx, f, 6));
                sub_004378D0(f);
            }
        }
    }
    sub_004220A0(&unit);
    sub_004220A0(&vp);
    sub_004220A0(&sel);
    sub_004220A0(&cfg);
    return this;
}
