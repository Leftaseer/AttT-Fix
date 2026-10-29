/* 0x004B0E80: CSAO (scripted animated object) constructor (base 0x00532290 with the fourth argument; the second
 * at +0x320): the script table (first argument, +0x1E8) gives the name ([1]; +0x230, +8, registered by
 * 0x004850F0), the position ([2]: +0x1C4, +0x64), the direction ([3]: +0x78), the scale ([5]: +0x1DC, +0x98) and
 * the model ([4]: +0x2E8 / +0x2E4); SAO[name] gives the animations (Active +0x264, Talk +0x268, Inactive +0x374;
 * 0x004CB990), ViewDistance (+0x2D8) and Enabled (+0x324; always in the editor); then the shadow (+0x2E0) and the
 * box (+0x1A8, 0x00592020 kind 4); outside the editor every object but the gates, bridges and the magic barrier
 * gets its selection marker (+0x370) and drops its script tables; the ships join the third argument's list.
 * Returns this */
/* @conv ECX 16 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4B0E80;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_4B0E80;                 /* nScript::Table */
typedef struct { void *tbl; Str_4B0E80 key; } Ref_4B0E80;
typedef struct { Tbl_4B0E80 t; const char *k; } RefC_4B0E80;
DECOMP_C void __thiscall sub_00532290(void *self, void *a);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C void *__cdecl sub_0045BB70(void *self, unsigned int ebx, void *out);
DECOMP_C void *__cdecl sub_004B0AA0(void);
DECOMP_C void __thiscall sub_004850F0(void *self, void *name, void *obj);
DECOMP_C void __thiscall sub_0045CE60(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C void *__cdecl sub_0045BA50(void *self, unsigned int ebx, void *out);
DECOMP_C void *__thiscall sub_00448C50(void *self, void *name);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_4B0E80 *__thiscall sub_0045C740(void *self, Ref_4B0E80 *out, Str_4B0E80 key);
DECOMP_C RefC_4B0E80 *__thiscall sub_004648E0(void *self, RefC_4B0E80 *out, const char *key);
DECOMP_C void *__thiscall sub_00464600(void *self, void *out);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C unsigned char __thiscall sub_0057AA20(void *self, const char *key);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_004CB990(void *self, void *anim, Str_4B0E80 kind, void *owner, void *name);
DECOMP_C void __thiscall sub_004CAFE0(void *self, int a);
DECOMP_C void *__thiscall sub_004EC6F0(void *self, void *a, void *owner, unsigned int b, Str_4B0E80 s1,
                                       Str_4B0E80 s2);
DECOMP_C void *__thiscall sub_00592020(void *self, void *owner, const void *box, int kind);
DECOMP_C void *__thiscall sub_00440B10(void *self, void *owner, int a, int b, int c, int d);
DECOMP_C void __thiscall sub_00421F50(void *self);
DECOMP_C char **__stdcall sub_005AD6C0(char **next, char **prev, void *val);
DECOMP_C void __thiscall sub_004E0EF0(void *list, unsigned int n);
DECOMP_C void __thiscall sub_005335F0(void *self);
DECOMP_C char d_00610704[], d_006106F4[], d_006106D4[], d_006106C0[], d_006106B8[], d_006106AC[], d_006C8714[],
    d_006107E8[], d_0060C138[], d_0060FA8B[], d_00610920[], d_0061009C[], d_00610914[], d_006100AC[], d_0060C2E8[],
    d_0060C2D8[], d_0061090C[], d_006C88D8[], d_006108F4[], d_0060BAE4[], d_006108E0[], d_006108CC[], d_006108B4[],
    d_0061089C[], d_00610888[], d_00610870[], d_0061085C[], d_00610844[], d_0061082C[], d_0061081C[], d_0061080C[],
    d_006107FC[], d_006107EC[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C unsigned char (__cdecl *imp_00607214)(const void *, const char *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
DECOMP_C unsigned char (__cdecl *imp_006071E4)(const void *, const char *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef void (__thiscall *vfd_4B0E80)(void *self, int a);
typedef void *(__thiscall *box_4B0E80)(void *self);

#define TBL(s) ((s) + 0x1e8)

static void set_4B0E80(void **slot, char *o)
{
    char *old;
    if (o)
        (*(int *)(o + 4))++;
    old = (char *)*slot;
    if (old && --*(int *)(old + 4) == 0)
        ((vfd_4B0E80)(*(void ***)old)[0])(old, 1);
    *slot = o;
}

/* an animation of the subtable key of anim for the "kind" string */
static void anim_4B0E80(char *this, void **slot, Tbl_4B0E80 *anim, const char *key, Str_4B0E80 *kind)
{
    void *mem = sub_005E3EAE(0x24);
    if (mem) {
        Str_4B0E80 empty, k;
        Tbl_4B0E80 t;
        struct { void *t; const char *k; } ref;
        imp_00607324(&empty, d_0060FA8B);
        ref.t = anim;
        ref.k = key;
        sub_004369F0(&ref, &t);
        imp_00607334(&k, kind);
        set_4B0E80(slot, (char *)sub_004CB990(mem, &t, k, this + 0x260, &empty));
        sub_004220A0(&t);
        imp_00607330(&empty);
    } else
        set_4B0E80(slot, 0);
}

/* the script table field i as a table */
static void field_4B0E80(char *this, int i, Tbl_4B0E80 *out)
{
    struct { void *t; int i; } k;
    Tbl_4B0E80 t;
    k.t = TBL(this);
    k.i = i;
    sub_0045CE60(&k, &t);
    sub_00435D90(out, &t);
    sub_004220A0(&t);
}

/* the script table field 4 (the model name) */
static void model_4B0E80(char *this, unsigned int ebx, Str_4B0E80 *out)
{
    struct { void *t; int i; } k;
    k.t = TBL(this);
    k.i = 4;
    sub_0045BA50(&k, ebx, out);
}

DECOMP(004B0E80)
void *__thiscall f_004B0E80(void *self, void *tbl, int a2, char **ships, void *a4)
{
    static const char *const fixed[] = {
        d_006108F4, d_0060BAE4, d_006108E0, d_006108CC, d_006108B4, d_0061089C,
        d_00610888, d_00610870, d_0061085C, d_00610844, d_0061082C,
    };
    char *this = (char *)self;
    unsigned int ebx = (unsigned int)(size_t)TBL(this);
    Tbl_4B0E80 pos, sc, sao, anim;
    Str_4B0E80 kind;
    void *mem;
    unsigned int k;

    sub_00532290(this, a4);
    *(void **)this = d_00610704;
    *(void **)(this + 0x1f4) = d_006106F4;
    *(void **)(this + 0x1fc) = d_006106D4;
    *(void **)(this + 0x250) = d_006106C0;
    *(void **)(this + 0x258) = d_006106B8;
    *(void **)(this + 0x25c) = d_006106AC;
    *(int *)(this + 0x374) = 0;
    *(int *)(this + 0x320) = a2;
    sub_0057A860(TBL(this), tbl);
    {
        struct { void *t; int i; } kk;
        Str_4B0E80 s;
        kk.t = TBL(this);
        kk.i = 1;
        imp_0060731C(this + 0x230, sub_0045BB70(&kk, ebx, &s));
        imp_00607330(&s);
    }
    imp_0060731C(this + 8, this + 0x230);
    sub_004850F0(sub_004B0AA0(), this + 0x230, this);
    field_4B0E80(this, 2, &pos);
    sub_0057A860(this + 0x1c4, &pos);
    {
        float c3 = sub_0057AC90(&pos, 3), c2 = sub_0057AC90(&pos, 2), c1 = sub_0057AC90(&pos, 1);
        *(int *)(this + 0x58) = *(int *)(this + 0x64);
        *(int *)(this + 0x5c) = *(int *)(this + 0x68);
        *(int *)(this + 0x60) = *(int *)(this + 0x6c);
        *(float *)(this + 0x64) = c1;
        *(float *)(this + 0x68) = c2;
        *(float *)(this + 0x6c) = c3;
        this[0x70] = 1;
    }
    *(float *)(this + 0x78) = sub_0057AC90(TBL(this), 3);
    this[0x80] = 1;
    field_4B0E80(this, 5, &sc);
    sub_0057A860(this + 0x1dc, &sc);
    {
        float s3 = sub_0057AC90(&sc, 3), s2 = sub_0057AC90(&sc, 2), s1 = sub_0057AC90(&sc, 1);
        *(float *)(this + 0x98) = s1;
        *(float *)(this + 0x9c) = s2;
        this[0xa4] = 1;
        *(float *)(this + 0xa0) = s3;
    }
    {
        Str_4B0E80 s;
        model_4B0E80(this, ebx, &s);
        *(void **)(this + 0x2e8) = sub_00448C50(*(void **)d_006C8714, &s);
        imp_00607330(&s);
        *(void **)(this + 0x2e4) = *(void **)(this + 0x2e8);
    }
    {
        Str_4B0E80 name;
        Tbl_4B0E80 sa, t;
        Ref_4B0E80 r;
        imp_00607334(&name, this + 8);
        sub_00464600(sub_0045C740(sub_004323E0(&sa, d_006107E8), &r, name), &t);
        sub_00435D90(&sao, &t);
        sub_004220A0(&t);
        imp_00607330(&r.key);
        sub_004220A0(&sa);
    }
    {
        struct { void *t; const char *k; } ref;
        Tbl_4B0E80 t;
        ref.t = &sao;
        ref.k = d_0060C138;
        sub_004369F0(&ref, &t);
        sub_00435D90(&anim, &t);
        sub_004220A0(&t);
    }
    {
        Str_4B0E80 s;
        model_4B0E80(this, ebx, &s);
        imp_00607334(&kind, &s);
        imp_00607330(&s);
    }
    anim_4B0E80(this, (void **)(this + 0x264), &anim, d_00610920, &kind);
    anim_4B0E80(this, (void **)(this + 0x268), &anim, d_0061009C, &kind);
    anim_4B0E80(this, (void **)(this + 0x374), &anim, d_00610914, &kind);
    *(float *)(this + 0x2d8) = sub_0057AD40(&sao, d_006100AC);
    *(void **)(this + 0x270) = *(void **)(this + 0x264);
    sub_004CAFE0(*(void **)(this + 0x264), 1);
    mem = sub_005E3EAE(0x324);
    if (mem) {
        Str_4B0E80 sa, sb;
        imp_00607324(&sa, d_0060C2E8);
        imp_00607324(&sb, d_0060C2D8);
        *(void **)(this + 0x2e0) = sub_004EC6F0(mem, this + 0x260, this, 1, sb, sa);
    } else
        *(void **)(this + 0x2e0) = 0;
    *(int *)(this + 0x2dc) = 0;
    this[0x31c] = 0;
    this[0x310] = 0;
    {
        Str_4B0E80 name;
        Tbl_4B0E80 sa;
        Ref_4B0E80 r1;
        RefC_4B0E80 r2, *p;
        imp_00607334(&name, this + 8);
        p = sub_004648E0(sub_0045C740(sub_004323E0(&sa, d_006107E8), &r1, name), &r2, d_0061090C);
        this[0x324] = sub_0057AA20(p, p->k);
        sub_004220A0(&r2.t);
        imp_00607330(&r1.key);
        sub_004220A0(&sa);
    }
    this[0x325] = 0;
    if ((*(char **)d_006C88D8)[0x40])
        this[0x324] = 1;
    {
        unsigned int box[0x60 / 4];
        void *o = **(void ***)(*(char **)(this + 0x264) + 0x14);
        __builtin_memcpy(box, ((box_4B0E80)(*(void ***)o)[0xec / 4])(o), 0x60);
        mem = sub_005E3EAE(0x380);
        set_4B0E80((void **)(this + 0x1a8), mem ? (char *)sub_00592020(mem, this, box, 4) : 0);
    }
    if (!(*(char **)d_006C88D8)[0x40]) {
        for (k = 0; k < sizeof fixed / sizeof fixed[0]; k++)
            if (!imp_00607214(this + 8, fixed[k]))
                break;
        if (k == sizeof fixed / sizeof fixed[0]) {
            mem = sub_005E3EAE(0x438);
            *(void **)(this + 0x370) = mem ? sub_00440B10(mem, this, 1, 3, 1, 0) : 0;
            this[0x326] = 1;
            sub_00421F50(this + 0x1c4);
            sub_00421F50(this + 0x1d0);
            sub_00421F50(this + 0x1dc);
            sub_00421F50(TBL(this));
        }
    }
    if (imp_006071E4(this + 8, d_0061081C) || imp_006071E4(this + 8, d_0061080C) ||
        imp_006071E4(this + 8, d_006107FC) || imp_006071E4(this + 8, d_006107EC)) {
        char **head = (char **)ships[1], **node;
        void *val = this + 0x25c;
        node = sub_005AD6C0(head, (char **)head[1], &val);
        sub_004E0EF0(ships, 1);
        head[1] = (char *)node;
        *(char ***)node[1] = node;
    }
    this[0x378] = 0;
    this[0x379] = 1;
    sub_005335F0(this);
    this[0x36d] = 0;
    imp_00607330(&kind);
    sub_004220A0(&anim);
    sub_004220A0(&sao);
    sub_004220A0(&sc);
    sub_004220A0(&pos);
    return this;
}
