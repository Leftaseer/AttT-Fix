/* 0x00480AC0: walks the polygon's edges from the node *it (0x00480020 exactly 1), the count of its list at it[1]: each edge (the points
 * at +0xC of the node and its next, copied as four dwords) must pass; *it moves to the next node; true (in AL) when
 * all passed */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_00480020(void *p, float *e0, float *e1);

DECOMP(00480AC0)
unsigned char __cdecl f_00480AC0(char **it, void *p)
{
    int n = ((int *)it)[1];
    while (n) {
        char *node = *it, *next = *(char **)(node + 4);
        unsigned int *a = node ? (unsigned int *)(node + 0xc) : 0;
        unsigned int *b = next ? (unsigned int *)(next + 0xc) : 0;
        unsigned int e[4];
        n--;
        e[0] = a[0]; e[1] = a[1];
        e[2] = b[0]; e[3] = b[1];
        if (sub_00480020(p, (float *)e, (float *)(e + 2)) != 1)
            return 0;
        *it = next;
    }
    return 1;
}
