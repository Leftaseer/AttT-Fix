/* 0x0042E420: the projectile's scalar deleting destructor: 0x0042E330, then operator delete when bit 0 of the flag
 * is set; returns this */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042E330(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                       /* operator delete */

DECOMP(0042E420)
void *__thiscall f_0042E420(void *this, unsigned char flag)
{
    sub_0042E330(this);
    if (flag & 1)
        sub_005E3E9C(this);
    return this;
}
