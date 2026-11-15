/* 0x0042B240: CSimpleAnimation's deleting destructor: only the base destructor, then operator delete when the flag
 * asks for it.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042A720(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                         /* operator delete */

DECOMP(0042B240)
void *__thiscall f_0042B240(void *this, unsigned int freeing)
{
    sub_0042A720(this);
    if (freeing & 1)
        sub_005E3E9C(this);
    return this;
}
