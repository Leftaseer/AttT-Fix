/* 0x0042ECA0: initialises the vtable-only base of the nCfg::GamePath singleton (0x00608CD4) */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608CD4[];                                            /* vftable */

DECOMP(0042ECA0)
void __thiscall f_0042ECA0(void *this)
{
    *(const void **)this = d_00608CD4;
}
