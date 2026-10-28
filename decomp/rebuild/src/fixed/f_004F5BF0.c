/* 0x004F5BF0: a unit enters the sound manager's view: not yet tracked (map +0x54, 0x004EDF50) it is added only if its
 * sound set (vf8C, a name, in the bank +0xA4: 0x004EE860) exists (0x004F4100); tracked, its group (the node's +0xC)
 * gets the time +0xB0 (0x004EE630), and unless it is still alive (vf80 >= vf84) with the same sound set and sounds,
 * or listed at +0x108 and still alive, the group is retired (0x004EE240 false: queued at +0x7C, 0x004F5AE0 /
 * 0x004F1A20), the node erased (0x004F24C0) and the unit added anew; true (in AL) unless the set was missing */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004EDF50(void *map, char **out, void *key);
DECOMP_C void *__thiscall sub_004EE860(void *bank, void *name);
DECOMP_C void __thiscall sub_004F4100(void *self, void *unit);
DECOMP_C void __thiscall sub_004EE630(void *g, float t, void *unit);
DECOMP_C unsigned int __cdecl sub_004EE240(void *g, void *eax, int a);
DECOMP_C void *__thiscall sub_004F5AE0(void *self, void *key);
DECOMP_C void __thiscall sub_004F1A20(void *self, void *g);
DECOMP_C void __thiscall sub_004F24C0(void *map, void *key, char *node);
DECOMP_C void (__thiscall *imp_00607334)(void *, const void *) __asm__("__imp_??0?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@ABV01@@Z");
DECOMP_C void (__thiscall *imp_00607330)(void *) __asm__("__imp_??1?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@QAE@XZ");
DECOMP_C int (__cdecl *imp_00607210)(const void *, const void *) __asm__("__imp_??$?8DU?$char_traits@D@std@@V?$allocator@D@1@@std@@YA_NABV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@0@0@Z");
typedef void *(__thiscall *vf8C_4F5BF0)(void *self);
typedef double (__thiscall *vft_4F5BF0)(void *self);

/* the two times in this order (vf80 first, kept as a double) */
static int cmp_4F5BF0(void *u, int nan_true)
{
    double a = ((vft_4F5BF0)(*(void ***)u)[0x80 / 4])(u);
    double b = ((vft_4F5BF0)(*(void ***)u)[0x84 / 4])(u);
    return nan_true ? !(a < b) : a >= b;
}

DECOMP(004F5BF0)
unsigned char __thiscall f_004F5BF0(void *this, void *unit)
{
    char *s = (char *)this;
    char *node, *g;
    char **head, **e;
    sub_004EDF50(s + 0x54, &node, &unit);
    if (node == *(char **)(s + 0x5c)) {
        unsigned int name[7];
        imp_00607334(name, ((vf8C_4F5BF0)(*(void ***)unit)[0x8c / 4])(unit));
        if (!sub_004EE860(*(void **)(s + 0xa4), name)) {
            imp_00607330(name);
            return 0;
        }
        sub_004F4100(this, unit);
        imp_00607330(name);
        return 1;
    }
    g = node + 0xc;
    sub_004EE630(g, *(float *)(s + 0xb0), unit);
    if (cmp_4F5BF0(unit, 1) && (char)imp_00607210(node + 0x4c, ((vf8C_4F5BF0)(*(void ***)unit)[0x8c / 4])(unit)) &&
        *(char **)(g + 0x14) && (*(char **)(g + 0x18) - *(char **)(g + 0x14)) >> 2 &&
        *(void **)(s + 0x44) != unit)
        return 1;
    head = *(char ***)(s + 0x108);
    for (e = (char **)*head; e != head && e[2] != unit; e = (char **)*e)
        ;
    if (e != head && cmp_4F5BF0(unit, 0))
        return 1;
    if (!(char)sub_004EE240(g, e, 0))
        sub_004F1A20(sub_004F5AE0(s + 0x7c, &unit), g);
    sub_004F24C0(s + 0x54, &unit, node);
    sub_004F4100(this, unit);
    return 1;
}
