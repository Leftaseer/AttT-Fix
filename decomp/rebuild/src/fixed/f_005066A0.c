/* 0x005066A0: battle standard constructor (name, army, a3): the base (0x004AD180, 0x004B8640 at +0x1C4) and vtables
 * 0x613784 / 0x613778; the army (+0x1CC, its +0xA4 points back) gives a random bearer among its first half
 * (+0x1D4) whose two callback lists get this standard (0x00506500, 0x00506540); Standard[name].TacticalFileName
 * names the lowercased "standard" model (0x004C0FE0, +0x208; mesh +0x1F8 0x004C0F80) whose loop animation
 * (0x0042AF50, +0x1E8, scale 2, a random first frame of 40) gets a shadow (0x004EC6F0, +0x1EC), a box (0x00592020,
 * +0x1A8) and the "StandardActive.psp" particles (0x00550420, +0x1E4) coloured by the side (army +0x94) and added to
 * the battle (0x005184B0); +0x20C gets its two corners (0x00485210) */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_5066A0;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_5066A0;                 /* nScript::Table */
typedef struct { Str_5066A0 file; int a, b, first, last; } Anim_5066A0;
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
DECOMP_C void __thiscall sub_004B8640(void *self, int a);
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void *__thiscall sub_00437870(void *self, void *out, void *name);
DECOMP_C void *__cdecl sub_00463B40(void *self, unsigned int ebx, void *out);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__thiscall sub_004C0FE0(void *self, void *file, void *kind);
DECOMP_C void *__thiscall sub_004C0F80(void *self, void *name);
DECOMP_C unsigned int *__thiscall sub_0042AF50(void *self, void *desc, void *tmpl, int a);
DECOMP_C char *__cdecl sub_004F9ED0(void);
DECOMP_C void *__thiscall sub_004EC6F0(void *self, void *a, void *owner, unsigned int b, Str_5066A0 s1,
                                       Str_5066A0 s2);
DECOMP_C unsigned int *__thiscall sub_00592020(void *self, void *owner, void *a, int b);
DECOMP_C void *__thiscall sub_00550420(void *self, void *name, int a, int b);
DECOMP_C int __thiscall sub_0054EA10(void *self, void *a);
DECOMP_C int __thiscall sub_0054FE30(void *self, int a, float b);
DECOMP_C void __cdecl sub_0054D350(void *self, int eax, float rate);
DECOMP_C char *__cdecl sub_00432260(void);
DECOMP_C void *__thiscall sub_005184B0(void *self);
DECOMP_C void __thiscall sub_00485210(void *self, float *a, float *b);
DECOMP_C char d_0060FA8B[], d_00613784[], d_00613778[], d_00613848[], d_00506500[], d_0061385C[], d_00506540[],
    d_0060C46C[], d_006138A4[], d_00613898[], d_00608A70[], d_0060C2E8[], d_0060C2D8[], d_00613884[], d_00613228[],
    d_00613214[], d_00613224[], d_00613220[], d_0061321C[], d_00613218[], d_00613880[], d_0061387C[], d_00613878[],
    d_00613874[], d_00613870[], d_0061386C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C const char *(__thiscall *imp_0060732C)(const void *) __asm__("__imp_?c_str@?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QBEPBDXZ");
DECOMP_C char *(__stdcall *imp_006076CC)(const char *) __asm__("__imp__CharLowerA@4");
typedef void (__thiscall *rel_5066A0)(void *self, int flag);
typedef void *(__thiscall *vfp_5066A0)(void *self);
typedef void (__thiscall *vff_5066A0)(void *self, float a);
typedef void (__thiscall *vf0_5066A0)(void *self);
typedef void (__thiscall *vf1_5066A0)(void *self, void *a);
typedef void (__thiscall *prov_5066A0)(void *obj, void *p, float *color);

#define VT(o) (*(void ***)(o))
#define F(a) (*(float *)(a))

static void set_5066A0(unsigned int **slot, unsigned int *o)
{
    unsigned int *old = *slot;
    if (o)
        o[1]++;
    if (old && --old[1] == 0)
        ((rel_5066A0)VT(old)[0])(old, 1);
    *slot = o;
}

/* a callback node (vtable vt, method fn on arg) pushed on the list at slot */
static void hook_5066A0(void **slot, void *vt, void *arg, void *fn)
{
    void **n = sub_005E3EAE(0x10);
    if (n) {
        n[1] = *slot;
        n[0] = vt;
        n[2] = arg;
        n[3] = fn;
    }
    *slot = n;
}

DECOMP(005066A0)
void *__thiscall f_005066A0(char *this, void *name, char *army, int a3)
{
    Str_5066A0 s, file;
    Anim_5066A0 desc;
    char *bearer, *lp, *ps;
    void *mem, *o;
    unsigned int k, r;
    float color[4], v1[3], v2[3];

    imp_00607324(&s, d_0060FA8B);
    sub_004AD180(this, &s, 0, 0);
    imp_00607330(&s);
    sub_004B8640(this + 0x1c4, 1);
    *(void **)this = d_00613784;
    *(void **)(this + 0x1c4) = d_00613778;
    *(void **)(this + 0x1e8) = 0;
    *(char **)(this + 0x1cc) = army;
    *(void **)(army + 0xa4) = this;
    army = *(char **)(this + 0x1cc);
    k = (unsigned int)(long long)((long double)*(unsigned int *)(army + 0x5c) * 0.5 + 0.5);
    r = (unsigned int)imp_00607400() % k;
    bearer = (*(char ***)(army + 0x58))[r];
    *(char **)(this + 0x1d4) = bearer;
    *(char **)(this + 0x1f0) = army;
    *(char **)(this + 0x1f4) = army;
    hook_5066A0((void **)(bearer + 0x1d0), d_00613848, this + 0x1f0, d_00506500);
    hook_5066A0((void **)(*(char **)(this + 0x1d4) + 0x1d8), d_0061385C, this + 0x1f4, d_00506540);
    *(int *)(this + 0x1d0) = a3;

    {
        Tbl_5066A0 st, t;
        struct { void *t; const char *k; } ref;
        ref.t = sub_00437870(sub_004323E0(&st, d_0060C46C), &t, name);
        ref.k = d_006138A4;
        sub_00463B40(&ref, (unsigned int)(size_t)(this + 0x1f4), &file);
        sub_004220A0(&t);
        sub_004220A0(&st);
    }
    mem = sub_005E3EAE(0x248);
    o = 0;
    if (mem) {
        Str_5066A0 kind, low;
        imp_00607324(&kind, d_00613898);
        imp_00607324(&low, imp_006076CC(imp_0060732C(&file)));
        o = sub_004C0FE0(mem, &low, &kind);
        *(void **)(this + 0x208) = o;
        imp_00607330(&low);
        imp_00607330(&kind);
    } else
        *(void **)(this + 0x208) = 0;
    imp_00607324(&s, d_0060C46C);
    *(void **)(this + 0x1f8) = sub_004C0F80(*(void **)(this + 0x208), &s);
    imp_00607330(&s);

    imp_00607334(&desc.file, &file);
    desc.a = 0;
    desc.b = 0;
    desc.first = *(int *)(*(char **)(this + 0x208) + 0x1c8) - 2;
    desc.last = *(int *)(*(char **)(this + 0x208) + 0x1c8) - 1;
    mem = sub_005E3EAE(0x21c);
    set_5066A0((unsigned int **)(this + 0x1e8),
               mem ? sub_0042AF50(mem, &desc, *(void **)(this + 0x208), 1) : 0);
    lp = *(char **)(this + 0x1e8);
    F(lp + 0x98) = F(d_00608A70);
    F(lp + 0x9c) = F(d_00608A70);
    F(lp + 0xa0) = F(d_00608A70);
    lp[0xa4] = 1;
    lp = *(char **)(this + 0x1e8);
    r = (unsigned int)(imp_00607400() % 40);
    *(int *)(lp + 0x1cc) = (int)r;
    *(int *)(*(char **)(lp + 0x1c4) + 0x1d8) = (int)r;
    *(int *)(this + 0x1d8) = 0;
    F(this + 0x1dc) = F(sub_004F9ED0() + 0x64);
    this[0x1e1] = 1;

    {
        void *owner = *(void **)(this + 0x1e8);
        mem = sub_005E3EAE(0x324);
        o = 0;
        if (mem) {
            Str_5066A0 sa, sb;
            imp_00607324(&sa, d_0060C2E8);
            imp_00607324(&sb, d_0060C2D8);
            o = sub_004EC6F0(mem, &owner, *(void **)(this + 0x1e8), 1, sb, sa);
        }
        *(void **)(this + 0x1ec) = o;
    }
    mem = sub_005E3EAE(0x380);
    if (mem) {
        void *m = *(void **)(this + 0x1e8);
        set_5066A0((unsigned int **)(this + 0x1a8), sub_00592020(mem, this, ((vfp_5066A0)VT(m)[0xec / 4])(m), 0));
    } else
        set_5066A0((unsigned int **)(this + 0x1a8), 0);
    this[0x1e2] = 0;

    mem = sub_005E3EAE(0x690);
    if (mem) {
        imp_00607324(&s, d_0060FA8B);
        *(void **)(this + 0x1e4) = sub_00550420(mem, &s, 0, 0);
        imp_00607330(&s);
    } else
        *(void **)(this + 0x1e4) = 0;
    imp_00607324(&s, d_00613884);
    sub_0054EA10(*(void **)(this + 0x1e4), &s);
    imp_00607330(&s);
    sub_0054D350(*(void **)(this + 0x1e4), sub_0054FE30(*(void **)(this + 0x1e4), 0, 0.0f), F(d_00613228));
    sub_0054FE30(*(void **)(this + 0x1e4), 0, 0.0f);
    ps = *(char **)(this + 0x1e4);
    ((vff_5066A0)VT(ps)[4 / 4])(ps, F(d_00613214));
    ps = *(char **)(this + 0x1e4);
    ((vf0_5066A0)VT(ps)[0x50 / 4])(ps);

    color[3] = 1.0f;
    if (*(int *)(*(char **)(this + 0x1cc) + 0x94) == 1) {
        color[0] = F(d_00613224);
        color[1] = F(d_00613220);
        color[2] = 0.0f;
    } else {
        color[0] = F(d_0061321C);
        color[1] = F(d_00613218);
        color[2] = F(d_00613218);
    }
    ps = *(char **)(this + 0x1e4);
    ((prov_5066A0)*(void **)(ps + 0x330))(*(void **)(ps + 0x334), ps + 0x31c, color);
    {
        void *m = sub_005184B0(sub_00432260());
        ((vf1_5066A0)VT(m)[4 / 4])(m, *(void **)(this + 0x1e4));
    }
    v1[0] = F(d_00613880);
    v1[1] = F(d_0061387C);
    v1[2] = F(d_00613878);
    v2[0] = F(d_00613874);
    v2[1] = F(d_00613870);
    v2[2] = F(d_0061386C);
    *(int *)(this + 0x1fc) = 0;
    sub_00485210(this + 0x20c, v2, v1);
    imp_00607330(&desc.file);
    imp_00607330(&file);
    return this;
}
