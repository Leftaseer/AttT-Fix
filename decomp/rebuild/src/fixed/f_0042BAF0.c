/* 0x0042BAF0: the army screen's deleting destructor: runs 0x0042B910 and, when the free flag is set, releases the
 * object (0x005E3E9C); returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042B910(void *self);
DECOMP_C unsigned int __cdecl sub_005E3E9C(void *self);

DECOMP(0042BAF0)
void *__thiscall f_0042BAF0(void *this, unsigned int freeing)
{
    sub_0042B910(this);
    if (freeing & 1)
        sub_005E3E9C(this);
    return this;
}
