/* 0x00426BD0: the alpha control's deleting destructor: the control destructor, then the delete if the flag says so.
 * Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00426AB0(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00426BD0)
void *__thiscall f_00426BD0(void *this, unsigned int flags)
{
    sub_00426AB0(this);
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
