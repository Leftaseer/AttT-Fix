/* 0x0058B970: a conversation's speaker (script table, camera entry name, animation name): without a table the speaker
 * model (+0x290), its shadow (+0x34C) and +0x294 / +0x298 are dropped. Otherwise the table's Animation.WaitWorld (or,
 * missing, its Animation entry of the animation name; 0x0057B5A0, 0x00437870) gives the animation description
 * (0x0057B320 [1] -> 0x004A01A0: name, ..., frame count +0x24); a model of a different name is replaced by a new
 * 0x21C-byte one (0x0042AF50 with 0x0042A0D0 of "standart3d") starting on a random frame (+0x1CC and its
 * +0x1C4's +0x1D8); the camera is the table's ConversationCamera or its entry by the camera name (0x0045C740 /
 * 0x00464600), applied by 0x0058B090; +0x294 follows the model, a new 0x324-byte shadow (0x004EC6F0) replaces +0x34C
 * and +0x298 is cleared */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[7]; } Str_58B970;                 /* std::string */
typedef struct { unsigned int w[3]; } Tbl_58B970;                 /* nScript::Table */
typedef struct { void *tbl; Str_58B970 key; } Ref_58B970;
DECOMP_C void *__thiscall sub_0057B4E0(void *self, Tbl_58B970 *out, const char *key);
DECOMP_C void *__thiscall sub_0057B5A0(void *self, Tbl_58B970 *out, const char *key, Tbl_58B970 *def);
DECOMP_C void *__thiscall sub_00437870(void *self, Tbl_58B970 *out, void *name);
DECOMP_C void __thiscall sub_0057A860(void *self, void *src);
DECOMP_C int __thiscall sub_004220A0(void *self);
DECOMP_C void *__thiscall sub_0057B320(void *self, Tbl_58B970 *out, int i);
DECOMP_C void __cdecl sub_004A01A0(void *self, unsigned int ebx, void *tbl);
DECOMP_C void *__cdecl sub_0042A0D0(void *desc, void *textures, int a);
DECOMP_C char *__thiscall sub_0042AF50(void *self, void *desc, void *tmpl, int a);
DECOMP_C void __thiscall sub_004369F0(void *self, void *out);
DECOMP_C Ref_58B970 *__thiscall sub_0045C740(void *self, Ref_58B970 *out, Str_58B970 key);
DECOMP_C void *__thiscall sub_00464600(void *self, Tbl_58B970 *out);
DECOMP_C void __thiscall sub_0058B090(void *self, void *cam);
DECOMP_C void *__thiscall sub_004EC6F0(void *self, void *a, void *owner, unsigned int b, Str_58B970 s1,
                                       Str_58B970 s2);
DECOMP_C void *__cdecl sub_005E3EAE(unsigned int size);
DECOMP_C char d_00607CC4[], d_0060C138[], d_0060C124[], d_0060B8CC[], d_006120A0[], d_0060C2E8[], d_0060C2D8[];
DECOMP_C void (__thiscall *imp_006071E0)(void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607324)(void *, const char *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@PBD@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C int (__cdecl *imp_00607368)(const void *, const void *) __asm__("__imp_??$?9DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@0@Z");
DECOMP_C int (__cdecl *imp_00607400)(void) __asm__("__imp__rand");
typedef void (__thiscall *rel_58B970)(void *self, int del);

static void put_58B970(void **slot, void *o)
{
    void *old;
    if (o)
        *(int *)((char *)o + 4) += 1;
    old = *slot;
    if (old && !(*(int *)((char *)old + 4) -= 1))
        ((rel_58B970)**(void ***)old)(old, 1);
    *slot = o;
}

static void nil_58B970(Tbl_58B970 *t)
{
    t->w[1] = 0;
    t->w[0] = (unsigned int)d_00607CC4;
    t->w[2] = 0xffffffff;
}

DECOMP(0058B970)
void __thiscall f_0058B970(void *this, char *tbl, void *cam, void *anim)
{
    char *s = (char *)this, *m;
    Tbl_58B970 t, a, w, c, tmp;
    unsigned int desc[0x2c / 4];
    void *o;
    if (*(int *)(tbl + 8) <= 0) {
        put_58B970((void **)(s + 0x290), 0);
        put_58B970((void **)(s + 0x34c), 0);
        *(void **)(s + 0x294) = 0;
        *(void **)(s + 0x298) = 0;
        return;
    }
    nil_58B970(&t);
    sub_0057B5A0(sub_0057B4E0(tbl, &a, d_0060C138), &w, d_0060C124, &t);
    sub_004220A0(&a);
    sub_004220A0(&t);
    if ((int)w.w[2] <= 0) {
        sub_0057A860(&w, sub_00437870(sub_0057B4E0(tbl, &a, d_0060C138), &tmp, anim));
        sub_004220A0(&tmp);
        sub_004220A0(&a);
    }
    imp_006071E0(desc);
    sub_004A01A0(desc, 1, sub_0057B320(&w, &tmp, 1));
    sub_004220A0(&tmp);
    if (!*(char **)(s + 0x290) || (char)imp_00607368(desc, *(char **)(*(char **)(s + 0x290) + 0x1c4) + 8)) {
        o = sub_005E3EAE(0x21c);
        if (o) {
            unsigned int str[7];
            imp_00607324(str, d_0060B8CC);
            o = sub_0042AF50(o, desc, sub_0042A0D0(desc, str, 9), 1);
            put_58B970((void **)(s + 0x290), o);
            imp_00607330(str);
        } else
            put_58B970((void **)(s + 0x290), 0);
        m = *(char **)(s + 0x290);
        *(unsigned int *)(m + 0x1cc) = (unsigned int)imp_00607400() % desc[0x24 / 4];
        *(unsigned int *)(*(char **)(m + 0x1c4) + 0x1d8) = *(unsigned int *)(m + 0x1cc);
    }
    nil_58B970(&c);
    if (!*(unsigned int *)((char *)cam + 0x14)) {
        struct { void *t; const char *k; } key;
        key.t = tbl;
        key.k = d_006120A0;
        sub_004369F0(&key, &tmp);
        sub_0057A860(&c, &tmp);
        sub_004220A0(&tmp);
    } else {
        Str_58B970 k;
        Ref_58B970 r;
        imp_00607334(&k, cam);
        sub_00464600(sub_0045C740(tbl, &r, k), &tmp);
        sub_0057A860(&c, &tmp);
        sub_004220A0(&tmp);
        imp_00607330(&r.key);
    }
    sub_0058B090(this, &c);
    *(void **)(s + 0x294) = *(void **)(s + 0x290);
    o = sub_005E3EAE(0x324);
    if (o) {
        Str_58B970 x, y;
        imp_00607324(&y, d_0060C2E8);
        imp_00607324(&x, d_0060C2D8);
        o = sub_004EC6F0(o, s + 0x294, *(void **)(s + 0x290), 0, x, y);
    }
    put_58B970((void **)(s + 0x34c), o);
    sub_004220A0(&c);
    imp_00607330(desc);
    sub_004220A0(&w);
    *(void **)(s + 0x298) = 0;
}
