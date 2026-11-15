/* 0x004273C0: the deleting destructor: vtable 0x00608250, then the delete on flag bit 0; returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00608250[];
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(004273C0)
void *__thiscall f_004273C0(void *this, unsigned int flags)
{
    *(const void **)this = d_00608250;
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
