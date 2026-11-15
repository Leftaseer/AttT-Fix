/* 0x00426530: the 2D render y (+0x5C) moved by the float and the +0x60 flag set; returns EAX */
/* @func 00426530 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

DECOMP(00426530)
unsigned int __cdecl f_00426530(void *this, unsigned int eax, float y)
{
    char *s = (char *)this;
    s[0x60] = 1;
    *(float *)(s + 0x5c) += y;
    return eax;
}
