/* 0x004B2720: SceneRankChange constructor (base 0x004B20D0 with the first argument, the second kept at +0x80 as the
 * scene's object list): named "Подсцена смены звания Героя"; the hero's (0x00425F60) current skin
 * Hero[name].CurSkin picks Hero[name].Skins[skin] whose Animation.RankChange[1] table names the creature model
 * (+0x74, "Creature" textures, 0x0042A0D0 / 0x0042A530) placed at the hero with the hero's direction and unit scale,
 * its animation player (+0x7C, 0x004B2430) and its shadow (+0x78, 0x004EC6F0); every entry of RankChangeGlow adds a
 * BloodPS particle system (0x00550420) with the entry's effect (field 0x34 as text), count (field 1) and height
 * (field 2) above the hero. Returns this */
/* @conv ECX 8 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4B2720;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_4B2720;                 /* nScript::Table */
typedef struct { void *tbl; Str_4B2720 key; } Ref_4B2720;
typedef struct { Tbl_4B2720 t; const char *k; } RefC_4B2720;
typedef struct { Tbl_4B2720 t; int i; } RefI_4B2720;
typedef struct { Tbl_4B2720 t; Str_4B2720 k; } RefS_4B2720;
DECOMP_C void __thiscall sub_004B20D0(void *self, int a);
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C Ref_4B2720 *__thiscall sub_0045C740(void *self, Ref_4B2720 *out, Str_4B2720 key);
DECOMP_C RefC_4B2720 *__thiscall sub_004648E0(void *self, RefC_4B2720 *out, const char *key);
DECOMP_C RefS_4B2720 *__thiscall sub_00464970(void *self, RefS_4B2720 *out, Str_4B2720 key);
DECOMP_C void *__cdecl sub_00463AD0(void *self, unsigned int ebx, Str_4B2720 *out);
DECOMP_C void __thiscall sub_004491F0(void *self, void *out);
DECOMP_C void __thiscall sub_00435D90(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__thiscall sub_0044D030(void *self, void *out, const void *key);
DECOMP_C RefI_4B2720 *__thiscall sub_004B2690(void *self, RefI_4B2720 *out, int i);
DECOMP_C void __thiscall sub_004B2670(void *self, void *out);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void *__cdecl sub_0045BB70(void *self, unsigned int ebx, Str_4B2720 *out);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__cdecl sub_0042A0D0(void *desc, void *textures, int a);
DECOMP_C int *__thiscall sub_0042A530(void *self, void *desc, void *tex, int a);
DECOMP_C void *__thiscall sub_004B2430(void *self, void *creature);
DECOMP_C void *__thiscall sub_004EC6F0(void *self, void *a, void *owner, unsigned int b, Str_4B2720 s1,
                                       Str_4B2720 s2);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C void __cdecl sub_00403080(void *L);                        /* lua_pushnil */
DECOMP_C int __cdecl sub_00403B00(void *L, int idx);                /* lua_next */
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C Tbl_4B2720 *__stdcall sub_0045C850(Tbl_4B2720 *out);
DECOMP_C void __thiscall sub_0045C920(void *self);
DECOMP_C void *__thiscall sub_00550420(void *self, void *name, int a, int b);
DECOMP_C void *__cdecl sub_0057AFB0(void *self, unsigned int ebx, void *out, int i);
DECOMP_C int __thiscall sub_0054EA10(void *self, void *a);
DECOMP_C void __thiscall sub_0054FE30(void *self, int a, float b);
DECOMP_C char d_006109BC[], d_0061099C[], d_00610AFC[], d_0060C0E0[], d_0060C080[], d_0060C130[], d_00610AF0[],
    d_0060C138[], d_00610AE0[], d_0060C118[], d_00608A70[], d_0060C2E8[], d_0060C2D8[], d_008D122C[], d_0060B97C[],
    d_00609234[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
typedef void (__thiscall *vf0_4B2720)(void *self);
typedef void (__thiscall *vfp_4B2720)(void *self, void *p);
typedef float *(__thiscall *vfv_4B2720)(void *self);
typedef void (__thiscall *place_4B2720)(void *self, void *a, void *pos);

#define LS (*(void **)d_008D122C)
#define REG (-10000)
#define VF(o, off) ((*(void ***)(o))[(off) / 4])

/* the scene's object list (+0x80) takes p */
static void add_4B2720(char *this, void *p)
{
    void *list = *(void **)(this + 0x80);
    ((vfp_4B2720)VF(list, 4))(list, p);
}

DECOMP(004B2720)
void *__thiscall f_004B2720(void *self, int a, void *list)
{
    char *this = (char *)self, *hero, *cr;
    void **model = (void **)(this + 0x74);
    unsigned int ebx;
    Str_4B2720 skin, name;
    Tbl_4B2720 skins, anim, glow;
    unsigned int it[3];
    void *mem, *p;

    sub_004B20D0(this, a);
    *(void **)(this + 0x80) = list;
    *(void **)this = d_006109BC;
    *(void **)(this + 4) = d_0061099C;
    *model = 0;
    imp_006072F8(this + 0x1c, d_00610AFC);
    hero = sub_00425F60();
    ((vf0_4B2720)VF(hero, 0x18))(hero);
    ebx = (unsigned int)(size_t)(hero + 8);
    {
        Str_4B2720 k;
        Tbl_4B2720 h;
        Ref_4B2720 r1;
        RefC_4B2720 r2;
        imp_00607334(&k, hero + 8);
        sub_00463AD0(sub_004648E0(sub_0045C740(sub_004323E0(&h, d_0060C080), &r1, k), &r2, d_0060C0E0), ebx,
                     &skin);
        sub_004220A0(&r2.t);
        imp_00607330(&r1.key);
        sub_004220A0(&h);
    }
    {
        Str_4B2720 k1, k2;
        Tbl_4B2720 h, t;
        Ref_4B2720 r1;
        RefC_4B2720 r2;
        RefS_4B2720 r3;
        imp_00607334(&k2, &skin);
        imp_00607334(&k1, hero + 8);
        sub_004491F0(sub_00464970(sub_004648E0(sub_0045C740(sub_004323E0(&h, d_0060C080), &r1, k1), &r2,
                                               d_0060C130), &r3, k2), &t);
        sub_00435D90(&skins, &t);
        sub_004220A0(&t);
        imp_00607330(&r3.k);
        sub_004220A0(&r3.t);
        sub_004220A0(&r2.t);
        imp_00607330(&r1.key);
        sub_004220A0(&h);
    }
    {
        struct { void *t; const char *k; } ref;
        RefC_4B2720 r1;
        RefI_4B2720 r2;
        Tbl_4B2720 t;
        ref.t = &skins;
        ref.k = d_0060C138;
        sub_004B2670(sub_004B2690(sub_0044D030(&ref, &r1, d_00610AF0), &r2, 1), &t);
        sub_00435D90(&anim, &t);
        sub_004220A0(&t);
        sub_004220A0(&r2.t);
        sub_004220A0(&r1.t);
    }
    {
        struct { void *t; const char *k; } ref;
        Tbl_4B2720 t;
        ref.t = &skins;
        ref.k = d_00610AE0;
        sub_004369F0(&ref, &t);
        sub_00435D90(&glow, &t);
        sub_004220A0(&t);
    }
    imp_006071E0(&name);
    {
        struct { void *t; int i; } k;
        Str_4B2720 s;
        k.t = &anim;
        k.i = 1;
        imp_0060731C(&name, sub_0045BB70(&k, ebx, &s));
        imp_00607330(&s);
    }
    sub_0057AC90(&anim, 2);
    sub_0057AC90(&anim, 5);

    mem = sub_005E3EAE(0x204);
    if (mem) {
        Str_4B2720 c;
        imp_00607324(&c, d_0060C118);
        p = sub_0042A530(mem, &name, sub_0042A0D0(&name, &c, 1), 1);
        *model = p;
        add_4B2720(this, p);
        imp_00607330(&c);
    } else {
        *model = 0;
        add_4B2720(this, 0);
    }
    mem = sub_005E3EAE(0x1cc);
    *(void **)(this + 0x7c) = mem ? sub_004B2430(mem, *model) : 0;
    {
        float *pos = ((vfv_4B2720)VF(hero, 0x68))(hero);
        cr = (char *)*model;
        *(int *)(cr + 0x58) = *(int *)(cr + 0x64);
        *(int *)(cr + 0x5c) = *(int *)(cr + 0x68);
        *(int *)(cr + 0x60) = *(int *)(cr + 0x6c);
        __builtin_memcpy(cr + 0x64, pos, 12);
        cr[0x70] = 1;
        cr = (char *)*model;
        __builtin_memcpy(cr + 0x74, hero + 0x74, 12);
        cr[0x80] = 1;
        cr = (char *)*model;
        *(float *)(cr + 0x98) = *(float *)d_00608A70;
        *(float *)(cr + 0x9c) = *(float *)d_00608A70;
        *(float *)(cr + 0xa0) = *(float *)d_00608A70;
        cr[0xa4] = 1;
        cr = (char *)*model;
        ((vf0_4B2720)VF(cr, 0x18))(cr);
        ((char *)*model)[0x1e4] = 1;
    }
    mem = sub_005E3EAE(0x324);
    if (mem) {
        Str_4B2720 sa, sb;
        imp_00607324(&sa, d_0060C2E8);
        imp_00607324(&sb, d_0060C2D8);
        p = sub_004EC6F0(mem, model, *model, 1, sb, sa);
    } else
        p = 0;
    *(void **)(this + 0x78) = p;
    add_4B2720(this, p);

    sub_00403390(LS, REG, (int)glow.w[2]);
    it[1] = 0;
    it[0] = (unsigned int)(size_t)d_0060B97C;
    sub_00403080(LS);
    *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
    while (!*(unsigned char *)&it[2]) {
        Tbl_4B2720 val;
        Str_4B2720 s;
        char *ps;
        float h, *hp, pos[3];
        int n;
        sub_0045C850(&val);
        mem = sub_005E3EAE(0x690);
        if (mem) {
            Str_4B2720 bp;
            imp_00607324(&bp, d_00609234);
            ps = sub_00550420(mem, &bp, 0, 0);
            imp_00607330(&bp);
        } else
            ps = 0;
        sub_0054EA10(ps, sub_0057AFB0(&val, 0x34, &s, 4));
        imp_00607330(&s);
        n = (int)(long long)sub_0057AC90(&val, 1);
        sub_0054FE30(ps, n, 0.0f);
        h = sub_0057AC90(&val, 2);
        hp = ((vfv_4B2720)VF(hero, 0x68))(hero);
        pos[0] = (float)(hp[0] + 0.0f);
        pos[1] = (float)((long double)hp[1] + h);
        pos[2] = (float)(0.0f + hp[2]);
        ((place_4B2720)*(void **)(ps + 0x2f4))(*(void **)(ps + 0x2f8), ps + 0x2e4, pos);
        add_4B2720(this, ps);
        sub_004220A0(&val);
        sub_00402A70(LS, -2);
        *(unsigned char *)&it[2] = sub_00403B00(LS, -2) == 0;
    }
    ((vf0_4B2720)VF(hero, 0x50))(hero);
    sub_0045C920(it);
    imp_00607330(&name);
    sub_004220A0(&glow);
    sub_004220A0(&anim);
    sub_004220A0(&skins);
    imp_00607330(&skin);
    return this;
}
