/* 0x004C6640: CSpellIcon::CSpellIcon(owner, icon file, glow file): the 2D mesh base "SpellIcon" (0x0047A120) and its
 * interface part (+0x224, 0x00473FD0 with the owner), their vtables, the render name "SpellIcon" (0x004AB810); the
 * icon and glow videos (new 0x54-byte textures, 0x004DF920, at +0x278 / +0x27C) set as "tIcon" / "tGlow" on the
 * effect (+0x3C vf0C), the mesh sized to the icon's frame (vf10 / vf14 unsigned, 0x00479D80 taking the height in EAX
 * too), vfD4; both videos are set to their last frame (vf34 - 1, kept in +0x284; 0x004DEDC0, +0x53, +0x40) and
 * updated (vf30); +0x280 cleared. The original tests the icon's frame against +0x284 with the same code on both sides
 * (the original destroys the parts built if one throws; this C does not) */
/* @conv ECX 12 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0047A120(void *self, void *name);
DECOMP_C void __thiscall sub_00473FD0(void *self, void *owner);
DECOMP_C void __thiscall sub_004AB810(void *self, void *name, int a);
DECOMP_C void *__thiscall sub_004DF920(void *self, void *file, int a);
DECOMP_C void __cdecl sub_00479D80(void *self, unsigned int eax, float h, float w);
DECOMP_C void __thiscall sub_004DEDC0(void *self, int a, int b);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_00611AC8[], d_0061189C[], d_00611888[], d_00611AC0[], d_00611AB8[];
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
typedef void (__thiscall *vf0C_4C6640)(void *self, void *name, void *tex);
typedef unsigned int (__thiscall *vf_4C6640)(void *self);

#define FRAME(v) (*(void ***)(*(char **)((v) + 0x38) + *(int *)((v) + 0x40) * 4))

static void *tex_4C6640(void *file)
{
    void *m = sub_005E3EAE(0x54);
    return m ? sub_004DF920(m, file, 0) : 0;
}

static void set_4C6640(char *s, const char *name, void *tex)
{
    unsigned int str[7];
    void **fx;
    imp_00607324(str, name);
    fx = *(void ***)(s + 0x3c);
    ((vf0C_4C6640)(*(void ***)fx)[0xc / 4])(fx, str, tex);
    imp_00607330(str);
}

DECOMP(004C6640)
void *__thiscall f_004C6640(void *this, void *owner, void *icon, void *glow)
{
    char *s = (char *)this, *v;
    unsigned int str[7], w, h;
    void **f;
    float fw;
    imp_00607324(str, d_00611AC8);
    sub_0047A120(this, str);
    imp_00607330(str);
    sub_00473FD0(s + 0x224, owner);
    *(void **)s = d_0061189C;
    *(void **)(s + 0x224) = d_00611888;
    imp_00607324(str, d_00611AC8);
    sub_004AB810(this, str, 1);
    imp_00607330(str);
    *(void **)(s + 0x278) = tex_4C6640(icon);
    *(void **)(s + 0x27c) = tex_4C6640(glow);
    set_4C6640(s, d_00611AC0, *(void **)(s + 0x278));
    set_4C6640(s, d_00611AB8, *(void **)(s + 0x27c));
    v = *(char **)(s + 0x278);
    f = FRAME(v);
    w = ((vf_4C6640)(*(void ***)f)[0x14 / 4])(f);
    fw = (float)(double)w;
    v = *(char **)(s + 0x278);
    f = FRAME(v);
    h = ((vf_4C6640)(*(void ***)f)[0x10 / 4])(f);
    sub_00479D80(this, h, (float)(double)h, fw);
    ((vf_4C6640)(*(void ***)this)[0xd4 / 4])(this);
    s[0x280] = 0;
    v = *(char **)(s + 0x278);
    *(int *)(s + 0x284) = ((vf_4C6640)(*(void ***)v)[0x34 / 4])(v) - 1;
    sub_004DEDC0(*(void **)(s + 0x278), *(int *)(s + 0x284), *(int *)(s + 0x284));
    sub_004DEDC0(*(void **)(s + 0x27c), *(int *)(s + 0x284), *(int *)(s + 0x284));
    (*(char **)(s + 0x278))[0x53] = 1;
    (*(char **)(s + 0x27c))[0x53] = 1;
    *(int *)(*(char **)(s + 0x278) + 0x40) = *(int *)(s + 0x284);
    *(int *)(*(char **)(s + 0x27c) + 0x40) = *(int *)(s + 0x284);
    v = *(char **)(s + 0x278);
    ((vf_4C6640)(*(void ***)v)[0x30 / 4])(v);
    v = *(char **)(s + 0x27c);
    ((vf_4C6640)(*(void ***)v)[0x30 / 4])(v);
    return this;
}
