/* 0x004274B0: descends the +0 links while they are not the head; returns the last real node. */
/* @conv 0 */
#include "auto_pre.h"

DECOMP(004274B0)
void *__cdecl f_004274B0(void *node)
{
    char *cur = (char *)node, *next = *(char **)(cur + 0);
    while (!next[0x31]) {
        cur = next;
        next = *(char **)(cur + 0);
    }
    return cur;
}
