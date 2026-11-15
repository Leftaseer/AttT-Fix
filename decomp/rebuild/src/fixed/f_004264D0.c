/* 0x004264D0: the 2D render position +0x58/+0x5C moved by the vector and the +0x60 flag set; returns the vector */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(004264D0)
void *__thiscall f_004264D0(void *this, float *v)
{
    char *s = (char *)this;
    *(float *)(s + 0x58) += v[0];
    *(float *)(s + 0x5c) += v[1];
    s[0x60] = 1;
    return v;
}
