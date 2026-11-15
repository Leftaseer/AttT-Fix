/* 0x00426590: the 2D render size +0x74/+0x78 moved by the two floats and the +0x7C flag set; returns EAX */
/* @func 00426590 custom */
/* @conv ECX,EAX 8 */
#include "auto_pre.h"

DECOMP(00426590)
unsigned int __cdecl f_00426590(void *this, unsigned int eax, float w, float h)
{
    char *s = (char *)this;
    s[0x7c] = 1;
    *(float *)(s + 0x74) += w;
    *(float *)(s + 0x78) += h;
    return eax;
}
