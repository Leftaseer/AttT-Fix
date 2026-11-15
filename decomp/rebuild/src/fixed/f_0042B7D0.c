/* 0x0042B7D0: the deleting destructor of the 0x00608848 object: the vtable is installed, operator delete runs when
 * the flag's low bit asks for it, and this is returned. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C char d_00608848[];
DECOMP_C void __cdecl sub_005E3E9C(void *block);                         /* operator delete */

DECOMP(0042B7D0)
void *__thiscall f_0042B7D0(void *this, unsigned int freeing)
{
    *(void **)this = d_00608848;
    if (freeing & 1)
        sub_005E3E9C(this);
    return this;
}
