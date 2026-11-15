/* 0x0042ECF0: the deleting destructor of the vtable-only base of the nCfg::GamePath singleton: vtable 0x00608CD4,
 * then operator delete when bit 0 of the flag is set; returns this */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00608CD4[];                                            /* vftable */
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(0042ECF0)
void *__thiscall f_0042ECF0(void *this, unsigned char flag)
{
    *(const void **)this = d_00608CD4;
    if (flag & 1)
        sub_005E3E9C(this);
    return this;
}
