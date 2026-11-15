/* 0x00427A40: the node the map's lower bound for key arg 2 sits at: the walk starts at the root (head +4) and goes
 * right (+8) while a node key is below the key, keeping the node it went left from; the head when everything is
 * below.  The node is stored through arg 1. */
/* @conv ECX 8 */
#include "auto_pre.h"

DECOMP(00427A40)
void __thiscall f_00427A40(void *this, char **out, const unsigned int *key)
{
    unsigned int k = *key;
    char *node = *(char **)((char *)this + 4);          /* the head: the result when nothing is kept */
    char *p = *(char **)(node + 4);                     /* the root */
    if (!p[0x31]) {
        do {
            if (*(unsigned int *)(p + 0xc) < k) {
                p = *(char **)(p + 8);
            } else {
                node = p;
                p = *(char **)p;
            }
        } while (!p[0x31]);
    }
    *out = node;
}
