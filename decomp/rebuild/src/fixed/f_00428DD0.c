/* 0x00428DD0: releases a sound map node's item vector (+0x24) and clears it (+0x24..+0x2C); the node itself is
 * not freed (the erase routines do that). */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *block);                        /* operator delete */

DECOMP(00428DD0)
void __cdecl f_00428DD0(void *node)
{
    char *n = (char *)node;

    if (*(void **)(n + 0x24) != 0)
        sub_005E3E9C(*(void **)(n + 0x24));
    *(void **)(n + 0x24) = 0;
    *(void **)(n + 0x28) = 0;
    *(void **)(n + 0x2c) = 0;
}
