/* 0x00426EA0: the alpha control manager's deleting destructor: the destructor, then the delete if the flag says
 * so; returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00426D50(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00426EA0)
void *__thiscall f_00426EA0(void *this, unsigned int flags)
{
    sub_00426D50(this);
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
