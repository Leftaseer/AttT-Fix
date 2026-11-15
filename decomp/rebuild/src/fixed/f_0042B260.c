/* 0x0042B260: CInvSimpleAnimation's deleting destructor: vtable 0x00608534, the base destructor and, when the flag
 * asks for it, operator delete.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042A720(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                         /* operator delete */
DECOMP_C char d_00608534[];

DECOMP(0042B260)
void *__thiscall f_0042B260(char *this, unsigned int freeing)
{
    *(void **)this = d_00608534;
    sub_0042A720(this);
    if (freeing & 1)
        sub_005E3E9C(this);
    return this;
}
