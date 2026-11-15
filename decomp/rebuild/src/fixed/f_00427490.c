/* 0x00427490: descends the +8 links while they are not the head (the +0x31 flag on the head is set); returns the
 * last real node. */
/* @conv 0 */
#include "auto_pre.h"

DECOMP(00427490)
void *__cdecl f_00427490(void *node)
{
    char *cur = (char *)node, *next = *(char **)(cur + 8);
    while (!next[0x31]) {
        cur = next;
        next = *(char **)(cur + 8);
    }
    return cur;
}
