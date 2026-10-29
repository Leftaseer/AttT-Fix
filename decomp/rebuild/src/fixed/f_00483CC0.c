/* 0x00483CC0: notes book scene init: the back buffer (0x00421730 +0x7C, picture 0x0047A120 +0xAC over the screen),
 * a choice group (0x00473F10, +0x80) as the controls, the notes book (0x00482B40, +0x78) centred by its page size,
 * the cursor and input (+0x98 / +0x9C), the "Use", "Default" and "ExitRed" cursors (0x004207C0, +0xA0..+0xA8), the
 * group placed at the page corner (0x00473AD0); five mask regions (0x00473FD0, +0x84..+0x94, keys 0 / 100 / 200 /
 * 150 / 255) get their handlers by the registered member addresses (0x004838F0); the default cursor is shown, the
 * pages "1111", "2222", "3333" added (0x00483770) and the first one opened (0x004827B0) */
/* @conv ECX 0 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_483CC0;                 /* std::string */
DECOMP_C char *__cdecl sub_00421730(void);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);             /* operator new */
DECOMP_C void *__thiscall sub_0047A120(void *self, void *name);
DECOMP_C void *__thiscall sub_00473F10(void *self);
DECOMP_C int __thiscall sub_004205C0(void *self, void *child);
DECOMP_C char *__thiscall sub_00482B40(void *self, void *scene, void *group);
DECOMP_C void *__cdecl sub_00421680(void);
DECOMP_C void *__cdecl sub_004215D0(void);
DECOMP_C void *__thiscall sub_004207C0(void *self, void *name);
DECOMP_C void __thiscall sub_00473AD0(void *self, unsigned int x, unsigned int y);
DECOMP_C char *__thiscall sub_00473FD0(void *self, void *scene);
DECOMP_C void __thiscall sub_00473AC0(void *self, void *choice, int key);
DECOMP_C int __cdecl sub_004838F0(void *fn, int adj);
DECOMP_C void __thiscall sub_00483770(void *self, void *name);
DECOMP_C void __thiscall sub_004827B0(void *self, int page);
DECOMP_C char d_00607C14[], d_00607C08[], d_006C8958[], d_006C895C[], d_00608A6C[], d_00607C00[], d_0060A49C[],
    d_00483940[], d_00483960[], d_00483980[], d_004839A0[], d_004839C0[], d_00483A00[], d_0060F60C[], d_0060F604[],
    d_0060F5FC[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *vf1_483CC0)(void *self, void *a);
typedef void (__thiscall *vf2_483CC0)(void *self, void *a, int b);
typedef void *(__thiscall *vfp_483CC0)(void *self);
typedef void (__thiscall *vff_483CC0)(void *self, float a, float b);
typedef unsigned int (__thiscall *vfi_483CC0)(void *self);

#define VT(o) (*(void ***)(o))
#define F(a) (*(float *)(a))

/* the current page of the notes book */
static void *page_483CC0(char *this)
{
    char *p = *(char **)(*(char **)(this + 0x78) + 0x23c);
    return (*(void ***)(p + 0x38))[*(int *)(p + 0x40)];
}

static void *cursor_483CC0(const char *name)
{
    void *mem = sub_005E3EAE(0x5c), *c = 0;
    if (mem) {
        Str_483CC0 s;
        imp_00607324(&s, name);
        c = sub_004207C0(mem, &s);
        imp_00607330(&s);
    }
    return c;
}

static void region_483CC0(char *this, int slot, int key, void *f10, void *f14, void *fc)
{
    void *mem = sub_005E3EAE(0x54);
    char *r = mem ? sub_00473FD0(mem, this) : 0;
    *(char **)(this + slot) = r;
    sub_00473AC0(*(void **)(this + 0x80), r, key);
    *(int *)(*(char **)(this + slot) + 0x10) = sub_004838F0(f10, 0);
    *(int *)(*(char **)(this + slot) + 0x14) = sub_004838F0(f14, 0);
    if (fc)
        *(int *)(*(char **)(this + slot) + 0xc) = sub_004838F0(fc, 0);
}

static void addpage_483CC0(char *this, const char *name)
{
    Str_483CC0 s;
    imp_00607324(&s, name);
    sub_00483770(*(void **)(this + 0x78), &s);
    imp_00607330(&s);
}

DECOMP(00483CC0)
void __thiscall f_00483CC0(char *this)
{
    void *layer = this + 4, *mem, *o, *m;
    Str_483CC0 s;
    unsigned int h, w;

    *(char **)(this + 0x7c) = sub_00421730();
    mem = sub_005E3EAE(0x224);
    o = 0;
    if (mem) {
        imp_00607324(&s, d_00607C14);
        o = sub_0047A120(mem, &s);
        *(void **)(this + 0xac) = o;
        imp_00607330(&s);
    } else
        *(void **)(this + 0xac) = 0;
    imp_00607324(&s, d_00607C14);
    o = *(void **)(this + 0xac);
    ((vf2_483CC0)VT(o)[0x2c / 4])(o, &s, 1);
    imp_00607330(&s);
    imp_00607324(&s, d_00607C08);
    o = *(void **)(this + 0xac);
    m = ((vfp_483CC0)VT(o)[0x30 / 4])(o);
    ((vf2_483CC0)VT(m)[0xc / 4])(m, &s, *(int *)(*(char **)(this + 0x7c) + 4));
    imp_00607330(&s);
    o = *(void **)(this + 0xac);
    ((vff_483CC0)VT(o)[0x94 / 4])(o, F(d_006C895C), F(d_006C8958));
    ((vf1_483CC0)VT(layer)[4 / 4])(layer, *(void **)(this + 0xac));

    mem = sub_005E3EAE(0x458);
    o = mem ? sub_00473F10(mem) : 0;
    *(void **)(this + 0x80) = o;
    sub_004205C0(this, o);
    *(void **)(this + 0x78) = 0;
    mem = sub_005E3EAE(0x2a4);
    *(char **)(this + 0x78) = mem ? sub_00482B40(mem, this, *(void **)(this + 0x80)) : 0;
    o = page_483CC0(this);
    h = ((vfi_483CC0)VT(o)[0x14 / 4])(o);
    o = page_483CC0(this);
    w = ((vfi_483CC0)VT(o)[0x10 / 4])(o);
    {
        float y = (float)(((long double)F(d_006C8958) - h) * 0.5);
        float x = (float)(((long double)F(d_006C895C) - w) * 0.5);
        o = *(void **)(this + 0x78);
        ((vff_483CC0)VT(o)[0x68 / 4])(o, x, y);
    }
    ((vf1_483CC0)VT(layer)[4 / 4])(layer, *(void **)(this + 0x78));
    *(void **)(this + 0x98) = sub_00421680();
    *(void **)(this + 0x9c) = sub_004215D0();
    *(void **)(this + 0xa0) = cursor_483CC0(d_00608A6C);
    *(void **)(this + 0xa4) = cursor_483CC0(d_00607C00);
    *(void **)(this + 0xa8) = cursor_483CC0(d_0060A49C);

    o = page_483CC0(this);
    h = ((vfi_483CC0)VT(o)[0x14 / 4])(o);
    o = page_483CC0(this);
    w = ((vfi_483CC0)VT(o)[0x10 / 4])(o);
    {
        unsigned int y = (unsigned int)(long long)((long double)F(d_006C8958) - h) >> 1;
        unsigned int x = (unsigned int)(long long)((long double)F(d_006C895C) - w) >> 1;
        sub_00473AD0(*(void **)(this + 0x80), x, y);
    }
    region_483CC0(this, 0x84, 0, d_00483940, d_00483960, d_00483980);
    region_483CC0(this, 0x88, 100, d_004839A0, d_00483960, d_004839C0);
    region_483CC0(this, 0x8c, 200, d_004839A0, d_00483960, d_00483A00);
    region_483CC0(this, 0x90, 150, d_00483960, d_00483960, 0);
    region_483CC0(this, 0x94, 255, d_00483960, d_00483960, 0);
    o = *(void **)(this + 0x98);
    ((vf1_483CC0)VT(o)[0xe8 / 4])(o, *(void **)(this + 0xa4));
    addpage_483CC0(this, d_0060F60C);
    addpage_483CC0(this, d_0060F604);
    addpage_483CC0(this, d_0060F5FC);
    sub_004827B0(*(void **)(this + 0x78), 1);
}
