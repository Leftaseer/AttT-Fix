/* 0x00427C40: the deleting destructor: the base vtable 0x00607CB8, the _Object destructor 0x00422000 and the
 * delete on flag bit 0; returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00607CB8[];
DECOMP_C unsigned int __thiscall sub_00422000(void *self);             /* _Object::~_Object */
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(00427C40)
void *__thiscall f_00427C40(void *this, unsigned int flags)
{
    *(void **)this = d_00607CB8;
    sub_00422000(this);
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
