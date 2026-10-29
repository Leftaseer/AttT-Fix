/* 0x0042CFE0: CArmyScreenScene vf2 (start): the base (0x004B1B20), the army is refreshed between the checker
 * calls (0x0043A280..0x0043A310 around the argument's vf18, 0x00430350 / 0x00430430 on +0x80), the page set
 * (0x0042BB90) and the cursor shown; the hero's rank (0x00425F60 +0x1D8: 0Soldier .. 9Imperor) names the
 * "AS_Lines" picture (+0xB8 / +0xBC, none for a soldier), the "AS_PlacesAccessed" picture (+0xC0 / +0xC4, both at
 * +0xB0 + (190, 41) by 0x006088C8 / 0x0068AE18) and the "AS_TWarrior" picture (+0xC8 / +0xCC, at +0xD4 + 12 * page);
 * all are added to the layer with the panel +0xD0. Returns what 0x0043A310 returns */
/* @conv ECX 4 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_42CFE0;                 /* std::string */
typedef struct { unsigned int w[0x230 / 4]; } Chk_42CFE0;
DECOMP_C void __thiscall sub_004B1B20(void *self, void *arg);
DECOMP_C void __thiscall sub_0043A280(void *self);
DECOMP_C void __thiscall sub_00430350(void *self);
DECOMP_C void __thiscall sub_0043A320(void *self);
DECOMP_C void __thiscall sub_00430430(void *self);
DECOMP_C unsigned char __cdecl sub_0042BB10(void);
DECOMP_C void __thiscall sub_0042BB90(void *self, int page);
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C int __thiscall sub_0043A310(void *self);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C void *__thiscall sub_004DF920(void *self, void *name, int a);
DECOMP_C void *__thiscall sub_0047A120(void *self, void *name);
DECOMP_C char d_00608B30[], d_00608B08[], d_00608AFC[], d_00608AF0[], d_00608AE4[], d_00608AD8[], d_00608ACC[],
    d_00608AC4[], d_00608ABC[], d_00608AB0[], d_00608AA4[], d_00608B14[], d_0060891C[], d_006088C8[], d_0068AE18[],
    d_00608B1C[], d_00608A98[];
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__cdecl *imp_006071C0)(void *, const void *, const void *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@0@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
typedef void (__thiscall *vf0_42CFE0)(void *self);
typedef void (__thiscall *vf1_42CFE0)(void *self, void *a);
typedef void (__thiscall *vff_42CFE0)(void *self, float a, float b);

#define VT(o) (*(void ***)(o))

/* texture prefix + rank + ".tga" */
static void *tex_42CFE0(const char *prefix, void *rank)
{
    void *mem = sub_005E3EAE(0x54), *t = 0;
    if (mem) {
        Str_42CFE0 s1, s2, s3;
        imp_00607324(&s1, prefix);
        t = sub_004DF920(mem, imp_006071DC(&s3, imp_006071C0(&s2, &s1, rank), d_00608B14), 0);
        imp_00607330(&s3);
        imp_00607330(&s2);
        imp_00607330(&s1);
    }
    return t;
}

/* a "Default2DAlpha" picture of the texture at the position, added to the layer */
static void *pic_42CFE0(void)
{
    void *mem = sub_005E3EAE(0x224), *p = 0;
    if (mem) {
        Str_42CFE0 s;
        imp_00607324(&s, d_0060891C);
        p = sub_0047A120(mem, &s);
        imp_00607330(&s);
    }
    return p;
}

static void show_42CFE0(char *this, void *p, void *tex, float *pos)
{
    void *layer = this + 4;
    ((vf1_42CFE0)VT(p)[0x34 / 4])(p, tex);
    ((vf1_42CFE0)VT(p)[0x6c / 4])(p, pos);
    ((vff_42CFE0)VT(p)[0x94 / 4])(p, 0.0f, 0.0f);
    ((vf1_42CFE0)VT(layer)[0xc / 4])(layer, p);
}

DECOMP(0042CFE0)
int __thiscall f_0042CFE0(char *this, void *arg)
{
    static char *const ranks[10] = { d_00608B30, d_00608B08, d_00608AFC, d_00608AF0, d_00608AE4, d_00608AD8,
                                     d_00608ACC, d_00608AC4, d_00608ABC, d_00608AB0 };
    Chk_42CFE0 chk;
    Str_42CFE0 rank;
    unsigned int r;
    float pos[2];
    void *cur;

    sub_004B1B20(this, arg);
    sub_0043A280(&chk);
    sub_00430350(*(void **)(this + 0x80));
    ((vf0_42CFE0)VT(arg)[0x18 / 4])(arg);
    sub_0043A320(&chk);
    sub_00430430(*(void **)(this + 0x80));
    sub_0042BB90(this, sub_0042BB10());
    cur = *(void **)(this + 0x8c);
    ((vf1_42CFE0)VT(cur)[0xe8 / 4])(cur, *(void **)(this + 0x98));
    r = *(unsigned int *)(sub_00425F60() + 0x1d8);
    imp_006071E0(&rank);
    if (r <= 9)
        imp_006072F8(&rank, ranks[r]);
    if (r == 0) {
        *(void **)(this + 0xb8) = 0;
        *(void **)(this + 0xbc) = 0;
    } else {
        *(void **)(this + 0xb8) = tex_42CFE0(d_00608AA4, &rank);
        *(void **)(this + 0xbc) = pic_42CFE0();
        pos[0] = (float)(*(float *)(this + 0xb0) + *(double *)d_006088C8);
        pos[1] = (float)(*(float *)(this + 0xb4) + *(double *)d_0068AE18);
        show_42CFE0(this, *(void **)(this + 0xbc), *(void **)(this + 0xb8), pos);
    }
    *(void **)(this + 0xc0) = tex_42CFE0(d_00608B1C, &rank);
    *(void **)(this + 0xc4) = pic_42CFE0();
    pos[0] = (float)(*(float *)(this + 0xb0) + *(double *)d_006088C8);
    pos[1] = (float)(*(float *)(this + 0xb4) + *(double *)d_0068AE18);
    show_42CFE0(this, *(void **)(this + 0xc4), *(void **)(this + 0xc0), pos);
    {
        void *layer = this + 4;
        ((vf1_42CFE0)VT(layer)[0xc / 4])(layer, *(void **)(this + 0xd0));
    }
    *(void **)(this + 0xc8) = tex_42CFE0(d_00608A98, &rank);
    *(void **)(this + 0xcc) = pic_42CFE0();
    {
        void *p = *(void **)(this + 0xcc), *layer = this + 4;
        ((vf1_42CFE0)VT(p)[0x34 / 4])(p, *(void **)(this + 0xc8));
        ((vf1_42CFE0)VT(p)[0x6c / 4])(p, this + 0xd4 + sub_0042BB10() * 12);
        ((vff_42CFE0)VT(p)[0x94 / 4])(p, 0.0f, 0.0f);
        ((vf1_42CFE0)VT(layer)[0xc / 4])(layer, *(void **)(this + 0xcc));
    }
    imp_00607330(&rank);
    return sub_0043A310(&chk);
}
