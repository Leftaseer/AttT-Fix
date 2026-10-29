/* 0x004AFBF0: sets up a text element from its script table (arg): position 0,0 (vf68) and size 1,1 (vf94), scale 1
 * (+0x22C, changed +0x230), empty text (+0x210), shown (+0x49), +0x244 / +0x238 / +0x23C cleared, +0x248 = 2,
 * +0x251 = 60; the table's "Font" (0x00561830) gives the font by its name (entry 1, 0x0055F560; the old font +0x240
 * released by 0x004AE7C0, the new one from the font manager 0x006CA2D8, 0x004AF860), the entry at 0x00608A70
 * (0x004AD550) and the scale at 0x006097EC (0x0055F4A0); then the script's SpellUtil.PreProcessText (0x005608F0,
 * 0x005626D0) is called with the table (lua_rawgeti from the registry, lua_call) and the font re-lays the text
 * (0x004AE7C0, 0x004AEFE0). Script objects are held by reference; 0x0055F560 takes SpellUtil in EBX */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__cdecl sub_005608F0(void);
DECOMP_C int *__thiscall sub_00561830(void *self, void *name);
DECOMP_C void *__cdecl sub_0055F560(void *self, void *ebx, void *out, float i);
DECOMP_C void __thiscall sub_004AE7C0(void *self, void *el);
DECOMP_C void *__thiscall sub_004AF860(void *self, void *name);
DECOMP_C void __thiscall sub_004AD550(void *self, void *s);
DECOMP_C float __thiscall sub_0055F4A0(void *self, float i);
DECOMP_C int *__thiscall sub_005626D0(void *self, void *name);
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);        /* lua_rawgeti */
DECOMP_C void __cdecl sub_00403800(void *L, int nargs, int nres);   /* lua_call */
DECOMP_C void __thiscall sub_004AEFE0(void *self, void *el, void *util);
DECOMP_C char d_0068AE40[], d_0060FA8B[], d_00610684[], d_0061067C[], d_006CA2D8[], d_00608A70[], d_006097EC[],
    d_008D122C[], d_0061066C[], d_008CF080[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_006072F8)(void *, const char *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@PBD@Z");
typedef void (__thiscall *xy_4AFBF0)(void *self, float x, float y);
typedef void (__thiscall *del_4AFBF0)(void *self, int flags);

static int *get_4AFBF0(int *(__thiscall *f)(void *, void *), void *self, const char *n)
{
    unsigned int name[7];
    int *o;
    imp_00607324(name, n);
    o = f(self, name);
    if (o)
        o[1]++;
    imp_00607330(name);
    return o;
}

static void release_4AFBF0(int *o)
{
    if (o && !--o[1])
        ((del_4AFBF0)(*(void ***)o)[0])(o, 1);
}

DECOMP(004AFBF0)
void __thiscall f_004AFBF0(void *this, int *tbl)
{
    char *s = (char *)this;
    int *su, *font, *fn;
    unsigned int out[7];
    void *L;
    *(void **)(s + 0x240) = 0;
    ((xy_4AFBF0)(*(void ***)this)[0x68 / 4])(this, 0.0f, 0.0f);
    ((xy_4AFBF0)(*(void ***)this)[0x94 / 4])(this, 1.0f, 1.0f);
    *(unsigned int *)(s + 0x22c) = *(unsigned int *)d_0068AE40;
    s[0x230] = 1;
    imp_006072F8(s + 0x210, d_0060FA8B);
    s[0x49] = 1;
    *(int *)(s + 0x244) = 0;
    *(float *)(s + 0x238) = 0.0f;
    *(float *)(s + 0x23c) = 0.0f;
    *(int *)(s + 0x248) = 2;
    s[0x251] = 0x3c;
    su = get_4AFBF0(sub_00561830, sub_005608F0(), d_00610684);
    font = get_4AFBF0(sub_00561830, tbl, d_0061067C);
    {
        void *n = sub_0055F560(font, su, out, 1.0f);
        if (*(void **)(s + 0x240))
            sub_004AE7C0(*(void **)(s + 0x240), this);
        *(void **)(s + 0x240) = sub_004AF860(*(void **)d_006CA2D8, n);
        imp_00607330(out);
    }
    sub_004AD550(this, sub_0055F560(font, su, out, *(float *)d_00608A70));
    imp_00607330(out);
    *(float *)(s + 0x22c) = sub_0055F4A0(font, *(float *)d_006097EC);
    s[0x230] = 1;
    L = *(void **)d_008D122C;
    fn = get_4AFBF0(sub_005626D0, su, d_0061066C);
    sub_00403390(*(void **)d_008CF080, -10000, fn[3]);
    sub_00403390(*(void **)d_008CF080, -10000, tbl[3]);
    sub_00403800(L, 1, 0);
    if (*(void **)(s + 0x240))
        sub_004AE7C0(*(void **)(s + 0x240), this);
    sub_004AEFE0(*(void **)(s + 0x240), this, su);
    release_4AFBF0(fn);
    release_4AFBF0(font);
    release_4AFBF0(su);
}
