/* 0x0047FEF0: walks the polygon's edges from the node *it (the count of its list at it[1]): each edge (the points at
 * +0xC of the node and its next, copied as four dwords) must have 0x0047FA20(x, y, edge) + eps above 0; *it moves to
 * the next node; true (in AL) when all passed */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C double __cdecl sub_0047FA20(float x, float y, float *edge);

DECOMP(0047FEF0)
unsigned char __cdecl f_0047FEF0(char **it, float x, float y, float eps)
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
        if (0.0 >= sub_0047FA20(x, y, (float *)e) + eps)
            return 0;
        *it = next;
    }
    return 1;
}
