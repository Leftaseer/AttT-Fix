/* 0x004265D0: the 2D render height (+0x78) moved by the float and the +0x7C flag set; returns EAX */
/* @func 004265D0 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

DECOMP(004265D0)
unsigned int __cdecl f_004265D0(void *this, unsigned int eax, float h)
{
    char *s = (char *)this;
    s[0x7c] = 1;
    *(float *)(s + 0x78) += h;
    return eax;
}
