/* 0x004C6450: CSpellBook::CSpellBook: the 2D mesh base "Spellbook" (0x0047A120), its vtable, the render name
 * "SpellBook" (0x004AB810), the book's Bink video "Spellbook.bik" (a new 0x54-byte texture, 0x004DF920) at +0x224
 * set as "tSpellbook" on its effect (+0x3C vf0C), sized to the video's frame (vf10 / vf14, unsigned) by 0x00479D80
 * (which takes the height in EAX too), rewound (0x004DEDC0(0, 0)) and the effect's vf08 (the original destroys the
 * parts built if one throws; this C does not) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0047A120(void *self, void *name);
DECOMP_C void __thiscall sub_004AB810(void *self, void *name, int a);
DECOMP_C void *__thiscall sub_004DF920(void *self, void *file, int a);
DECOMP_C void __cdecl sub_00479D80(void *self, unsigned int eax, float h, float w);
DECOMP_C void __thiscall sub_004DEDC0(void *self, int a, int b);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_00611AAC[], d_0061179C[], d_00611AA0[], d_00611A90[], d_00611A84[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *vf0C_4C6450)(void *self, void *name, void *tex);
typedef unsigned int (__thiscall *vf_4C6450)(void *self);

#define FRAME(v) (*(void ***)(*(char **)((v) + 0x38) + *(int *)((v) + 0x40) * 4))

DECOMP(004C6450)
void *__thiscall f_004C6450(void *this)
{
    char *s = (char *)this;
    unsigned int str[7], w, h;
    void *tex, **fx, **f;
    char *v;
    float fw;
    imp_00607324(str, d_00611AAC);
    sub_0047A120(this, str);
    imp_00607330(str);
    *(void **)s = d_0061179C;
    imp_00607324(str, d_00611AA0);
    sub_004AB810(this, str, 1);
    imp_00607330(str);
    tex = sub_005E3EAE(0x54);
    if (tex) {
        imp_00607324(str, d_00611A90);
        *(void **)(s + 0x224) = sub_004DF920(tex, str, 0);
        imp_00607330(str);
    } else
        *(void **)(s + 0x224) = 0;
    imp_00607324(str, d_00611A84);
    fx = *(void ***)(s + 0x3c);
    ((vf0C_4C6450)(*(void ***)fx)[0xc / 4])(fx, str, *(void **)(s + 0x224));
    imp_00607330(str);
    v = *(char **)(s + 0x224);
    f = FRAME(v);
    w = ((vf_4C6450)(*(void ***)f)[0x14 / 4])(f);
    fw = (float)(double)w;
    v = *(char **)(s + 0x224);
    f = FRAME(v);
    h = ((vf_4C6450)(*(void ***)f)[0x10 / 4])(f);
    sub_00479D80(this, h, (float)(double)h, fw);
    *(unsigned int *)(s + 0x228) = 0;
    sub_004DEDC0(*(void **)(s + 0x224), 0, 0);
    fx = *(void ***)(s + 0x3c);
    ((vf_4C6450)(*(void ***)fx)[2])(fx);
    s[0x22c] = 0;
    return this;
}
