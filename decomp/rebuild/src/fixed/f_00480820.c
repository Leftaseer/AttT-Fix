/* 0x00480820: walks a circular list of points from *it until 0x00480020 says the point a (the node at +4) lies on
 * the edge test's side for (b, node) (b starting as the node at +8, then the previous node); *it advances by its +4
 * link, a is taken through 0x0047F710 (which leaves EDX, the previous node, alone) */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_00480020(void *p, void *e0, void *e1);
DECOMP_C char *__thiscall sub_0047F710(char **it, int which);

DECOMP(00480820)
void __cdecl f_00480820(char **it)
{
    char *node = *it;
    char *b = *(char **)(node + 8);
    char *a = *(char **)(node + 4);
    for (;;) {
        char *old;
        if (sub_00480020(a + 0xc, b ? b + 0xc : 0, node ? node + 0xc : 0) == 1)
            break;
        old = node;
        node = *(char **)(*it + 4);
        *it = node;
        a = sub_0047F710(it, 0);
        b = old;
    }
}
