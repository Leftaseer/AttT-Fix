/* 0x00426B10: with the +0x49 flag set, the call goes on to the mesh's update virtual (no stack arguments); without
 * it the result EAX comes back untouched */
/* @func 00426B10 custom */
/* @conv ECX,EAX 0 */
#include "auto_pre.h"
DECOMP_C unsigned int __thiscall sub_004796D0(void *self);

DECOMP(00426B10)
unsigned int __cdecl f_00426B10(void *this, unsigned int eax)
{
    if (((char *)this)[0x49])
        return sub_004796D0(this);
    return eax;
}
