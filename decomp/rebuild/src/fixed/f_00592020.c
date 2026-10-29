/* 0x00592020: DrawableBBox constructor (base 0x004AD180 with an empty name; the owner a at +0x1BC, the 0x60-byte
 * box at +0x1E4, the kind at +0x354): 12 edge lines (+0x1C4) and 3 axis lines (+0x1D4: red x, blue y, green z of
 * length 0x00613C20; 0x00425B50); in the editor (0x006C88D8 +0x40) the lines take the kind's colour from
 * Editor.objectColor / houseColor / townColor / pspColor (+0x2E8, +0x2EC), the box is set (0x0058FF10), the box
 * registered (0x005B1B50) and the selection colours read (+0x2F0 objectSelectColor, +0x2F4 houseSelectColor,
 * +0x2F8 / +0x2FC townSelectColor). Returns this */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_592020;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_592020;                 /* nScript::Table */
DECOMP_C void __thiscall sub_004AD180(void *self, void *name, int a, int b);
DECOMP_C void __thiscall sub_00591D70(void *self, unsigned int n, void *v);
DECOMP_C void *__thiscall sub_004323E0(void *self, const char *name);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C float __thiscall sub_0057AC90(void *self, int i);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int n);                /* operator new */
DECOMP_C void *__thiscall sub_00425B50(void *self, float x0, float y0, float z0, float x1, float y1, float z1,
                                       unsigned int color);
DECOMP_C void __thiscall sub_004257E0(void *self, unsigned int color);
DECOMP_C void __thiscall sub_0058FF10(void *self, void *a, void *b);
DECOMP_C void __thiscall sub_005B1B50(void *self, void *box);
DECOMP_C char d_0060FA8B[], d_0061F6F4[], d_006C88D8[], d_00607CC4[], d_0060BB60[], d_0061F7F8[], d_0060BB54[],
    d_00615B10[], d_0061F7EC[], d_00613C20[], d_0061F7D8[], d_0061F7C4[], d_0061F7B4[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *vfd_592020)(void *self, int a);

/* c = Editor[key] */
static void color_592020(Tbl_592020 *c, const char *key)
{
    struct { void *t; const char *k; } ref;
    Tbl_592020 ed, t;
    ref.t = sub_004323E0(&ed, d_0060BB60);
    ref.k = key;
    sub_004369F0(&ref, &t);
    sub_0057A860(c, &t);
    sub_004220A0(&t);
    sub_004220A0(&ed);
}

/* the colour table's 1, 2, 3 as 0xRRGGBB */
static unsigned int rgb_592020(Tbl_592020 *c)
{
    int r = (int)(long long)sub_0057AC90(c, 1);
    int g = (int)(long long)sub_0057AC90(c, 2);
    int b = (int)(long long)sub_0057AC90(c, 3);
    return (unsigned int)(r & 0xff) << 16 | (unsigned int)(g & 0xff) << 8 | (unsigned int)(b & 0xff);
}

/* a refcounted slot takes o */
static void set_592020(void **slot, char *o)
{
    char *old;
    if (o)
        (*(int *)(o + 4))++;
    old = (char *)*slot;
    if (old && --*(int *)(old + 4) == 0)
        ((vfd_592020)(*(void ***)old)[0])(old, 1);
    *slot = o;
}

static void *line_592020(float x1, float y1, float z1, unsigned int color)
{
    void *mem = sub_005E3EAE(0x1d0);
    return mem ? sub_00425B50(mem, 0.0f, 0.0f, 0.0f, x1, y1, z1, color) : 0;
}

/* axis line k of the vector +0x1D4 */
static void axis_592020(char *this, int k, float x1, float y1, float z1, unsigned int color)
{
    char *o = (char *)line_592020(x1, y1, z1, color);
    set_592020(&(*(void ***)(this + 0x1d8))[k], o);
    (*(char **)(*(char **)(this + 0x1d8) + k * 4))[0x1cc] = 0;
    sub_004257E0((*(void ***)(this + 0x1d8))[k], color);
}

DECOMP(00592020)
void *__thiscall f_00592020(void *self, int owner, const void *box, int kind)
{
    char *this = (char *)self;
    Tbl_592020 c;
    unsigned int color;
    void **p;
    float len;

    {
        Str_592020 s;
        imp_00607324(&s, d_0060FA8B);
        sub_004AD180(this, &s, 0, 0);
        imp_00607330(&s);
    }
    *(void **)this = d_0061F6F4;
    {
        void *z = 0;
        sub_00591D70(this + 0x1c4, 0xc, &z);
        z = 0;
        sub_00591D70(this + 0x1d4, 3, &z);
    }
    *(int *)(this + 0x354) = kind;
    this[0x2e4] = 0;
    this[0x2e5] = 0;
    *(int *)(this + 0x358) = 0;
    *(int *)(this + 0x1bc) = owner;
    __builtin_memcpy(this + 0x1e4, box, 0x60);
    if (!(*(char **)d_006C88D8)[0x40])
        return this;
    c.w[1] = 0;
    c.w[0] = (unsigned int)(size_t)d_00607CC4;
    c.w[2] = 0xffffffffu;
    switch (*(unsigned int *)(this + 0x354)) {
    case 0: case 5: case 6:
        color_592020(&c, d_0061F7F8);
        break;
    case 1: case 3: case 4:
        color_592020(&c, d_0060BB54);
        break;
    case 2:
        color_592020(&c, d_00615B10);
        break;
    case 7: case 8:
        color_592020(&c, d_0061F7EC);
        break;
    }
    color = rgb_592020(&c);
    __builtin_memcpy(this + 0x300, this + 0x1e4, 12);
    __builtin_memcpy(this + 0x30c, this + 0x238, 12);
    for (p = *(void ***)(this + 0x1c8); p != *(void ***)(this + 0x1cc); p++)
        set_592020(p, (char *)line_592020(0.0f, 0.0f, 0.0f, color));
    len = *(float *)d_00613C20;
    axis_592020(this, 0, len, 0.0f, 0.0f, 0xff0000);
    axis_592020(this, 1, 0.0f, len, 0.0f, 0xff);
    axis_592020(this, 2, 0.0f, 0.0f, len, 0xff00);
    sub_0058FF10(this, this + 0x1e4, this + 0x238);
    *(unsigned int *)(this + 0x2ec) = color;
    *(unsigned int *)(this + 0x2e8) = color;
    for (p = *(void ***)(this + 0x1c8); p != *(void ***)(this + 0x1cc); p++)
        sub_004257E0(*p, color);
    sub_005B1B50(*(void **)d_006C88D8, this);
    color_592020(&c, d_0061F7D8);
    *(unsigned int *)(this + 0x2f0) = rgb_592020(&c);
    color_592020(&c, d_0061F7C4);
    *(unsigned int *)(this + 0x2f4) = rgb_592020(&c);
    color_592020(&c, d_0061F7B4);
    *(unsigned int *)(this + 0x2f8) = rgb_592020(&c);
    color_592020(&c, d_0061F7B4);
    *(unsigned int *)(this + 0x2fc) = rgb_592020(&c);
    sub_004220A0(&c);
    return this;
}
