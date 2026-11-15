/* 0x00427330: puts the vtable 0x00608250 at +0; returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608250[];

DECOMP(00427330)
void *__thiscall f_00427330(void *this)
{
    *(const void **)this = d_00608250;
    return this;
}
