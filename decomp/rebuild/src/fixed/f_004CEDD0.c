/* 0x004CEDD0: the statistics screen's set-up: its 3D view (+0x78, 0x004AF7A0, made current), the yellow Century
 * Gothic font (+0x7C, 0x00457510 / 0x00457600), the back buffer filled white, the Bubbles.bmp background (+0x80 on
 * the BackGround sprite +0x98), the text panel (+0x84, 0x00473F10, at the screen origin +0xC4 / +0xC8), the input
 * (+0x8C, +0x90) with the ExitRed button (+0x94), and five icons (battle, gold, parameters, quests, warrior rank;
 * picture and Default2DAlpha sprite pairs at +0x9C..+0xC0) placed from the origin; finally the view joins the list */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_4CEDD0;                 /* std::string */
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_004AF7A0(void *self);
DECOMP_C int __cdecl sub_004AD530(void *self, unsigned int eax);
DECOMP_C void *__thiscall sub_00457510(void *self);
DECOMP_C void __thiscall sub_00457600(void *self, float a, float b, float size, float d, void *font, void *tex);
DECOMP_C int __thiscall sub_004205C0(void *self, void *child);
DECOMP_C char *__cdecl sub_00425F60(void);
DECOMP_C void *__cdecl sub_005E40BE(void *p, int c, unsigned int n);
DECOMP_C void *__thiscall sub_004DF920(void *self, void *name, int a);
DECOMP_C void *__thiscall sub_0047A120(void *self, void *name);
DECOMP_C void *__thiscall sub_00473F10(void *self);
DECOMP_C void __thiscall sub_00473AD0(void *self, unsigned int x, unsigned int y);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C char *__cdecl sub_004215D0(void);
DECOMP_C void *__thiscall sub_004207C0(void *self, void *name);
DECOMP_C char d_00608A88[], d_00608A78[], d_00608A74[], d_00608A70[], d_006C8C10[], d_00611FE0[], d_00611FD4[],
    d_0060A49C[], d_00611FC0[], d_0060891C[], d_00609308[], d_00611FB8[], d_00611FA4[], d_0060A208[], d_00611F90[],
    d_00611F88[], d_0068AE18[], d_00611F70[], d_00611F68[], d_00611F48[], d_006088E8[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef long (__stdcall *backbuf_4CEDD0)(void *dev, unsigned int chain, unsigned int i, int type, void **out);
typedef long (__stdcall *desc_4CEDD0)(void *surf, void *desc);
typedef long (__stdcall *lock_4CEDD0)(void *surf, void *lr, void *rect, unsigned int flags);
typedef long (__stdcall *com_4CEDD0)(void *o);
typedef void (__thiscall *vfp_4CEDD0)(void *self, void *p);
typedef void (__thiscall *pos_4CEDD0)(void *self, float x, float y);

#define VF(o, off) ((*(void ***)(o))[(off) / 4])
#define D(a) (*(double *)(a))

static void *named_4CEDD0(int size, void *(__thiscall *ctor)(void *, void *), const char *name)
{
    void *mem = sub_005E3EAE(size), *o = 0;
    if (mem) {
        Str_4CEDD0 s;
        imp_00607324(&s, name);
        o = ctor(mem, &s);
        imp_00607330(&s);
    }
    return o;
}

static void *picture_4CEDD0(const char *name)
{
    void *mem = sub_005E3EAE(0x54), *o = 0;
    if (mem) {
        Str_4CEDD0 s;
        imp_00607324(&s, name);
        o = sub_004DF920(mem, &s, 0);
        imp_00607330(&s);
    }
    return o;
}

/* a sprite showing picture p (stored at +pic / +spr) at the origin plus (dx, dy), added to the scene's list */
static void icon_4CEDD0(char *this, int pic, int spr, const char *name, double dx, double dy)
{
    void *s, *list = this + 4;
    float pos[2];
    *(void **)(this + pic) = picture_4CEDD0(name);
    *(void **)(this + spr) = named_4CEDD0(0x224, sub_0047A120, d_0060891C);
    s = *(void **)(this + spr);
    ((vfp_4CEDD0)VF(s, 0x34))(s, *(void **)(this + pic));
    pos[0] = (float)(*(float *)(this + 0xc4) + dx);
    pos[1] = (float)(*(float *)(this + 0xc8) + dy);
    s = *(void **)(this + spr);
    ((vfp_4CEDD0)VF(s, 0x6c))(s, pos);
    s = *(void **)(this + spr);
    ((pos_4CEDD0)VF(s, 0x94))(s, 0.0f, 0.0f);
    ((vfp_4CEDD0)VF(list, 4))(list, *(void **)(this + spr));
}

DECOMP(004CEDD0)
void __thiscall f_004CEDD0(void *self)
{
    char *this = (char *)self;
    void *mem, *list = this + 4;

    mem = sub_005E3EAE(0x84);
    *(void **)(this + 0x78) = mem ? sub_004AF7A0(mem) : 0;
    sub_004AD530(*(void **)(this + 0x78), 0);
    mem = sub_005E3EAE(0x2bc);
    *(void **)(this + 0x7c) = mem ? sub_00457510(mem) : 0;
    {
        Str_4CEDD0 tex, font;
        imp_00607324(&tex, d_00608A88);
        imp_00607324(&font, d_00608A78);
        sub_00457600(*(void **)(this + 0x7c), *(float *)d_00608A70, *(float *)d_00608A70, *(float *)d_00608A74, 1.0f,
                     &font, &tex);
        imp_00607330(&font);
        imp_00607330(&tex);
    }
    sub_004205C0(this, *(void **)(this + 0x7c));
    (*(int *)(sub_00425F60() + 0x1d8))++;
    {
        void *dev = *(void **)d_006C8C10, *surf;
        unsigned int desc[8], lr[2];
        ((backbuf_4CEDD0)VF(dev, 0x48))(dev, 0, 0, 0, &surf);
        ((desc_4CEDD0)VF(surf, 0x30))(surf, desc);
        ((lock_4CEDD0)VF(surf, 0x34))(surf, lr, 0, 0);
        sub_005E40BE((void *)(size_t)lr[1], 0xff, desc[7] * lr[0]);
        ((com_4CEDD0)VF(surf, 0x38))(surf);
        *(void **)(this + 0x80) = picture_4CEDD0(d_00611FE0);
        ((com_4CEDD0)VF(surf, 8))(surf);
    }
    *(void **)(this + 0x98) = named_4CEDD0(0x224, sub_0047A120, d_00611FD4);
    {
        void *s = *(void **)(this + 0x98);
        ((vfp_4CEDD0)VF(s, 0x34))(s, *(void **)(this + 0x80));
        s = *(void **)(this + 0x98);
        ((pos_4CEDD0)VF(s, 0x94))(s, 0.0f, 0.0f);
        ((vfp_4CEDD0)VF(list, 4))(list, *(void **)(this + 0x98));
    }
    mem = sub_005E3EAE(0x458);
    {
        void *t = mem ? sub_00473F10(mem) : 0;
        unsigned int y, x;
        *(void **)(this + 0x84) = t;
        y = (unsigned int)(long long)*(float *)(this + 0xc8);
        x = (unsigned int)(long long)*(float *)(this + 0xc4);
        sub_00473AD0(t, x, y);
    }
    sub_004205C0(this, *(void **)(this + 0x84));
    *(void **)(this + 0x8c) = sub_00421680();
    *(char **)(this + 0x90) = sub_004215D0();
    *(void **)(this + 0x94) = named_4CEDD0(0x5c, sub_004207C0, d_0060A49C);
    {
        void *in = *(void **)(this + 0x8c);
        ((vfp_4CEDD0)VF(in, 0xe8))(in, *(void **)(this + 0x94));
    }
    icon_4CEDD0(this, 0x9c, 0xa0, d_00611FC0, D(d_00609308), D(d_00611FB8));
    icon_4CEDD0(this, 0xa4, 0xa8, d_00611FA4, D(d_00609308), D(d_0060A208));
    icon_4CEDD0(this, 0xac, 0xb0, d_00611F90, D(d_00611F88), D(d_0068AE18));
    icon_4CEDD0(this, 0xb4, 0xb8, d_00611F70, D(d_00609308), D(d_00611F68));
    icon_4CEDD0(this, 0xbc, 0xc0, d_00611F48, D(d_006088E8), D(d_0068AE18));
    ((vfp_4CEDD0)VF(list, 4))(list, *(void **)(this + 0x78));
}
