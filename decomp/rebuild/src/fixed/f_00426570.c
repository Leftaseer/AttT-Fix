/* 0x00426570: the 2D render size (+0x74/+0x78) moved by the vector and the +0x7C flag set; returns the vector */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00426570)
void *__thiscall f_00426570(void *this, float *v)
{
    char *s = (char *)this;
    *(float *)(s + 0x74) += v[0];
    *(float *)(s + 0x78) += v[1];
    s[0x7c] = 1;
    return v;
}
