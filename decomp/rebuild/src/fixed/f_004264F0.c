/* 0x004264F0: the 2D render position +0x58/+0x5C moved by the two floats and the +0x60 flag set; returns EAX */
/* @func 004264F0 custom */
/* @conv ECX,EAX 8 */
#include "auto_pre.h"

DECOMP(004264F0)
unsigned int __cdecl f_004264F0(void *this, unsigned int eax, float x, float y)
{
    char *s = (char *)this;
    s[0x60] = 1;
    *(float *)(s + 0x58) += x;
    *(float *)(s + 0x5c) += y;
    return eax;
}
