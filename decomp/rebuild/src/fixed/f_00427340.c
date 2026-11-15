/* 0x00427340: puts the vtable 0x00608250 at +0. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608250[];

DECOMP(00427340)
void __thiscall f_00427340(void *this)
{
    *(const void **)this = d_00608250;
}
