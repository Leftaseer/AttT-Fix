/* 0x00427610: rotates the node's +8 link up: y = node->+8 takes the node's place (the +4 parent, the head's +4 or
 * the parent's +0/+8 link are rewired) and adopts the node as its +0 child. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00427610)
void __thiscall f_00427610(void *this, void *where)
{
    char *s = (char *)this;
    char *node = (char *)where;
    char *y = *(char **)(node + 8);
    char *parent;
    *(char **)(node + 8) = *(char **)y;
    if (!(*(char **)y)[0x31])
        *(char **)(*(char **)y + 4) = node;
    *(char **)(y + 4) = *(char **)(node + 4);
    if (node == *(char **)(*(char **)(s + 4) + 4)) {
        *(char **)(*(char **)(s + 4) + 4) = y;
        *(char **)y = node;
        *(char **)(node + 4) = y;
        return;
    }
    parent = *(char **)(node + 4);
    if (node == *(char **)parent) {
        *(char **)parent = y;
        *(char **)y = node;
        *(char **)(node + 4) = y;
        return;
    }
    *(char **)(parent + 8) = y;
    *(char **)y = node;
    *(char **)(node + 4) = y;
}
