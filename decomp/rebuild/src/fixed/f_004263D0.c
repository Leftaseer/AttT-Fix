/* 0x004263D0: a 2D render object's position (+0/+4) moved by the vector; returns this */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(004263D0)
void *__thiscall f_004263D0(void *this, float *v)
{
    char *s = (char *)this;
    *(float *)(s + 0) += v[0];
    *(float *)(s + 4) += v[1];
    return s;
}
