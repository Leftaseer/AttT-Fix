/* 0x00427FA0: post-increments the map iterator held at +0: the current node is copied to *out, the iterator advances
 * (0x00427720) and out is returned. */
/* @conv ECX 8 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00427720(void *self);

DECOMP(00427FA0)
unsigned int *__thiscall f_00427FA0(void *this, unsigned int *out, unsigned int unused)
{
    *out = *(unsigned int *)this;
    sub_00427720(this);
    return out;
}
