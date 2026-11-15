/* 0x00426EC0: allocates a list node holding the argument, appends it after the current last node of the +0x5C
 * list, tells the +0x58 part, and fixes the neighbour links. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C unsigned int __stdcall sub_005AD6C0(unsigned int head, unsigned int prev, unsigned int *value);
DECOMP_C unsigned int __thiscall sub_004E0EF0(void *self, unsigned int one);

DECOMP(00426EC0)
void __thiscall f_00426EC0(void *this, unsigned int value)
{
    char *s = (char *)this;
    char *head = *(char **)(s + 0x5c);
    unsigned int node = sub_005AD6C0((unsigned int)head, *(unsigned int *)(head + 4), &value);

    sub_004E0EF0(s + 0x58, 1);
    *(unsigned int *)(head + 4) = node;
    *(unsigned int *)*(unsigned int *)(node + 4) = node;
}
