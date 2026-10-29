/* 0x004C6F60: shows the selected spell's description: from the GUI root (0x005608F0) the "Spell" element's child
 * for the level (+0x26C plus 1), then for the school group of the spell type (+0x278[level]: 0..3 -> 1, 4..6 -> 2,
 * 7..8 -> 3, else 4) and the rank (0x004C6A90) (0x00561830 by name, 0x005619C0 by number; all refcounted); its
 * "Caption" and "Text" go to the two text boxes (+0x28C / +0x290, 0x004AFBF0), each centred on the screen
 * (0x006C8958 x 0x006C895C) by the current font's (+0xB8's +0x224) size (vf14 / vf10) through vf68, and its
 * "NameFile" (0x00561520) is kept (+0x2E8) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C unsigned char __thiscall sub_004C6A90(void *self);
DECOMP_C void *__cdecl sub_005608F0(void);
DECOMP_C char *__thiscall sub_00561830(void *self, void *name);
DECOMP_C char *__thiscall sub_005619C0(void *self, float i);
DECOMP_C void *__thiscall sub_00561520(void *self, void *out, void *name);
DECOMP_C void __thiscall sub_004AFBF0(void *self, void *el);
DECOMP_C char d_00611738[], d_00611AE4[], d_00611ADC[], d_00611740[], d_006C8958[], d_006C895C[], d_0068AE08[],
    d_00607CE0[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void *(__thiscall *imp_0060731C)(void *, const void *) __asm__("__imp_??4?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAEAAV01@ABV01@@Z");
typedef unsigned int (__thiscall *size_4C6F60)(void *self);
typedef void (__thiscall *pos_4C6F60)(void *self, float a, float b);
typedef void (__thiscall *del_4C6F60)(void *self, int del);

static char *ref_4C6F60(char *p)
{
    if (p)
        *(int *)(p + 4) += 1;
    return p;
}

static void unref_4C6F60(char *p)
{
    if (p && !(*(int *)(p + 4) -= 1))
        ((del_4C6F60)**(void ***)p)(p, 1);
}

static char *named_4C6F60(char *el, const char *name)
{
    unsigned int str[7];
    char *r;
    imp_00607324(str, name);
    r = ref_4C6F60(sub_00561830(el, str));
    imp_00607330(str);
    return r;
}

static float u2f_4C6F60(unsigned int v)
{
    float f = (float)(int)v;
    if ((int)v < 0)
        f += *(float *)d_0068AE08;
    return f;
}

static void centre_4C6F60(char *s, char *box, char *el)
{
    char *f;
    unsigned int w, h;
    float x;
    sub_004AFBF0(box, el);
    f = *(char **)(s + 0xb8) + 0x224;
    f = (*(char ***)(*(char **)f + 0x38))[*(int *)(*(char **)f + 0x40)];
    w = ((size_4C6F60)(*(void ***)f)[0x14 / 4])(f);
    f = *(char **)(s + 0xb8) + 0x224;
    f = (*(char ***)(*(char **)f + 0x38))[*(int *)(*(char **)f + 0x40)];
    h = ((size_4C6F60)(*(void ***)f)[0x10 / 4])(f);
    x = (float)((*(float *)d_006C8958 - u2f_4C6F60(w)) * *(double *)d_00607CE0);
    ((pos_4C6F60)(*(void ***)box)[0x68 / 4])(box, (float)((*(float *)d_006C895C - u2f_4C6F60(h)) *
                                                            *(double *)d_00607CE0), x);
}

DECOMP(004C6F60)
void __thiscall f_004C6F60(void *this)
{
    char *s = (char *)this, *spell, *e1, *e2, *e3, *cap, *text;
    unsigned int lvl = *(unsigned int *)(s + 0x26c), str[7], name[7];
    int v = *(int *)(s + 0x278 + lvl * 4);
    float f1 = (float)(unsigned char)((unsigned char)lvl + 1), f2, f3;
    unsigned char cat;
    if (v >= 0 && v <= 3)
        cat = 1;
    else if (v >= 4 && v <= 6)
        cat = 2;
    else if (v >= 7 && v <= 8)
        cat = 3;
    else
        cat = 4;
    f2 = (float)cat;
    f3 = (float)sub_004C6A90(this);
    spell = named_4C6F60((char *)sub_005608F0(), d_00611738);
    e1 = ref_4C6F60(sub_005619C0(spell, f1));
    e2 = ref_4C6F60(sub_005619C0(e1, f2));
    e3 = ref_4C6F60(sub_005619C0(e2, f3));
    cap = named_4C6F60(e3, d_00611AE4);
    text = named_4C6F60(e3, d_00611ADC);
    centre_4C6F60(s, *(char **)(s + 0x28c), cap);
    centre_4C6F60(s, *(char **)(s + 0x290), text);
    imp_00607324(str, d_00611740);
    imp_0060731C(s + 0x2e8, sub_00561520(e3, name, str));
    imp_00607330(name);
    imp_00607330(str);
    unref_4C6F60(text);
    unref_4C6F60(cap);
    unref_4C6F60(e3);
    unref_4C6F60(e2);
    unref_4C6F60(e1);
    unref_4C6F60(spell);
}
