/* 0x00427720: the mirror of 0x004276C0: with a real +8 child it descends the +0 links, otherwise it climbs the +4
 * parents while it is their +8; the iterator held at +0 is updated in place. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(00427720)
void __thiscall f_00427720(void *this)
{
    unsigned int *slot = (unsigned int *)this;
    unsigned int *node = (unsigned int *)*slot, *n, *cur, *parent;
    char color;

    if (((char *)node)[0x31])
        return;
    n = (unsigned int *)node[2];
    if (!((char *)n)[0x31]) {
        cur = (unsigned int *)*n;
        color = ((char *)cur)[0x31];
        while (!color) {
            color = ((char *)((unsigned int *)*cur))[0x31];
            n = cur;
            cur = (unsigned int *)*cur;
        }
        *slot = (unsigned int)n;
        return;
    }
    parent = (unsigned int *)node[1];
    color = ((char *)parent)[0x31];
    while (!color && *slot == parent[2]) {
        *slot = (unsigned int)parent;
        parent = (unsigned int *)parent[1];
        color = ((char *)parent)[0x31];
    }
    *slot = (unsigned int)parent;
}
