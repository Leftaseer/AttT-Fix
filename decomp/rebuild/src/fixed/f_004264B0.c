/* 0x004264B0: the 2D render y (+0x5C) set and the +0x60 flag set; returns EAX */
/* @func 004264B0 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

DECOMP(004264B0)
unsigned int __cdecl f_004264B0(void *this, unsigned int eax, float y)
{
    char *s = (char *)this;
    *(float *)(s + 0x5c) = y;
    s[0x60] = 1;
    return eax;
}
