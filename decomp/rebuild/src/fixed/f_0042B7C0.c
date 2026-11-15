/* 0x0042B7C0: installs vtable 0x00608848 (the object and the registers are otherwise left alone). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608848[];

DECOMP(0042B7C0)
void __thiscall f_0042B7C0(void *this)
{
    *(void **)this = d_00608848;
}
