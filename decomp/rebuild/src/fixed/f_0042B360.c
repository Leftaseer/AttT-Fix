/* 0x0042B360: CLoopAnimation's deleting destructor: vtable 0x00608744, the base destructor and, when the flag asks
 * for it, operator delete.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042A720(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                         /* operator delete */
DECOMP_C char d_00608744[];

DECOMP(0042B360)
void *__thiscall f_0042B360(char *this, unsigned int freeing)
{
    *(void **)this = d_00608744;
    sub_0042A720(this);
    if (freeing & 1)
        sub_005E3E9C(this);
    return this;
}
