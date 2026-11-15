/* 0x00426470: the 2D render position +0x58/+0x5C set from the two floats and the +0x60 flag set; returns EAX */
/* @func 00426470 custom */
/* @conv ECX,EAX 8 */
#include "auto_pre.h"

DECOMP(00426470)
unsigned int __cdecl f_00426470(void *this, unsigned int eax, float x, float y)
{
    char *s = (char *)this;
    *(float *)(s + 0x58) = x;
    *(float *)(s + 0x5c) = y;
    s[0x60] = 1;
    return eax;
}
