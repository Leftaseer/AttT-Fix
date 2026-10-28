/* 0x00480200: whether the polygon (the list iterator it) is convex: walking from *it, each corner's turn (0x00480020
 * of the point after next with the two before it) must keep the side of the previous one (1 or 0; 4 at the start);
 * *it advances; a bool in AL */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C int __thiscall sub_00480020(void *p, void *e0, void *e1);

DECOMP(00480200)
unsigned char __thiscall f_00480200(void *this)
{
    char **it = (char **)this;
    int n = ((int *)it)[1], prev = 4;
    while (n) {
        char *node = *it, *nx, *nn;
        unsigned int *p;
        unsigned int a[2], b[2], c[2];
        int r;
        n--;
        p = node ? (unsigned int *)(node + 0xc) : 0;
        a[0] = p[0]; a[1] = p[1];
        nx = *(char **)(node + 4);
        *it = nx;
        p = nx ? (unsigned int *)(nx + 0xc) : 0;
        b[0] = p[0]; b[1] = p[1];
        nn = *(char **)(nx + 4);
        p = nn ? (unsigned int *)(nn + 0xc) : 0;
        c[0] = p[0]; c[1] = p[1];
        r = sub_00480020(c, a, b);
        if (prev == 0 ? r == 1 : prev == 1 && r == 0)
            return 0;
        prev = r;
    }
    return 1;
}
