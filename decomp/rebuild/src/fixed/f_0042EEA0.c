/* 0x0042EEA0: the deleting destructor of nCfg::GamePath: 0x0042EE40, then operator delete when bit 0 of the flag is
 * set; returns this */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042EE40(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(0042EEA0)
void *__thiscall f_0042EEA0(void *this, unsigned char flag)
{
    sub_0042EE40(this);
    if (flag & 1)
        sub_005E3E9C(this);
    return this;
}
