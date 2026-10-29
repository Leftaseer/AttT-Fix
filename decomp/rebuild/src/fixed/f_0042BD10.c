/* 0x0042BD10: the army screen's set-up (origin +0xB0 / +0xB4): its 3D view (+0x78), the yellow Century Gothic font
 * (+0x7C), the back buffer picture (+0x80 / +0xA0) shown at double size, the text panel (+0x84) with the
 * AS_maskSelect.bmp selection mask (+0xA4), the input (+0x8C, +0x90), the Use / Default / ExitBlue buttons
 * (+0x94..+0x9C), eleven troop slots (+0x170.., 0x00473FD0, keys 110..210), the dismiss troop / unit buttons
 * (+0xA8, +0xAC, 0x00473720), the selection choice (+0x88), the slot rectangles (+0xD4..+0x150) moved by the
 * origin, the AS_SelectionLevel1..5 pictures (+0xDC..+0x154), the soldier and level pictures (+0x15C, +0x160,
 * +0x164) and the denied places mark (+0x16C / +0x168) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_42BD10;                 /* std::string */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_004AF7A0(void *self);
DECOMP_C int __cdecl sub_004AD530(void *self, unsigned int eax);
DECOMP_C void *__thiscall sub_00457510(void *self);
DECOMP_C void __thiscall sub_00457600(void *self, float a, float b, float size, float d, void *font, void *tex);
DECOMP_C int __thiscall sub_004205C0(void *self, void *child);
DECOMP_C char *__cdecl sub_00421730(void);
DECOMP_C void *__thiscall sub_0047A120(void *self, void *name);
DECOMP_C void *__thiscall sub_00473F10(void *self);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C void *__thiscall sub_004207C0(void *self, void *name);
DECOMP_C void *__thiscall sub_004740C0(void *self, void *name);
DECOMP_C void __cdecl sub_00473D20(void *self, unsigned int eax, unsigned int tex);
DECOMP_C void __thiscall sub_00473AD0(void *self, unsigned int x, unsigned int y);
DECOMP_C char *__thiscall sub_00473FD0(void *self, void *scene);
DECOMP_C void __thiscall sub_00473AC0(void *self, void *choice, int key);
DECOMP_C void *__cdecl sub_0042B720(void *fn, int a);
DECOMP_C char *__thiscall sub_00473720(void *self, void *scene, void *name, void *tex, void *tex_s, void *tex_n);
DECOMP_C void *__thiscall sub_004DF920(void *self, void *name, int a);
DECOMP_C char d_00608A88[], d_00608A78[], d_00608A74[], d_00608A70[], d_00607C14[], d_00607C08[], d_00608A6C[],
    d_00607C00[], d_00607BF4[], d_00608A58[], d_0042BC70[], d_0042BC90[], d_0042B790[], d_00608A54[], d_00608A40[],
    d_00608A28[], d_00608A10[], d_00608A00[], d_00608A08[], d_0055CFD0[], d_006089E8[], d_006089D0[], d_006089B8[],
    d_006089B0[], d_0042B770[], d_00483980[], d_006089A8[], d_006089A0[], d_00608998[], d_00608994[], d_00608990[],
    d_0060898C[], d_00608988[], d_00608984[], d_00608980[], d_0060897C[], d_00608978[], d_00608974[], d_00608970[],
    d_0060896C[], d_00608968[], d_00608954[], d_0060894C[], d_00608944[], d_0060893C[], d_00608934[], d_0060892C[],
    d_0060891C[], d_0060890C[], d_006088F8[], d_006088F0[], d_006088E8[], d_006088D0[], d_006088C8[], d_0068AE18[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
typedef void (__thiscall *vfp_42BD10)(void *self, void *p);
typedef void (__thiscall *vfs_42BD10)(void *self, void *name, int a);
typedef void *(__thiscall *vfr_42BD10)(void *self);
typedef void (__thiscall *reg_42BD10)(void *self, void *name, void *o);
typedef void (__thiscall *pos_42BD10)(void *self, float x, float y);
typedef void (__thiscall *vff_42BD10)(void *self, float v);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define F(o) (*(float *)(this + (o)))
#define P(o) (*(void **)(this + (o)))
#define D(a) (*(double *)(a))

static void *named_42BD10(int size, void *(__thiscall *ctor)(void *, void *), const char *name)
{
    void *mem = sub_005E3EAE(size), *o = 0;
    if (mem) {
        Str_42BD10 s;
        imp_00607324(&s, name);
        o = ctor(mem, &s);
        imp_00607330(&s);
    }
    return o;
}

static void *picture_42BD10(const char *name)
{
    void *mem = sub_005E3EAE(0x54), *o = 0;
    if (mem) {
        Str_42BD10 s;
        imp_00607324(&s, name);
        o = sub_004DF920(mem, &s, 0);
        imp_00607330(&s);
    }
    return o;
}

/* the picture "<base><suffix>" */
static void *level_42BD10(Str_42BD10 *base, const char *suffix)
{
    void *mem = sub_005E3EAE(0x54), *o = 0;
    if (mem) {
        Str_42BD10 s;
        imp_006071DC(&s, base, suffix);
        o = sub_004DF920(mem, &s, 0);
        imp_00607330(&s);
    }
    return o;
}

static void add_42BD10(char *this, void *o)
{
    char *l = this + 4;
    ((vfp_42BD10)VF(l, 4))(l, o);
}

/* the handlers c, 0x10 and 0x14 of a choice */
static void handlers_42BD10(char *o, void *c, void *a, void *b)
{
    *(void **)(o + 0xc) = sub_0042B720(c, 0);
    *(void **)(o + 0x10) = sub_0042B720(a, 0);
    *(void **)(o + 0x14) = sub_0042B720(b, 0);
}

/* a dismiss button at +slot (pictures name, tex, tex_s, tex_n) on key, placed at the origin plus (dx, dy) */
static void dismiss_42BD10(char *this, int slot, Str_42BD10 *s, int key, double dx, double dy, int id)
{
    void *mem = sub_005E3EAE(0x288);
    char *b = mem ? sub_00473720(mem, this, &s[0], &s[1], &s[2], &s[3]) : 0;
    float x, y;
    P(slot) = b;
    add_42BD10(this, b ? b + 0x54 : 0);
    sub_00473AC0(P(0x84), P(slot), key);
    b = (char *)P(slot);
    y = (float)(F(0xb4) + dy);
    x = (float)(F(0xb0) + dx);
    ((pos_42BD10)VF(b + 0x54, 0x68))(b + 0x54, x, y);
    b = (char *)P(slot);
    *(int *)(b + 0x50) = id;
    *(void **)(b + 0xc) = sub_0042B720(d_0055CFD0, 0);
    *(void **)((char *)P(slot) + 0x10) = sub_0042B720(d_0042BC90, 0);
    *(void **)((char *)P(slot) + 0x14) = sub_0042B720(d_0042B790, 0);
}

DECOMP(0042BD10)
void __thiscall f_0042BD10(void *self)
{
    char *this = (char *)self;
    void *mem;
    Str_42BD10 bs[4], sel;
    int i;

    mem = sub_005E3EAE(0x84);
    {
        void *v = mem ? sub_004AF7A0(mem) : 0;
        P(0x78) = v;
        sub_004AD530(v, (unsigned int)(size_t)v);
    }
    mem = sub_005E3EAE(0x2bc);
    P(0x7c) = mem ? sub_00457510(mem) : 0;
    {
        Str_42BD10 tex, font;
        imp_00607324(&tex, d_00608A88);
        imp_00607324(&font, d_00608A78);
        sub_00457600(P(0x7c), *(float *)d_00608A70, *(float *)d_00608A70, *(float *)d_00608A74, 1.0f, &font, &tex);
        imp_00607330(&font);
        imp_00607330(&tex);
    }
    sub_004205C0(this, P(0x7c));
    P(0x80) = sub_00421730();
    P(0xa0) = named_42BD10(0x224, sub_0047A120, d_00607C14);
    {
        Str_42BD10 s;
        void *bb = P(0xa0), *e;
        float w;
        imp_00607324(&s, d_00607C14);
        ((vfs_42BD10)VF(bb, 0x2c))(bb, &s, 1);
        imp_00607330(&s);
        imp_00607324(&s, d_00607C08);
        e = ((vfr_42BD10)VF(P(0xa0), 0x30))(P(0xa0));
        ((reg_42BD10)VF(e, 0xc))(e, &s, ((void **)P(0x80))[1]);
        imp_00607330(&s);
        bb = P(0xa0);
        ((pos_42BD10)VF(bb, 0x94))(bb, 0.0f, 0.0f);
        bb = P(0xa0);
        w = *(float *)((char *)bb + 0x74);
        ((vff_42BD10)VF(bb, 0x9c))(bb, w + w);
        bb = P(0xa0);
        w = *(float *)((char *)bb + 0x78);
        ((vff_42BD10)VF(bb, 0xa0))(bb, w + w);
        add_42BD10(this, P(0xa0));
    }
    mem = sub_005E3EAE(0x458);
    P(0x84) = mem ? sub_00473F10(mem) : 0;
    sub_004205C0(this, P(0x84));
    P(0x8c) = sub_00421680();
    P(0x90) = sub_004215D0();
    P(0x94) = named_42BD10(0x5c, sub_004207C0, d_00608A6C);
    P(0x98) = named_42BD10(0x5c, sub_004207C0, d_00607C00);
    P(0x9c) = named_42BD10(0x5c, sub_004207C0, d_00607BF4);
    P(0xa4) = named_42BD10(0x1c, sub_004740C0, d_00608A58);
    sub_00473D20(P(0x84), (unsigned int)(size_t)P(0xa4), (unsigned int)(size_t)P(0xa4));
    {
        unsigned int y = (unsigned int)(long long)F(0xb4), x = (unsigned int)(long long)F(0xb0);
        sub_00473AD0(P(0x84), x, y);
    }
    for (i = 0; i < 11; i++) {
        char *o;
        mem = sub_005E3EAE(0x54);
        o = mem ? sub_00473FD0(mem, this) : 0;
        P(0x170 + i * 4) = o;
        sub_00473AC0(P(0x84), o, 0x6e + 10 * i);
        o = (char *)P(0x170 + i * 4);
        *(void **)(o + 0xc) = sub_0042B720(d_0042BC70, 0);
        *(void **)((char *)P(0x170 + i * 4) + 0x10) = sub_0042B720(d_0042BC90, 0);
        *(void **)((char *)P(0x170 + i * 4) + 0x14) = sub_0042B720(d_0042B790, 0);
        *(int *)((char *)P(0x170 + i * 4) + 0x50) = i;
    }
    imp_00607324(&bs[0], d_00608A54);
    imp_00607324(&bs[1], d_00608A40);
    imp_00607324(&bs[2], d_00608A28);
    imp_00607324(&bs[3], d_00608A10);
    dismiss_42BD10(this, 0xa8, bs, 0x32, D(d_00608A00), D(d_00608A08), 0xb);
    imp_006072F8(&bs[0], d_00608A54);
    imp_006072F8(&bs[1], d_006089E8);
    imp_006072F8(&bs[2], d_006089D0);
    imp_006072F8(&bs[3], d_006089B8);
    dismiss_42BD10(this, 0xac, bs, 0x3c, D(d_00608A00), D(d_006089B0), 0xc);
    mem = sub_005E3EAE(0x54);
    {
        char *o = mem ? sub_00473FD0(mem, this) : 0;
        P(0x88) = o;
        sub_00473AC0(P(0x84), o, 0);
        *(void **)((char *)P(0x88) + 0x10) = sub_0042B720(d_0042B770, 0);
        *(void **)((char *)P(0x88) + 0x14) = sub_0042B720(d_0042B790, 0);
        *(void **)((char *)P(0x88) + 0xc) = sub_0042B720(d_00483980, 0);
    }
    {
        static const short xs[] = { 0xd4, 0xe0, 0xec, 0xf8, 0x104, 0x110, 0x11c, 0x128, 0x134, 0x140, 0x14c };
        double c = D(d_006089A0);
        F(0xd4) = *(float *)d_006089A8;
        F(0xd8) = *(float *)d_00608990;
        F(0xe4) = *(float *)d_00608990;
        F(0xf0) = *(float *)d_00608990;
        F(0xfc) = *(float *)d_00608990;
        F(0x104) = *(float *)d_0060898C;
        F(0x108) = *(float *)d_00608988;
        F(0x114) = *(float *)d_00608988;
        F(0x120) = *(float *)d_00608988;
        F(0x128) = *(float *)d_00608984;
        F(0x12c) = *(float *)d_00608980;
        F(0x138) = *(float *)d_00608980;
        F(0x140) = *(float *)d_0060897C;
        F(0xf8) = *(float *)d_00608998;
        F(0x144) = *(float *)d_00608978;
        F(0xe0) = *(float *)d_00608994;
        F(0x110) = *(float *)d_00608974;
        F(0x14c) = *(float *)d_00608970;
        F(0xec) = *(float *)d_0060896C;
        F(0x11c) = *(float *)d_00608968;
        F(0x134) = *(float *)d_0060896C;
        F(0x150) = *(float *)d_00608A74;
        for (i = 0; i < 11; i++) {
            float dx = (float)(c - F(0xb0)), dy;
            F(xs[i]) = F(xs[i]) - dx;
            dy = (float)(c - F(0xb4));
            F(xs[i] + 4) = F(xs[i] + 4) - dy;
        }
    }
    imp_00607324(&sel, d_00608954);
    P(0xdc) = level_42BD10(&sel, d_0060894C);
    P(0xe8) = P(0xdc);
    P(0xf4) = P(0xdc);
    P(0x100) = P(0xdc);
    P(0x10c) = level_42BD10(&sel, d_00608944);
    P(0x118) = P(0x10c);
    P(0x124) = P(0x10c);
    P(0x130) = level_42BD10(&sel, d_0060893C);
    P(0x13c) = P(0x130);
    P(0x148) = level_42BD10(&sel, d_00608934);
    P(0x154) = level_42BD10(&sel, d_0060892C);
    P(0xd0) = named_42BD10(0x224, sub_0047A120, d_0060891C);
    P(0x15c) = picture_42BD10(d_0060890C);
    P(0x160) = picture_42BD10(d_006088F8);
    P(0x164) = named_42BD10(0x224, sub_0047A120, d_0060891C);
    {
        float pos[2];
        void *s = P(0x164);
        pos[0] = (float)(F(0xb0) + D(d_006088F0));
        pos[1] = (float)(F(0xb4) + D(d_006088E8));
        ((vfp_42BD10)VF(s, 0x6c))(s, pos);
        add_42BD10(this, P(0x164));
    }
    P(0x16c) = picture_42BD10(d_006088D0);
    P(0x168) = named_42BD10(0x224, sub_0047A120, d_0060891C);
    {
        float pos[2];
        void *s = P(0x168);
        ((vfp_42BD10)VF(s, 0x34))(s, P(0x16c));
        pos[0] = (float)(F(0xb0) + D(d_006088C8));
        pos[1] = (float)(F(0xb4) + D(d_0068AE18));
        s = P(0x168);
        ((vfp_42BD10)VF(s, 0x6c))(s, pos);
        s = P(0x168);
        ((pos_42BD10)VF(s, 0x94))(s, 0.0f, 0.0f);
        add_42BD10(this, P(0x168));
    }
    add_42BD10(this, P(0x78));
    imp_00607330(&sel);
    imp_00607330(&bs[3]);
    imp_00607330(&bs[2]);
    imp_00607330(&bs[1]);
    imp_00607330(&bs[0]);
}
