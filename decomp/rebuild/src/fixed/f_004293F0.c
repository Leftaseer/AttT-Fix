/* 0x004293F0: frees the subtree at arg 1: for every real node (+0x31 clear) it recurses into the +8 child, saves
 * the +0 child, releases the node's item vector (+0x24) and the node, then continues with the saved child. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);                        /* operator delete */
DECOMP_C void __thiscall sub_004293F0(void *self, char *node);

DECOMP(004293F0)
void __thiscall f_004293F0(void *this, char *node)
{
    while (!node[0x31]) {
        sub_004293F0(this, *(char **)(node + 8));
        char *left = *(char **)node;
        if (*(void **)(node + 0x24) != 0)
            sub_005E3E9C(*(void **)(node + 0x24));
        *(void **)(node + 0x24) = 0;
        *(void **)(node + 0x28) = 0;
        *(void **)(node + 0x2c) = 0;
        sub_005E3E9C(node);
        node = left;
    }
}
