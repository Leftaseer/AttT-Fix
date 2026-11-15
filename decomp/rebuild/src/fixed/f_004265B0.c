/* 0x004265B0: the 2D render width (+0x74) moved by the float and the +0x7C flag set; returns EAX */
/* @func 004265B0 custom */
/* @conv ECX,EAX 4 */
#include "auto_pre.h"

DECOMP(004265B0)
unsigned int __cdecl f_004265B0(void *this, unsigned int eax, float w)
{
    char *s = (char *)this;
    s[0x7c] = 1;
    *(float *)(s + 0x74) += w;
    return eax;
}
