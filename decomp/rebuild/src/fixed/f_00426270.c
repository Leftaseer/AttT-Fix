/* 0x00426270: the ActionScript object's deleting destructor: 0x00426070, then operator delete 0x005E3E9C when
 * the low bit of the flags argument is set.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00426070(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00426270)
void *__thiscall f_00426270(void *this, unsigned char flags)
{
    sub_00426070(this);
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
