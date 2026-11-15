/* 0x00427350: the number of 12-byte elements between +4 and +8 (0 when +4 is null). */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(00427350)
int __thiscall f_00427350(void *this)
{
    char *s = (char *)this;
    int first = *(int *)(s + 4);
    if (!first)
        return 0;
    return (*(int *)(s + 8) - first) / 0xc;
}
