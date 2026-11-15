/* 0x00426510: the 2D render x (+0x58) moved by the float and the +0x60 flag set; returns EAX */
/* @func 00426510 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

DECOMP(00426510)
unsigned int __cdecl f_00426510(void *this, unsigned int eax, float x)
{
    char *s = (char *)this;
    s[0x60] = 1;
    *(float *)(s + 0x58) += x;
    return eax;
}
