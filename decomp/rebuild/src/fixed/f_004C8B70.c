/* 0x004C8B70: the spell book scene's set-up (SpellBookScene.cpp): 0x004C8650, the SpellBook_AddSpell Lua function,
 * the back buffer picture (+0xA0), the view (+0x78), the book (+0xB8, 0x004C6450), two pictures (+0x28C, +0x290)
 * and the white-blue text (+0x294) centred on the book's page, the four page masks (+0xA4 vector), the panel
 * (+0xB4) with the page choice (+0x264) and the four page tabs (+0x254 vector, keys 30..60), the input (+0x84,
 * +0x88), the Use / Default / CastSpell / CastSpellInactive / ExitRed buttons (+0x8C..+0x9C); the known spells
 * (0x004C7A60, 4 elements x 10) get from SpellIconPos.dat (three page offsets per element, a position per spell)
 * their icon (+0xBC.., 0x004C6640 with <element><nn>.bik / Glow.bik) and logo (+0x188.., 0x004C5DC0 with
 * <element><nn>.tga, <element>Appearance.bik, <element>Glow.bik), all added to the scene (+4). A missing file
 * throws */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4C8B70;                 /* std::string */
DECOMP_C void __thiscall sub_004C8650(void *self);
DECOMP_C void __cdecl sub_004031F0(void *L, void *fn, int n);      /* lua_pushcclosure */
DECOMP_C void __cdecl sub_004034F0(void *L, int idx, const char *k);   /* lua_setfield */
DECOMP_C char *__cdecl sub_00421730(void);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_0047A120(void *self, void *name);
DECOMP_C void *__thiscall sub_004AF7A0(void *self);
DECOMP_C int __cdecl sub_004AD530(void *self, unsigned int eax);
DECOMP_C void *__thiscall sub_004C6450(void *self);
DECOMP_C void *__thiscall sub_004AD9B0(void *self);
DECOMP_C unsigned int *__thiscall sub_004B0290(void *self, float x, float y, float size, void *text, void *font,
                                               int align, int a, void *color, float scale, int b, int c);
DECOMP_C void *__thiscall sub_004740C0(void *self, void *name);
DECOMP_C void __thiscall sub_00487860(void *self, void *where, unsigned int n, void *val);
DECOMP_C void *__thiscall sub_00473F10(void *self);
DECOMP_C void __thiscall sub_00473AD0(void *self, unsigned int x, unsigned int y);
DECOMP_C int __thiscall sub_004205C0(void *self, void *child);
DECOMP_C char *__thiscall sub_00473FD0(void *self, void *scene);
DECOMP_C void __thiscall sub_00473AC0(void *self, void *choice, int key);
DECOMP_C void *__cdecl sub_004C6D30(void *fn, int a);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C void *__thiscall sub_004207C0(void *self, void *name);
DECOMP_C void __stdcall sub_004C7A60(char *known);
DECOMP_C void __thiscall sub_00459290(void *self, void *name, int a);
DECOMP_C void __thiscall sub_00459170(void *self);
DECOMP_C void __thiscall sub_00421220(void *exc, void *msg, const char *file, int line);
DECOMP_C void __stdcall sub_005E3EC0(void *obj, void *throw_info);      /* _CxxThrowException */
DECOMP_C void *__thiscall sub_004C6640(void *self, void *scene, void *video, void *glow);
DECOMP_C void *__thiscall sub_004C5DC0(void *self, void *scene, void *tex, void *appear, void *glow, void *n1, void *n2,
                                       void *n3, int a);
DECOMP_C void __thiscall sub_004C6290(void *self, float *pts);
DECOMP_C void __stdcall sub_005E4134(void *p, unsigned int size, int n, void *dtor);
DECOMP_C char d_008D122C[], d_004C8950[], d_00611CA8[], d_00607C14[], d_00607C08[], d_006C895C[], d_006C8958[],
    d_00607CE0[], d_0060B7B8[], d_00608A78[], d_0060FA8B[], d_00608A74[], d_00611C90[], d_00611C74[], d_00611C5C[],
    d_00611C40[], d_00611C38[], d_004C6C30[], d_004C6D10[], d_004C6C50[], d_004C6F50[], d_004C6C10[], d_00608A6C[],
    d_00607C00[], d_0060A45C[], d_0060A448[], d_0060A49C[], d_00611BC4[], d_00611BBC[], d_00611BB8[], d_00611BB0[],
    d_00611BA8[], d_00611B34[], d_00611B04[], d_00611AEC[], d_0069916C[], d_00611BA0[], d_00611B94[], d_00611B8C[],
    d_004C74E0[], d_00611B7C[], d_00611B68[], d_00611B5C[], d_00611B54[], d_00611B48[], d_00608B14[], d_004C75B0[],
    d_004C6C80[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__cdecl *imp_006071DC)(void *, const void *, const char *) __asm__("__imp_??$?HDU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA?AV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@ABV10@PBD@Z");
DECOMP_C void (__thiscall *imp_00607364)(void *, const void *, int, int) __asm__("__imp_??0?$basic_stringstream@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@1@H@Z");
DECOMP_C void (__thiscall *imp_00607360)(void *) __asm__("__imp_??_D?$basic_stringstream@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEXXZ");
DECOMP_C void *(__thiscall *imp_006072EC)(void *, float *) __asm__("__imp_??5?$basic_istream@DU?$char_traits@D@std@@@std@@QAEAAV01@AAM@Z");
DECOMP_C int (__cdecl *imp_sprintf)(char *, const char *, ...) __asm__("__imp__sprintf");
typedef void (__thiscall *vfp_4C8B70)(void *self, void *p);
typedef void (__thiscall *vfsi_4C8B70)(void *self, void *s, int a);
typedef void *(__thiscall *vfr_4C8B70)(void *self);
typedef void (__thiscall *vfsp_4C8B70)(void *self, void *s, void *p);
typedef void (__thiscall *vfff_4C8B70)(void *self, float x, float y);
typedef unsigned int (__thiscall *vfu_4C8B70)(void *self);
typedef float (__thiscall *vff_4C8B70)(void *self);
typedef void (__thiscall *vf0_4C8B70)(void *self);
typedef float *(__thiscall *vfpt_4C8B70)(void *self);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define P(o) (*(void **)(this + (o)))
#define C(o) (*(char **)(this + (o)))
#define FL(a) (*(float *)(a))
#define D(a) (*(double *)(a))
#define LS (*(void **)d_008D122C)

/* the book's current page picture */
static char *page_4C8B70(char *this)
{
    char *pg = *(char **)(C(0xb8) + 0x224);
    return (*(char ***)(pg + 0x38))[*(int *)(pg + 0x40)];
}

static unsigned int page_h_4C8B70(char *this)
{
    char *t = page_4C8B70(this);
    return ((vfu_4C8B70)VF(t, 0x14))(t);
}

static unsigned int page_w_4C8B70(char *this)
{
    char *t = page_4C8B70(this);
    return ((vfu_4C8B70)VF(t, 0x10))(t);
}

/* o placed so that the page picture is centred on the screen */
static void centre_4C8B70(char *this, char *o)
{
    unsigned int h = page_h_4C8B70(this), w = page_w_4C8B70(this);
    float y = (float)(((long double)FL(d_006C8958) - (long double)h) * D(d_00607CE0));
    float x = (float)(((long double)FL(d_006C895C) - (long double)w) * D(d_00607CE0));
    ((vfff_4C8B70)VF(o, 0x68))(o, x, y);
}

/* push_back into the pointer vector at vec */
static void push_4C8B70(char *vec, void *v)
{
    void **b = *(void ***)(vec + 4);
    unsigned int n = b ? (unsigned int)(*(void ***)(vec + 8) - b) : 0;
    if (b && n < (unsigned int)(*(void ***)(vec + 0xc) - b)) {
        **(void ***)(vec + 8) = v;
        *(void ***)(vec + 8) += 1;
    } else
        sub_00487860(vec, *(void **)(vec + 8), 1, &v);
}

static void *mask_4C8B70(const char *name)
{
    void *mem = sub_005E3EAE(0x1c), *o = 0;
    if (mem) {
        Str_4C8B70 s;
        imp_00607324(&s, name);
        o = sub_004740C0(mem, &s);
        imp_00607330(&s);
    }
    return o;
}

static void *button_4C8B70(const char *name)
{
    void *mem = sub_005E3EAE(0x5c), *o = 0;
    if (mem) {
        Str_4C8B70 s;
        imp_00607324(&s, name);
        o = sub_004207C0(mem, &s);
        imp_00607330(&s);
    }
    return o;
}

/* a spell's icon (slot) and logo (slot + 0xCC) of element name, number k, at (x, y); pts are the pages' offsets */
static void spell_4C8B70(char *this, char **slot, Str_4C8B70 *name, int k, float x, float y, float *pts)
{
    char num[32];
    void *mem;
    char *icon, *b;
    imp_sprintf(num, d_00611BA0, k + 1);
    mem = sub_005E3EAE(0x288);
    if (mem) {
        Str_4C8B70 t1, t2, t3, t4;
        imp_006071DC(&t1, name, num);
        imp_006071DC(&t2, &t1, d_00611B94);
        imp_006071DC(&t3, name, num);
        imp_006071DC(&t4, &t3, d_00611B8C);
        slot[0] = (char *)sub_004C6640(mem, this, &t4, &t2);
        imp_00607330(&t4);
        imp_00607330(&t3);
        imp_00607330(&t2);
        imp_00607330(&t1);
    } else
        slot[0] = 0;
    *(void **)(slot[0] + 0x224 + 0xc) = sub_004C6D30(d_004C74E0, 0);
    *(void **)(slot[0] + 0x224 + 0x10) = sub_004C6D30(d_004C6C10, 0);
    *(void **)(slot[0] + 0x238) = sub_004C6D30(d_004C6D10, 0);
    *(int *)(slot[0] + 0x224 + 0x50) = k;
    icon = slot[0];
    b = C(0xb8);
    {
        float yy = (float)(((vff_4C8B70)VF(b, 0x90))(b) + y);
        float xx = (float)(((vff_4C8B70)VF(b, 0x8c))(b) + x);
        ((vfff_4C8B70)VF(icon, 0x68))(icon, xx, yy);
    }
    ((vf0_4C8B70)VF(slot[0], 0x50))(slot[0]);
    mem = sub_005E3EAE(0x284);
    if (mem) {
        Str_4C8B70 a, bb, c, d, e, f, h, i, j;
        imp_00607324(&a, d_00611B7C);
        imp_00607324(&bb, d_00611B68);
        imp_00607324(&c, d_00611B5C);
        imp_006071DC(&d, name, d_00611B54);
        imp_006071DC(&e, &d, d_00611B8C);
        imp_006071DC(&f, name, d_00611B48);
        imp_006071DC(&h, &f, d_00611B8C);
        imp_006071DC(&i, name, num);
        imp_006071DC(&j, &i, d_00608B14);
        slot[0x33] = (char *)sub_004C5DC0(mem, this, &j, &h, &e, &c, &bb, &a, 0);
        imp_00607330(&j);
        imp_00607330(&i);
        imp_00607330(&h);
        imp_00607330(&f);
        imp_00607330(&e);
        imp_00607330(&d);
        imp_00607330(&c);
        imp_00607330(&bb);
        imp_00607330(&a);
    } else
        slot[0x33] = 0;
    sub_004C6290(slot[0x33], pts);
    *(void **)(slot[0x33] + 0x224 + 0xc) = sub_004C6D30(d_004C75B0, 0);
    *(void **)(slot[0x33] + 0x224 + 0x10) = sub_004C6D30(d_004C6C80, 0);
    *(void **)(slot[0x33] + 0x224 + 0x14) = sub_004C6D30(d_004C6D10, 0);
    ((vf0_4C8B70)VF(slot[0x33], 0x50))(slot[0x33]);
}

DECOMP(004C8B70)
void __thiscall f_004C8B70(void *self)
{
    char *this = (char *)self, *scene = this + 4, *bb;
    void *mem;
    int i;

    sub_004C8650(this);
    sub_004031F0(LS, d_004C8950, 0);
    sub_004034F0(LS, -10002, d_00611CA8);
    this[0x268] = 0;
    *(int *)(this + 0x270) = 0;
    *(int *)(this + 0x274) = 0;
    P(0xa0) = sub_00421730();
    mem = sub_005E3EAE(0x224);
    if (mem) {
        Str_4C8B70 s;
        imp_00607324(&s, d_00607C14);
        bb = (char *)sub_0047A120(mem, &s);
        imp_00607330(&s);
    } else
        bb = 0;
    {
        Str_4C8B70 s;
        void *e;
        imp_00607324(&s, d_00607C14);
        ((vfsi_4C8B70)VF(bb, 0x2c))(bb, &s, 1);
        imp_00607330(&s);
        imp_00607324(&s, d_00607C08);
        e = ((vfr_4C8B70)VF(bb, 0x30))(bb);
        ((vfsp_4C8B70)VF(e, 0xc))(e, &s, ((void **)P(0xa0))[1]);
        imp_00607330(&s);
    }
    ((vfff_4C8B70)VF(bb, 0x94))(bb, FL(d_006C895C), FL(d_006C8958));
    ((vfp_4C8B70)VF(scene, 4))(scene, bb);
    mem = sub_005E3EAE(0x84);
    P(0x78) = mem ? sub_004AF7A0(mem) : 0;
    sub_004AD530(P(0x78), (unsigned int)(size_t)P(0x78));
    mem = sub_005E3EAE(0x230);
    P(0xb8) = mem ? sub_004C6450(mem) : 0;
    mem = sub_005E3EAE(0x254);
    P(0x28c) = mem ? sub_004AD9B0(mem) : 0;
    centre_4C8B70(this, C(0x28c));
    mem = sub_005E3EAE(0x254);
    P(0x290) = mem ? sub_004AD9B0(mem) : 0;
    centre_4C8B70(this, C(0x290));
    mem = sub_005E3EAE(0x254);
    if (mem) {
        Str_4C8B70 tex, font, text;
        imp_00607324(&tex, d_0060B7B8);
        imp_00607324(&font, d_00608A78);
        imp_00607324(&text, d_0060FA8B);
        P(0x294) = sub_004B0290(mem, 0.0f, 0.0f, FL(d_00608A74), &text, &font, 0x7c, 2, &tex, 1.0f, 0, 0);
        imp_00607330(&text);
        imp_00607330(&font);
        imp_00607330(&tex);
    } else
        P(0x294) = 0;
    ((vfp_4C8B70)VF(scene, 0xc))(scene, this + 0x298);
    push_4C8B70(this + 0xa4, mask_4C8B70(d_00611C90));
    push_4C8B70(this + 0xa4, mask_4C8B70(d_00611C74));
    push_4C8B70(this + 0xa4, mask_4C8B70(d_00611C5C));
    push_4C8B70(this + 0xa4, mask_4C8B70(d_00611C40));
    mem = sub_005E3EAE(0x458);
    P(0xb4) = mem ? sub_00473F10(mem) : 0;
    centre_4C8B70(this, C(0xb8));
    {
        unsigned int h = page_h_4C8B70(this), w = page_w_4C8B70(this);
        unsigned int y = (unsigned int)(long long)((long double)FL(d_006C8958) - (long double)h) >> 1;
        unsigned int x = (unsigned int)(long long)((long double)FL(d_006C895C) - (long double)w) >> 1;
        sub_00473AD0(P(0xb4), x, y);
    }
    {
        unsigned int h = page_h_4C8B70(this), w = page_w_4C8B70(this);
        char *b = C(0xb8), *t = C(0x294);
        float y = (float)(((vff_4C8B70)VF(b, 0x90))(b) + (long double)(h >> 1) - D(d_00611C38));
        float x = (float)(((vff_4C8B70)VF(b, 0x8c))(b) + (long double)(w >> 1));
        ((vfff_4C8B70)VF(t, 0x68))(t, x, y);
    }
    sub_004205C0(this, P(0xb4));
    mem = sub_005E3EAE(0x54);
    P(0x264) = mem ? sub_00473FD0(mem, this) : 0;
    sub_00473AC0(P(0xb4), P(0x264), 0);
    *(void **)(C(0x264) + 0x10) = sub_004C6D30(d_004C6C30, 0);
    *(void **)(C(0x264) + 0x14) = sub_004C6D30(d_004C6D10, 0);
    *(void **)(C(0x264) + 0xc) = sub_004C6D30(d_004C6C50, 0);
    {
        unsigned char key = 0x1e;
        i = 0;
        do {
            char *o;
            mem = sub_005E3EAE(0x54);
            push_4C8B70(this + 0x254, mem ? sub_00473FD0(mem, this) : 0);
            sub_00473AC0(P(0xb4), (*(void ***)(this + 0x258))[i], key);
            o = (*(char ***)(this + 0x258))[i];
            *(void **)(o + 0xc) = sub_004C6D30(d_004C6F50, 0);
            *(void **)((*(char ***)(this + 0x258))[i] + 0x10) = sub_004C6D30(d_004C6C10, 0);
            *(void **)((*(char ***)(this + 0x258))[i] + 0x14) = sub_004C6D30(d_004C6D10, 0);
            *(int *)((*(char ***)(this + 0x258))[i] + 0x50) = i;
            key += 10;
            i++;
        } while (key < 0x46);
    }
    P(0x84) = sub_00421680();
    P(0x88) = sub_004215D0();
    P(0x8c) = button_4C8B70(d_00608A6C);
    P(0x90) = button_4C8B70(d_00607C00);
    P(0x94) = button_4C8B70(d_0060A45C);
    P(0x98) = button_4C8B70(d_0060A448);
    P(0x9c) = button_4C8B70(d_0060A49C);
    {
        Str_4C8B70 names[5];
        char known[50];
        unsigned int file[0x40 / 4];
        unsigned int ss[0x100 / 4] __attribute__((aligned(8)));
        int g, k;
        char *kp = known, **slot = (char **)(this + 0xbc);
        imp_00607324(&names[0], d_00611BC4);
        imp_00607324(&names[1], d_00611BBC);
        imp_00607324(&names[2], d_00611BB8);
        imp_00607324(&names[3], d_00611BB0);
        imp_00607324(&names[4], d_00611BA8);
        __builtin_memset(known, 0, sizeof(known));
        sub_004C7A60(known);
        {
            Str_4C8B70 fn;
            imp_00607324(&fn, d_00611B34);
            sub_00459290(file, &fn, 0);
            imp_00607330(&fn);
        }
        if (!((char *)file)[0x2c]) {
            Str_4C8B70 msg;
            unsigned int exc[0x40 / 4];
            imp_00607324(&msg, d_00611B04);
            sub_00421220(exc, &msg, d_00611AEC, 0x155);
            sub_005E3EC0(exc, d_0069916C);
        }
        {
            Str_4C8B70 data;
            imp_00607324(&data, *(const char **)((char *)file + 0x28));
            imp_00607364(ss, &data, 3, 1);
            imp_00607330(&data);
        }
        for (g = 0; g < 4; g++) {
            float pts[6], *o;
            for (k = 0; k < 6; k++)
                imp_006072EC(ss, &pts[k]);
            o = ((vfpt_4C8B70)VF(C(0xb8), 0x88))(C(0xb8));
            pts[0] = o[0] + pts[0];
            pts[1] = o[1] + pts[1];
            o = ((vfpt_4C8B70)VF(C(0xb8), 0x88))(C(0xb8));
            pts[2] = o[0] + pts[2];
            pts[3] = o[1] + pts[3];
            o = ((vfpt_4C8B70)VF(C(0xb8), 0x88))(C(0xb8));
            pts[4] = o[0] + pts[4];
            pts[5] = o[1] + pts[5];
            for (k = 0; k < 10; k++, kp++, slot++) {
                float x, y;
                imp_006072EC(ss, &x);
                imp_006072EC(ss, &y);
                if (!*kp) {
                    slot[0] = 0;
                    slot[0x33] = 0;
                    continue;
                }
                spell_4C8B70(this, slot, &names[g], k, x, y, pts);
            }
        }
        ((vfp_4C8B70)VF(scene, 4))(scene, P(0xb8));
        ((vfp_4C8B70)VF(scene, 0xc))(scene, P(0x78));
        kp = known;
        slot = (char **)(this + 0x188);
        for (g = 0; g < 4; g++)
            for (k = 0; k < 10; k++, kp++, slot++)
                if (*kp) {
                    ((vfp_4C8B70)VF(scene, 4))(scene, slot[-0x33]);
                    ((vfp_4C8B70)VF(scene, 4))(scene, slot[0]);
                }
        imp_00607360(ss);
        sub_00459170(file);
        sub_005E4134(names, 0x1c, 5, (void *)imp_00607330);
    }
}
