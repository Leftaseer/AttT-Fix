/* 0x00427080: the (0, -1, -1) triple written at the start of the 12-byte object. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(00427080)
void __thiscall f_00427080(void *this)
{
    unsigned int *p = (unsigned int *)this;
    p[0] = 0;
    p[1] = 0xffffffff;
    p[2] = 0xffffffff;
}
