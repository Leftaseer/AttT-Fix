/* 0x00539C70: CWorldHeroCreature::CWorldHeroCreature(name): the base (0x004AD180, 0x004B8640 at +0x1C4), vtables
 * 0x615C54 / 0x615C44; the first one loads the "standard" model (0x006C8714, 0x00448F10 into 0x006CAA28, counted in
 * 0x006CAA24); name +8, the world (0x00425F60) +0x1CC; Unit[name].Animation's WaitWorld and MoveWorld become
 * "creature" animations (0x004CB990, +0x1DC / +0x1E0); +0x210 tells a model twice as tall as the hero's, the box
 * (vfEC, +0x21C) and its visibility (0x00458120, +0x218) are kept, the wait animation runs (0x004CAFE0); the
 * MoveWorld frames 2 and 5 give the squared step length (+0x1F0); then the speeds, the shadow (0x004EC6F0, +0x214),
 * the selection (0x00440B10, +0x2D0) and the scale (0x006C3D78) */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_539C70;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_539C70;                 /* nScript::Table */
typedef struct { void *tbl; Str_539C70 key; } Ref_539C70;
typedef struct { Tbl_539C70 t; const char *k; } RefC_539C70;
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
DECOMP_C void __thiscall sub_004B8640(void *self, int a);
DECOMP_C void *__thiscall sub_00448F10(void *self, void *name);
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_539C70 *__thiscall sub_0045C740(void *self, Ref_539C70 *out, Str_539C70 key);
DECOMP_C RefC_539C70 *__thiscall sub_004648E0(void *self, RefC_539C70 *out, const char *key);
DECOMP_C void __thiscall sub_0044C0E0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C unsigned int *__thiscall sub_004CB990(void *self, void *anim, Str_539C70 kind, void *owner, void *name);
DECOMP_C unsigned int __cdecl sub_00458120(void *self, void *eax, void *pos);
DECOMP_C void __thiscall sub_004CAFE0(void *self, int a);
DECOMP_C void *__thiscall sub_0044D030(void *self, void *out, int a);
DECOMP_C void *__thiscall sub_00537AE0(void *self, void *out, int i);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C unsigned int *__thiscall sub_004EC6F0(void *self, void *a, void *owner, unsigned int b, Str_539C70 s1,
                                               Str_539C70 s2);
DECOMP_C void *__thiscall sub_00440B10(void *self, void *owner, int a, int b, int c, int d);
DECOMP_C char d_0060FA8B[], d_00615C54[], d_00615C44[], d_006CAA24[], d_00613898[], d_006C8714[], d_006CAA28[],
    d_0060C138[], d_0060C088[], d_0060C124[], d_0060FF34[], d_0060C10C[], d_006CA2C8[], d_0060A2A0[], d_00615D14[],
    d_006097EC[], d_0060C2E8[], d_0060C2D8[], d_006C3D78[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
typedef void (__thiscall *rel_539C70)(void *self, int flag);
typedef float *(__thiscall *vfp_539C70)(void *self);

#define VT(o) (*(void ***)(o))
#define F(a) (*(float *)(a))

static void set_539C70(unsigned int **slot, unsigned int *o)
{
    unsigned int *old = *slot;
    if (o)
        o[1]++;
    if (old && --old[1] == 0)
        ((rel_539C70)VT(old)[0])(old, 1);
    *slot = o;
}

/* a "creature" animation of the subtable key of anim */
static unsigned int *anim_539C70(char *this, Tbl_539C70 *anim, const char *key)
{
    void *mem = sub_005E3EAE(0x24);
    unsigned int *o = 0;
    if (mem) {
        Str_539C70 empty, kind;
        Tbl_539C70 t;
        struct { Tbl_539C70 *t; const char *k; } ref;
        imp_00607324(&empty, d_0060FA8B);
        ref.t = anim;
        ref.k = key;
        sub_004369F0(&ref, &t);
        imp_00607324(&kind, d_0060FF34);
        o = sub_004CB990(mem, &t, kind, this + 0x1e4, &empty);
        sub_004220A0(&t);
        imp_00607330(&empty);
    }
    return o;
}

/* the MoveWorld value i */
static char *frame_539C70(Tbl_539C70 *anim, Tbl_539C70 *out, Tbl_539C70 *val, int i)
{
    struct { Tbl_539C70 *t; const char *k; } ref;
    ref.t = anim;
    ref.k = d_0060C10C;
    return sub_00537AE0(sub_0044D030(&ref, out, 1), val, i);
}

DECOMP(00539C70)
void *__thiscall f_00539C70(char *this, void *name)
{
    Str_539C70 s;
    Tbl_539C70 anim;
    char *m, *hm;
    float *b1, *b2, f1, f2, d;
    int n1, n2;

    imp_00607324(&s, d_0060FA8B);
    sub_004AD180(this, &s, 0, 0);
    imp_00607330(&s);
    sub_004B8640(this + 0x1c4, 1);
    *(void **)this = d_00615C54;
    *(void **)(this + 0x1c4) = d_00615C44;
    *(void **)(this + 0x1dc) = 0;
    *(void **)(this + 0x1e0) = 0;
    *(void **)(this + 0x214) = 0;
    *(void **)(this + 0x27c) = 0;
    *(void **)(this + 0x2cc) = 0;
    if (*(int *)d_006CAA24 == 0) {
        imp_00607324(&s, d_00613898);
        *(void **)d_006CAA28 = sub_00448F10(*(void **)d_006C8714, &s);
        imp_00607330(&s);
    }
    (*(int *)d_006CAA24)++;
    imp_0060731C(this + 8, name);
    *(char **)(this + 0x1cc) = sub_00425F60();
    {
        Tbl_539C70 unit, t;
        Ref_539C70 r1;
        RefC_539C70 r2;
        Str_539C70 key;
        imp_00607334(&key, name);
        sub_0044C0E0(sub_004648E0(sub_0045C740(sub_004323E0(&unit, d_0060C088), &r1, key), &r2, d_0060C138), &t);
        sub_00435D90(&anim, &t);
        sub_004220A0(&t);
        sub_004220A0(&r2.t);
        imp_00607330(&r1.key);
        sub_004220A0(&unit);
    }
    set_539C70((unsigned int **)(this + 0x1dc), anim_539C70(this, &anim, d_0060C124));
    set_539C70((unsigned int **)(this + 0x1e0), anim_539C70(this, &anim, d_0060C10C));

    m = **(char ***)(*(char **)(this + 0x1e0) + 0x14);
    b1 = ((vfp_539C70)VT(m)[0xd0 / 4])(m);
    n1 = *(int *)(*(char **)(m + 0x1c4) + 0x1c8);
    hm = **(char ***)(*(char **)(*(char **)(this + 0x1cc) + 0x1f0) + 0x14);
    n2 = *(int *)(*(char **)(hm + 0x1c4) + 0x1c8);
    b2 = ((vfp_539C70)VT(hm)[0xd0 / 4])(hm);
    f2 = b2[n2 * 3 - 1];
    f1 = b1[n1 * 3 - 1];
    this[0x210] = f1 > (long double)f2 + f2;
    __builtin_memcpy(this + 0x21c, ((vfp_539C70)VT(m)[0xec / 4])(m), 0x60);
    this[0x218] = (char)sub_00458120(*(void **)d_006CA2C8, (void *)(size_t)*(unsigned int *)(this + 0x278),
                                     this + 0x21c);
    *(void **)(this + 0x1e8) = *(void **)(this + 0x1dc);
    sub_004CAFE0(*(void **)(this + 0x1dc), 1);
    *(int *)(this + 0x1ec) = 0;
    F(this + 0x1f4) = 1.0f;
    {
        Tbl_539C70 o1, v1, o2, v2;
        char *va = frame_539C70(&anim, &o1, &v1, 2), *vb = frame_539C70(&anim, &o2, &v2, 5);
        int i1 = (int)sub_0057AC90(va, *(int *)(va + 0xc)), i2 = (int)sub_0057AC90(vb, *(int *)(vb + 0xc));
        d = (float)((long double)b1[i2 * 3 + 2] - b1[i1 * 3 + 2]);
        F(this + 0x1f0) = -d;
        sub_004220A0(&v2);
        sub_004220A0(&o2);
        sub_004220A0(&v1);
        sub_004220A0(&o1);
    }
    F(this + 0x1f0) = (float)((long double)F(this + 0x1f0) * F(this + 0x1f0));
    F(this + 0x1f8) = F(d_0060A2A0);
    F(this + 0x1fc) = F(d_00615D14);
    F(this + 0x200) = F(d_006097EC);
    {
        void *mem = sub_005E3EAE(0x324);
        unsigned int *o = 0;
        if (mem) {
            Str_539C70 sa, sb;
            imp_00607324(&sa, d_0060C2E8);
            imp_00607324(&sb, d_0060C2D8);
            o = sub_004EC6F0(mem, this + 0x1e4, this, 1, sb, sa);
        }
        set_539C70((unsigned int **)(this + 0x214), o);
    }
    this[0x2c0] = 0;
    {
        void *mem = sub_005E3EAE(0x438);
        *(void **)(this + 0x2d0) = mem ? sub_00440B10(mem, this, 0, 0, 1, 0) : 0;
    }
    F(this + 0x98) = F(d_006C3D78);
    F(this + 0x9c) = F(d_006C3D78);
    F(this + 0xa0) = F(d_006C3D78);
    this[0xa4] = 1;
    sub_004220A0(&anim);
    return this;
}
