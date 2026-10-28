/* 0x0047FF90: walks the polygon's edges from the node *it (0x0047FBC0: the signed distance plus eps above 0), the count of its list at it[1]: each edge (the points
 * at +0xC of the node and its next, copied as four dwords) must pass; *it moves to the next node; true (in AL) when
 * all passed */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C double __thiscall sub_0047FBC0(void *p, float *edge);

DECOMP(0047FF90)
unsigned char __cdecl f_0047FF90(char **it, void *p, float eps)
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
        if (0.0 >= sub_0047FBC0(p, (float *)e) + eps)
            return 0;
        *it = next;
    }
    return 1;
}
