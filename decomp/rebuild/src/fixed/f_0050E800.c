/* 0x0050E800: whether a unit (arg 1) can take all of a group (arg 2, 0x0051DAA0 members, the first +0x58) in battle
 * (arg 3: attacking rather than moving): an attacker must be able to act (0x0051DBF0 on the group's +0x98), a mover
 * must have its cell (arg 1's +0x7C) free in that map; the reach (0x00504400 / 0x00503D20 on +0xD8, then its +0x15C /
 * +0x150 maps: 0x00503BC0 by the unit, 0x00502D10 by the first member) is copied (0x005019E0, passed by value) to the battle's
 * search (0x004E46D0, 0x004FB800 with 1 / 0) and merged into a set (0x0050A650); true when the set covers the group
 * and every entry is complete (the sum of 0x00511E00 on +0x0C less +0x10 is 0). The set is a std::set built and
 * freed inline (0x004FA480 head, 0x004FAF90 erase, 0x004FB2C0) */
/* @conv ECX 12 */
#include "auto_pre.h"
typedef struct { unsigned int w[3]; } Obj12_50E800;
typedef struct { unsigned int alloc; char *head; unsigned int size; } Set_50E800;
DECOMP_C unsigned int __thiscall sub_0051DAA0(void *self);
DECOMP_C char *__cdecl sub_004FA480(void);
DECOMP_C char __thiscall sub_0051DBF0(void *self, void *map, int a);
DECOMP_C void __thiscall sub_00504400(void *self, void *unit, void *first);
DECOMP_C void __thiscall sub_00503D20(void *self, void *unit, void *first);
DECOMP_C void *__thiscall sub_00503BC0(void *self, void *key);   /* map lookup by *key */
DECOMP_C void *__thiscall sub_00502D10(void *self, void *key);
DECOMP_C void __thiscall sub_005019E0(void *self, void *src);
DECOMP_C void *__cdecl sub_004E46D0(void);
DECOMP_C void *__thiscall sub_004FB800(void *self, void *out, Obj12_50E800 reach, int attack);
DECOMP_C void __thiscall sub_0050A650(void *self, void *src);
DECOMP_C void __thiscall sub_004FB2C0(void *self);
DECOMP_C int __thiscall sub_00511E00(void *self);
DECOMP_C void __thiscall sub_004FA240(void *self);
DECOMP_C void __thiscall sub_004FAF90(void *self, void *out, void *first, void *last);
DECOMP_C void __cdecl sub_005E3E9C(void *p);

DECOMP(0050E800)
unsigned char __thiscall f_0050E800(void *this, char *unit, char *grp, unsigned char attack)
{
    char *s = (char *)this, *it, *dummy;
    void *first, *r;
    Set_50E800 set;
    unsigned int res[3];
    Obj12_50E800 reach;
    int sum;
    if (!sub_0051DAA0(grp))
        return 0;
    first = **(void ***)(grp + 0x58);
    set.head = sub_004FA480();
    set.head[0x15] = 1;
    ((char **)set.head)[1] = set.head;
    ((char **)set.head)[0] = set.head;
    ((char **)set.head)[2] = set.head;
    set.size = 0;
    if (attack) {
        if (!sub_0051DBF0(unit, *(void **)(grp + 0x98), 0)) {
            sub_004FB2C0(&set);
            return 0;
        }
        sub_00504400(*(void **)(s + 0xd8), unit, first);
        r = sub_00502D10(sub_00503BC0(*(char **)(s + 0xd8) + 0x15c, &unit), &first);
    } else {
        if (!(*(char **)(grp + 0x98))[*(int *)(unit + 0x7c)]) {
            sub_004FB2C0(&set);
            return 0;
        }
        sub_00503D20(*(void **)(s + 0xd8), unit, first);
        r = sub_00502D10(sub_00503BC0(*(char **)(s + 0xd8) + 0x150, &unit), &first);
    }
    sub_005019E0(&reach, r);
    sub_0050A650(&set, sub_004FB800(sub_004E46D0(), res, reach, attack ? 1 : 0));
    sub_004FB2C0(res);
    if (set.size < sub_0051DAA0(grp)) {
        sub_004FB2C0(&set);
        return 0;
    }
    sum = 0;
    for (it = *(char **)set.head; it != set.head;) {
        sum += sub_00511E00(*(void **)(it + 0xc)) - *(int *)(it + 0x10);
        sub_004FA240(&it);
    }
    sub_004FAF90(&set, &dummy, *(char **)set.head, set.head);
    sub_005E3E9C(set.head);
    return sum == 0;
}
