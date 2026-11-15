/* 0x004276C0: advances the iterator held at +0 (the function's this): past the head (+0x31 set) it wraps to the
 * head's +8; with a +0 child it descends its +8 links, otherwise it climbs the +4 parents while it is their +0. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(004276C0)
void __thiscall f_004276C0(void *this)
{
    unsigned int *slot = (unsigned int *)this;
    unsigned int *node = (unsigned int *)*slot;
    unsigned int *child, *parent;
    char color;

    if (((char *)node)[0x31]) {
        *slot = node[2];
        return;
    }
    child = (unsigned int *)node[0];
    if (((char *)child)[0x31]) {
        parent = (unsigned int *)node[1];
        color = ((char *)parent)[0x31];
        while (!color && *slot == parent[0]) {
            *slot = (unsigned int)parent;
            parent = (unsigned int *)parent[1];
            color = ((char *)parent)[0x31];
        }
        if (!((char *)*slot)[0x31])
            *slot = (unsigned int)parent;
        return;
    }
    color = ((char *)((unsigned int *)child[2]))[0x31];
    parent = (unsigned int *)child[2];
    while (!color) {
        color = ((char *)((unsigned int *)parent[2]))[0x31];
        child = parent;
        parent = (unsigned int *)parent[2];
    }
    *slot = (unsigned int)child;
}
