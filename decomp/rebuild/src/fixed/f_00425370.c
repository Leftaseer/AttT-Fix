/* 0x00425370: C3DControlsManager's deleting destructor: the destructor (0x004251D0) runs and, with bit 0 of the
 * flag set, the object itself is freed with the MSVCR80 operator delete.  Returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004251D0(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block); /* operator delete */

DECOMP(00425370)
void *__thiscall f_00425370(void *this, int flags)
{
    sub_004251D0(this);
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
