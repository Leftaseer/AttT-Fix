/* 0x00425F40: the ActionScript singleton's deleting destructor: the vtable 0x00607ED0 and operator delete when
 * the low bit of the flags argument is set.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607ED0[];
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00425F40)
void *__thiscall f_00425F40(void *this, unsigned char flags)
{
    *(const void **)this = d_00607ED0;
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
