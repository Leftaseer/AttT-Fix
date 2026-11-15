/* 0x00426490: the 2D render x (+0x58) set and the +0x60 flag set; returns EAX */
/* @func 00426490 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

DECOMP(00426490)
unsigned int __cdecl f_00426490(void *this, unsigned int eax, float x)
{
    char *s = (char *)this;
    *(float *)(s + 0x58) = x;
    s[0x60] = 1;
    return eax;
}
