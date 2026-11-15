/* 0x00425DA0: the small ActionScript base's deleting destructor: like 0x00425D80, then operator delete when
 * the low bit of the flags argument is set.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607E94[];
DECOMP_C int d_006C8738;
DECOMP_C void __thiscall sub_00424C70(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00425DA0)
void *__thiscall f_00425DA0(void *this, unsigned char flags)
{
    *(const void **)this = d_00607E94;
    d_006C8738--;
    sub_00424C70(this);
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
