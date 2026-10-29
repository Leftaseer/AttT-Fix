/* 0x005151A0: CTacticCreature constructor (name, its script table, side, army): base 0x004AD180 with an empty name,
 * the sound part (+0x1C4, 0x004B8640), the members; the table (+0x3E4) gives Health (+0x1E0, 0x00513FA0, written
 * back as TabHealth), the army's Units[side + 1] table (+0x2B0); PlayDefense is registered once (0x006CA8F8 counts
 * the creatures); Unit[name].Animation gives the animations (0x004CB990 with Creature or CreatureEnemy textures):
 * WaitTactical (+0x228, current +0x224), MoveTactical (+0x22C, whose model box fills +0x334 and +0x2D4), Attack,
 * RangeAttack, Defense (+0x234..+0x23C), DeathTactical when it is a table else Death (+0x240), CastTactical when
 * there is no Cast else Cast (+0x244); then the shadow (+0x3AC), the health bar (+0x3B8, 0x00462650), the sound
 * registration (0x004EF750), RangeAttackObjectID (+0x258), AttackMaterial / DefenseMaterial / RangeAttackObjectPSP
 * (+0x25C, +0x278, +0x294), 0x00512EC0, the Blood entries {[4], [1], [2], [3]} (+0x248, 0x00515110) and the
 * critical hit text LocalText.tCriticalHit (+0x3F0). Returns this */
/* @conv ECX 16 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_5151A0;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_5151A0;                 /* nScript::Table */
typedef struct { void *tbl; Str_5151A0 key; } Ref_5151A0;
typedef struct { Str_5151A0 s; int n; float a, b; } Blood_5151A0;
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
DECOMP_C void __thiscall sub_004B8640(void *self, int a);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C float __thiscall sub_0057AD40(void *self, const char *key);
DECOMP_C void __thiscall sub_00513FA0(void *self, int health);
DECOMP_C void __thiscall sub_0057BC80(void *t, const char *key, float v);
DECOMP_C void *__thiscall sub_0057B4E0(void *self, void *out, const char *key);
DECOMP_C void __thiscall sub_0045CE60(void *self, void *out);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void __cdecl sub_004031F0(void *L, void *fn, int n);      /* lua_pushcclosure */
DECOMP_C void __cdecl sub_004034F0(void *L, int idx, const char *k);   /* lua_setfield */
DECOMP_C char *__cdecl sub_004F9ED0(void);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_5151A0 *__thiscall sub_0045C740(void *self, Ref_5151A0 *out, Str_5151A0 key);
DECOMP_C void *__thiscall sub_00464600(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_004CB990(void *self, void *anim, Str_5151A0 kind, void *owner, void *name);
DECOMP_C void __thiscall sub_004CAFE0(void *self, int a);
DECOMP_C int __thiscall sub_0057C660(void *self, const char *key);
DECOMP_C void *__thiscall sub_004EC6F0(void *self, void *a, void *owner, unsigned int b, Str_5151A0 s1,
                                       Str_5151A0 s2);
DECOMP_C void *__thiscall sub_00462650(void *self, void *owner);
DECOMP_C void __thiscall sub_004EF750(void *self, void *obj, int a, int b);
DECOMP_C void *__cdecl sub_00463B40(void *self, unsigned int ebx, void *out);
DECOMP_C void __thiscall sub_00512EC0(void *self);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C int __cdecl sub_00402F40(unsigned int ebx, void *L, int idx);   /* lua_objlen */
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C Tbl_5151A0 *__stdcall sub_0045C850(Tbl_5151A0 *out);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C void *__cdecl sub_0045BB70(void *self, unsigned int ebx, void *out);
DECOMP_C void __thiscall sub_00515110(void *self, void *rec);
DECOMP_C void *__cdecl sub_0057B080(void *self, unsigned int ebx, void *out, const char *key);
DECOMP_C char d_0060FA8B[], d_006139FC[], d_00613E30[], d_0060C45C[], d_006CA8F8[], d_00513940[], d_00613E24[],
    d_00613E14[], d_0060C118[], d_0060C088[], d_0060C138[], d_00613E04[], d_00613DF4[], d_00613AC4[], d_00613DE8[],
    d_00613DE0[], d_00613DD0[], d_00613DC8[], d_00613DC0[], d_00613DB0[], d_0060C2E8[], d_0060C2D8[], d_006C8C3C[],
    d_00613D9C[], d_00613D8C[], d_00613D7C[], d_00613D64[], d_0060924C[], d_00613A34[], d_00613D54[], d_008D122C[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
typedef void (__thiscall *vfd_5151A0)(void *self, int a);
typedef void *(__thiscall *vfr_5151A0)(void *self);

#define LS (*(void **)d_008D122C)
#define REG (-10000)
#define U(o) (*(unsigned int *)(this + (o)))
#define P(o) (*(void **)(this + (o)))
#define TBL (this + 0x3e4)

/* the refcounted pointer at +off takes o */
static void set_5151A0(char *this, int off, char *o)
{
    char *old;
    if (o)
        (*(int *)(o + 4))++;
    old = (char *)P(off);
    if (old && --*(int *)(old + 4) == 0)
        ((vfd_5151A0)(*(void ***)old)[0])(old, 1);
    P(off) = o;
}

/* the animation of the subtable key of anim with the textures tex */
static void anim_5151A0(char *this, int off, Tbl_5151A0 *anim, const char *key, Str_5151A0 *tex)
{
    void *mem = sub_005E3EAE(0x24);
    if (mem) {
        Str_5151A0 empty, k;
        Tbl_5151A0 t;
        struct { void *t; const char *k; } ref;
        imp_00607324(&empty, d_0060FA8B);
        ref.t = anim;
        ref.k = key;
        sub_004369F0(&ref, &t);
        imp_00607334(&k, tex);
        set_5151A0(this, off, (char *)sub_004CB990(mem, &t, k, this + 0x220, &empty));
        sub_004220A0(&t);
        imp_00607330(&empty);
    } else
        set_5151A0(this, off, 0);
}

/* the string at +off = the table's key */
static void text_5151A0(char *this, int off, const char *key)
{
    struct { void *t; const char *k; } ref;
    Str_5151A0 s;
    ref.t = TBL;
    ref.k = key;
    imp_0060731C(this + off, sub_00463B40(&ref, 0, &s));
    imp_00607330(&s);
}

DECOMP(005151A0)
void *__thiscall f_005151A0(void *self, void *name, void *tbl, int side, char *army)
{
    char *this = (char *)self;
    static const short zero[] = { 0x1d0, 0x1d4, 0x1d8, 0x1dc, 0x1e4 };
    Str_5151A0 tex;
    Tbl_5151A0 unit, anim, blood;
    int i;

    {
        Str_5151A0 s;
        imp_00607324(&s, d_0060FA8B);
        sub_004AD180(this, &s, 0, 0);
        imp_00607330(&s);
    }
    sub_004B8640(this + 0x1c4, 1);
    U(0x1cc) = 0x608214;
    U(0) = 0x613c8c;
    U(0x1c4) = 0x613c80;
    U(0x1cc) = 0x613c78;
    for (i = 0; i < 5; i++)
        U(zero[i]) = 0;
    U(0x1f4) = 0x613c00;
    U(0x1f8) = 0;
    U(0x1fc) = 0;
    U(0x208) = 0;
    U(0x20c) = 0;
    U(0x210) = 0x613c08;
    U(0x214) = 0;
    U(0x218) = 0;
    for (i = 0x228; i <= 0x244; i += 4)
        U(i) = 0;
    U(0x24c) = 0;
    U(0x250) = 0;
    U(0x254) = 0;
    imp_006071E0(this + 0x25c);
    imp_006071E0(this + 0x278);
    imp_006071E0(this + 0x294);
    U(0x2b4) = 0;
    U(0x2b0) = 0x607cc4;
    U(0x2b8) = 0xffffffffu;
    U(0x2bc) = 0;
    U(0x2c0) = 0;
    U(0x3b8) = 0;
    this[0x3bc] = 0;
    U(0x3c0) = 0;
    U(0x3c4) = 0;
    this[0x3c8] = 0;
    this[0x3c9] = 0;
    U(0x3d0) = 0;
    U(0x3d4) = 0;
    this[0x3d9] = 0;
    U(0x3e8) = 0;
    U(0x3e4) = 0x607cc4;
    U(0x3ec) = 0xffffffffu;
    imp_006071E0(this + 0x3f0);
    imp_0060731C(this + 8, name);
    sub_0057A860(TBL, tbl);
    *(int *)(this + 0x1e0) = (int)(long long)sub_0057AD40(TBL, d_006139FC);
    sub_00513FA0(this, *(int *)(this + 0x1e0));
    sub_0057BC80(TBL, d_00613E30, (float)*(int *)(this + 0x1e0));
    *(float *)(this + 0x1e8) =
        (float)(*(int *)(this + 0x1ec) - *(int *)(this + 0x3dc)) / (float)*(int *)(this + 0x1e0);
    {
        Tbl_5151A0 t1, t2;
        struct { void *t; int i; } ref;
        ref.t = sub_0057B4E0(army + 0x20, &t1, d_0060C45C);
        ref.i = side + 1;
        sub_0045CE60(&ref, &t2);
        sub_0057A860(this + 0x2b0, &t2);
        sub_004220A0(&t2);
        sub_004220A0(&t1);
    }
    U(0x200) = 0;
    U(0x204) = 0;
    set_5151A0(this, 0x208, 0);
    set_5151A0(this, 0x20c, 0);
    U(0x21c) = 0;
    if (*(int *)d_006CA8F8 == 0) {
        sub_004031F0(LS, d_00513940, 0);
        sub_004034F0(LS, -10002, d_00613E24);
    }
    (*(int *)d_006CA8F8)++;
    P(0x3b0) = sub_004F9ED0();
    *(int *)(this + 0x2c4) = side;
    P(0x2c8) = army;
    imp_006071E0(&tex);
    imp_006072F8(&tex, *(int *)(*(char **)(this + 0x2c8) + 0x94) == 1 ? d_00613E14 : d_0060C118);
    {
        Str_5151A0 nm;
        Tbl_5151A0 h, t;
        Ref_5151A0 r;
        imp_00607334(&nm, this + 8);
        sub_00464600(sub_0045C740(sub_004323E0(&h, d_0060C088), &r, nm), &t);
        sub_00435D90(&unit, &t);
        sub_004220A0(&t);
        imp_00607330(&r.key);
        sub_004220A0(&h);
    }
    {
        struct { void *t; const char *k; } ref;
        Tbl_5151A0 t;
        ref.t = &unit;
        ref.k = d_0060C138;
        sub_004369F0(&ref, &t);
        sub_00435D90(&anim, &t);
        sub_004220A0(&t);
    }
    anim_5151A0(this, 0x228, &anim, d_00613E04, &tex);
    P(0x224) = P(0x228);
    sub_004CAFE0(P(0x228), 1);
    anim_5151A0(this, 0x22c, &anim, d_00613DF4, &tex);
    anim_5151A0(this, 0x234, &anim, d_00613AC4, &tex);
    anim_5151A0(this, 0x238, &anim, d_00613DE8, &tex);
    anim_5151A0(this, 0x23c, &anim, d_00613DE0, &tex);
    anim_5151A0(this, 0x240, &anim, sub_0057C660(&anim, d_00613DD0) == 5 ? d_00613DD0 : d_00613DC8, &tex);
    anim_5151A0(this, 0x244, &anim, sub_0057C660(&anim, d_00613DC0) == 0 ? d_00613DB0 : d_00613DC0, &tex);
    U(0x2d0) = 2;
    {
        char *m = **(char ***)((char *)P(0x22c) + 0x14);
        void *box = ((vfr_5151A0)(*(void ***)m)[0xec / 4])(m);
        __builtin_memcpy(this + 0x334, box, 0x60);
        __builtin_memcpy(this + 0x2d4, this + 0x334, 0x60);
    }
    U(0x394) = 0;
    {
        void *mem = sub_005E3EAE(0x324), *p = 0;
        if (mem) {
            Str_5151A0 sa, sb;
            imp_00607324(&sa, d_0060C2E8);
            imp_00607324(&sb, d_0060C2D8);
            p = sub_004EC6F0(mem, this + 0x220, this, 1, sb, sa);
        }
        P(0x3ac) = p;
    }
    U(0x3b4) = 0;
    {
        void *mem = sub_005E3EAE(0x2d8);
        set_5151A0(this, 0x3b8, mem ? (char *)sub_00462650(mem, this) : 0);
    }
    sub_004EF750(*(void **)d_006C8C3C, this, 1, 0);
    *(int *)(this + 0x258) = (int)(long long)sub_0057AD40(TBL, d_00613D9C);
    text_5151A0(this, 0x25c, d_00613D8C);
    text_5151A0(this, 0x278, d_00613D7C);
    text_5151A0(this, 0x294, d_00613D64);
    sub_00512EC0(this);
    {
        struct { void *t; const char *k; } ref;
        Tbl_5151A0 t;
        int n, k;
        ref.t = TBL;
        ref.k = d_0060924C;
        sub_004369F0(&ref, &t);
        sub_00435D90(&blood, &t);
        sub_004220A0(&t);
        sub_00403390(LS, REG, (int)blood.w[2]);
        n = sub_00402F40(0, LS, -1);
        k = 1;
        sub_00403390(LS, -1, 1);
        while (!(n < k)) {
            Tbl_5151A0 v;
            Blood_5151A0 rec;
            struct { void *t; int i; } r4;
            Str_5151A0 s;
            sub_0045C850(&v);
            imp_006071E0(&rec.s);
            rec.n = (int)(long long)sub_0057AC90(&v, 1);
            rec.a = sub_0057AC90(&v, 2);
            rec.b = sub_0057AC90(&v, 3);
            r4.t = &v;
            r4.i = 4;
            imp_0060731C(&rec.s, sub_0045BB70(&r4, 0, &s));
            imp_00607330(&s);
            sub_00515110(this + 0x248, &rec);
            imp_00607330(&rec.s);
            sub_004220A0(&v);
            sub_00402A70(LS, -2);
            k++;
            sub_00403390(LS, -1, k);
        }
        sub_00402A70(LS, -3);
    }
    U(0x3dc) = 0;
    this[0x3e0] = 0;
    {
        Tbl_5151A0 lt;
        Str_5151A0 s;
        imp_0060731C(this + 0x3f0, sub_0057B080(sub_004323E0(&lt, d_00613A34), 0, &s, d_00613D54));
        imp_00607330(&s);
        sub_004220A0(&lt);
    }
    U(0x40c) = 0;
    U(0x410) = 0;
    sub_004220A0(&blood);
    sub_004220A0(&anim);
    sub_004220A0(&unit);
    imp_00607330(&tex);
    return this;
}
