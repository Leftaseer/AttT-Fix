/* 0x0042B7B0: installs vtable 0x00608848 and returns this. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608848[];

DECOMP(0042B7B0)
void *__thiscall f_0042B7B0(void *this)
{
    *(void **)this = d_00608848;
    return this;
}
