/* 0x00533E30: CNpc constructor (base 0x005B3FD0 "NPC" with the third argument; the second at +0x320): the script
 * table (first argument, +0x1E8) gives the name ([1]; +0x230 and the object name +8, registered by 0x004850F0),
 * the position ([2]: +0x1C4, +0x64), the direction ([3]: +0x78), the model ([4]: +0x2E8 / +0x2E4, 0x00448C50);
 * NPC[name] gives the animations (Action +0x264, Talk +0x268; 0x004CB990), ViewDistance (+0x2D8) and Enabled
 * (+0x324; always in the editor); then the shadow (+0x2E0), the box (+0x1A8, 0x00592020 kind 3), outside the editor
 * the selection marker (+0x370, 0x00440B10) with the four script references dropped, the sound registration
 * (0x004EF750) and +0x36F (not a lift cabin). Returns this */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_533E30;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_533E30;                 /* nScript::Table */
typedef struct { void *tbl; Str_533E30 key; } Ref_533E30;
typedef struct { Tbl_533E30 t; const char *k; } RefC_533E30;
DECOMP_C void __thiscall sub_005B3FD0(void *self, void *name, int a, unsigned int b);
DECOMP_C void __thiscall sub_004B8640(void *self, int a);
DECOMP_C void __thiscall sub_00424980(void *self, int a);
DECOMP_C void __thiscall sub_004B40E0(void *self);
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
DECOMP_C Ref_533E30 *__thiscall sub_0045C740(void *self, Ref_533E30 *out, Str_533E30 key);
DECOMP_C RefC_533E30 *__thiscall sub_004648E0(void *self, RefC_533E30 *out, const char *key);
DECOMP_C void __thiscall sub_0044C0E0(void *self, void *out);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C unsigned char __thiscall sub_0057AA20(void *self, const char *key);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void *__thiscall sub_004CB990(void *self, void *anim, Str_533E30 kind, void *owner, void *name);
DECOMP_C void __thiscall sub_004CAFE0(void *self, int a);
DECOMP_C void *__thiscall sub_004EC6F0(void *self, void *a, void *owner, unsigned int b, Str_533E30 s1,
                                       Str_533E30 s2);
DECOMP_C void *__thiscall sub_00592020(void *self, void *owner, const void *box, int kind);
DECOMP_C void *__thiscall sub_00440B10(void *self, void *owner, int a, int b, int c, int d);
DECOMP_C void __cdecl sub_00402270(void *L, int t, int ref);        /* luaL_unref */
DECOMP_C void __thiscall sub_005335F0(void *self);
DECOMP_C void __thiscall sub_004EF750(void *self, void *obj, int a, int b);
DECOMP_C char d_006100BC[], d_0061572C[], d_00615720[], d_00615700[], d_006156EC[], d_006156E4[], d_006156D8[],
    d_00613600[], d_00608A70[], d_006C8714[], d_0060C138[], d_006100AC[], d_0060FA8B[], d_006100A4[], d_0061009C[],
    d_0060C2E8[], d_0060C2D8[], d_0061090C[], d_006C88D8[], d_008D122C[], d_006C8C3C[], d_00615838[], d_00615824[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
DECOMP_C unsigned char (__cdecl *imp_00607214)(const void *, const char *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@PBD@Z");
typedef void (__thiscall *vfd_533E30)(void *self, int a);
typedef void *(__thiscall *box_533E30)(void *self);

#define TBL(s) ((s) + 0x1e8)
#define LS (*(void **)d_008D122C)

static void set_533E30(void **slot, char *o)
{
    char *old;
    if (o)
        (*(int *)(o + 4))++;
    old = (char *)*slot;
    if (old && --*(int *)(old + 4) == 0)
        ((vfd_533E30)(*(void ***)old)[0])(old, 1);
    *slot = o;
}

/* NPC[name][key] */
static RefC_533E30 *npc_533E30(char *this, const char *key, Tbl_533E30 *npc, Ref_533E30 *r1, RefC_533E30 *r2)
{
    Str_533E30 name;
    imp_00607334(&name, this + 8);
    return sub_004648E0(sub_0045C740(sub_004323E0(npc, d_006100BC), r1, name), r2, key);
}

/* an animation of the subtable key of anim for the "kind" string */
static void anim_533E30(char *this, void **slot, Tbl_533E30 *anim, const char *key, Str_533E30 *kind)
{
    void *mem = sub_005E3EAE(0x24);
    if (mem) {
        Str_533E30 empty, k;
        Tbl_533E30 t;
        struct { void *t; const char *k; } ref;
        imp_00607324(&empty, d_0060FA8B);
        ref.t = anim;
        ref.k = key;
        sub_004369F0(&ref, &t);
        imp_00607334(&k, kind);
        set_533E30(slot, (char *)sub_004CB990(mem, &t, k, this + 0x260, &empty));
        sub_004220A0(&t);
        imp_00607330(&empty);
    } else
        set_533E30(slot, 0);
}

/* drops a script reference */
static void unref_533E30(int *ref)
{
    if (*ref > 0) {
        sub_00402270(LS, -10000, *ref);
        *ref = -1;
    }
}

DECOMP(00533E30)
void *__thiscall f_00533E30(void *self, void *tbl, int a2, unsigned int a3)
{
    char *this = (char *)self;
    unsigned int ebx = (unsigned int)(size_t)TBL(this);
    Tbl_533E30 pos, anim;
    Str_533E30 kind;
    void *mem;

    {
        Str_533E30 s;
        imp_00607324(&s, d_006100BC);
        sub_005B3FD0(this, &s, 0, a3);
        imp_00607330(&s);
    }
    sub_004B8640(this + 0x1f4, 1);
    sub_00424980(this + 0x1fc, 0);
    sub_004B40E0(this + 0x250);
    *(void **)this = d_0061572C;
    *(void **)(this + 0x1f4) = d_00615720;
    *(void **)(this + 0x1fc) = d_00615700;
    *(void **)(this + 0x250) = d_006156EC;
    *(void **)(this + 0x258) = d_006156E4;
    *(void **)(this + 0x25c) = d_006156D8;
    *(int *)(this + 0x264) = 0;
    *(int *)(this + 0x268) = 0;
    *(int *)(this + 0x26c) = 0;
    *(int *)(this + 0x2ec) = 0;
    *(void **)(this + 0x2f4) = d_00613600;
    *(int *)(this + 0x2f8) = 0;
    *(int *)(this + 0x2fc) = 0;
    this[0x326] = 0;
    *(int *)(this + 0x370) = 0;
    *(int *)(this + 0x320) = a2;
    sub_0057A860(TBL(this), tbl);
    {
        struct { void *t; int i; } k;
        Str_533E30 s;
        k.t = TBL(this);
        k.i = 1;
        imp_0060731C(this + 0x230, sub_0045BB70(&k, ebx, &s));
        imp_00607330(&s);
    }
    imp_0060731C(this + 8, this + 0x230);
    sub_004850F0(sub_004B0AA0(), this + 0x230, this);
    {
        struct { void *t; int i; } k;
        Tbl_533E30 t;
        float c1, c2, c3;
        k.t = TBL(this);
        k.i = 2;
        sub_0045CE60(&k, &t);
        sub_00435D90(&pos, &t);
        sub_004220A0(&t);
        sub_0057A860(this + 0x1c4, &pos);
        c3 = sub_0057AC90(&pos, 3);
        c2 = sub_0057AC90(&pos, 2);
        c1 = sub_0057AC90(&pos, 1);
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
    *(float *)(this + 0x98) = *(float *)d_00608A70;
    *(float *)(this + 0x9c) = *(float *)d_00608A70;
    *(float *)(this + 0xa0) = *(float *)d_00608A70;
    this[0xa4] = 1;
    {
        struct { void *t; int i; } k;
        Str_533E30 s;
        k.t = TBL(this);
        k.i = 4;
        sub_0045BA50(&k, ebx, &s);
        *(void **)(this + 0x2e8) = sub_00448C50(*(void **)d_006C8714, &s);
        imp_00607330(&s);
        *(void **)(this + 0x2e4) = *(void **)(this + 0x2e8);
    }
    {
        Tbl_533E30 npc, t;
        Ref_533E30 r1;
        RefC_533E30 r2;
        Str_533E30 name;
        imp_00607334(&name, this + 8);
        sub_0044C0E0(sub_004648E0(sub_0045C740(sub_004323E0(&npc, d_006100BC), &r1, name), &r2, d_0060C138), &t);
        sub_00435D90(&anim, &t);
        sub_004220A0(&t);
        sub_004220A0(&r2.t);
        imp_00607330(&r1.key);
        sub_004220A0(&npc);
    }
    {
        Tbl_533E30 npc;
        Ref_533E30 r1;
        RefC_533E30 r2, *p = npc_533E30(this, d_006100AC, &npc, &r1, &r2);
        *(float *)(this + 0x2d8) = sub_0057AD40(p, p->k);
        sub_004220A0(&r2.t);
        imp_00607330(&r1.key);
        sub_004220A0(&npc);
    }
    {
        struct { void *t; int i; } k;
        Str_533E30 s;
        k.t = TBL(this);
        k.i = 4;
        sub_0045BA50(&k, ebx, &s);
        imp_00607334(&kind, &s);
        imp_00607330(&s);
    }
    anim_533E30(this, (void **)(this + 0x264), &anim, d_006100A4, &kind);
    anim_533E30(this, (void **)(this + 0x268), &anim, d_0061009C, &kind);
    *(void **)(this + 0x270) = *(void **)(this + 0x264);
    sub_004CAFE0(*(void **)(this + 0x264), 1);
    mem = sub_005E3EAE(0x324);
    if (mem) {
        Str_533E30 sa, sb;
        imp_00607324(&sa, d_0060C2E8);
        imp_00607324(&sb, d_0060C2D8);
        *(void **)(this + 0x2e0) = sub_004EC6F0(mem, this + 0x260, this, 1, sb, sa);
    } else
        *(void **)(this + 0x2e0) = 0;
    *(int *)(this + 0x2dc) = 0;
    this[0x31c] = 0;
    this[0x310] = 0;
    {
        Tbl_533E30 npc;
        Ref_533E30 r1;
        RefC_533E30 r2, *p = npc_533E30(this, d_0061090C, &npc, &r1, &r2);
        this[0x324] = sub_0057AA20(p, p->k);
        sub_004220A0(&r2.t);
        imp_00607330(&r1.key);
        sub_004220A0(&npc);
    }
    this[0x325] = 0;
    if ((*(char **)d_006C88D8)[0x40])
        this[0x324] = 1;
    {
        unsigned int box[0x60 / 4];
        void *o = **(void ***)(*(char **)(this + 0x264) + 0x14);
        __builtin_memcpy(box, ((box_533E30)(*(void ***)o)[0xec / 4])(o), 0x60);
        mem = sub_005E3EAE(0x380);
        set_533E30((void **)(this + 0x1a8), mem ? (char *)sub_00592020(mem, this, box, 3) : 0);
    }
    if (!(*(char **)d_006C88D8)[0x40]) {
        mem = sub_005E3EAE(0x438);
        *(void **)(this + 0x370) = mem ? sub_00440B10(mem, this, 1, 3, 1, 0) : 0;
        this[0x326] = 1;
        unref_533E30((int *)(this + 0x1cc));
        unref_533E30((int *)(this + 0x1d8));
        unref_533E30((int *)(this + 0x1e4));
        unref_533E30((int *)(this + 0x1f0));
    }
    sub_005335F0(this);
    this[0x36d] = 1;
    sub_004EF750(*(void **)d_006C8C3C, this, 1, 0);
    this[0x36e] = 1;
    this[0x36f] = imp_00607214(this + 8, d_00615838) && imp_00607214(this + 8, d_00615824);
    imp_00607330(&kind);
    sub_004220A0(&anim);
    sub_004220A0(&pos);
    return this;
}
