/* 0x00427660: the mirror rotation: y = node->+0 takes the node's place and adopts it as the +8 child. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00427660)
void __thiscall f_00427660(void *this, void *where)
{
    char *s = (char *)this;
    char *node = (char *)where;
    char *y = *(char **)node;
    char *parent;
    *(char **)node = *(char **)(y + 8);
    if (!(*(char **)(y + 8))[0x31])
        *(char **)(*(char **)(y + 8) + 4) = node;
    *(char **)(y + 4) = *(char **)(node + 4);
    if (node == *(char **)(*(char **)(s + 4) + 4)) {
        *(char **)(*(char **)(s + 4) + 4) = y;
        *(char **)(y + 8) = node;
        *(char **)(node + 4) = y;
        return;
    }
    parent = *(char **)(node + 4);
    if (node == *(char **)(parent + 8)) {
        *(char **)(parent + 8) = y;
        *(char **)(y + 8) = node;
        *(char **)(node + 4) = y;
        return;
    }
    *(char **)parent = y;
    *(char **)(y + 8) = node;
    *(char **)(node + 4) = y;
}
