/* 0x0042B330: the CCritKeyAnimation deleting destructor: vtable 0x0060863C, the base destructor and, when the flag
 * asks for it, operator delete.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042A720(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                         /* operator delete */
DECOMP_C char d_0060863C[];

DECOMP(0042B330)
void *__thiscall f_0042B330(char *this, unsigned int freeing)
{
    *(void **)this = d_0060863C;
    sub_0042A720(this);
    if (freeing & 1)
        sub_005E3E9C(this);
    return this;
}
