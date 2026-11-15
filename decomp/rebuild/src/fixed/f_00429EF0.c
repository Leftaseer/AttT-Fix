/* 0x00429EF0: the scalar deleting destructor of the ambient sound manager: 0x00429B40, then operator delete when the
 * flag's bit 0 is set; the object pointer is returned. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00429B40(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);                        /* operator delete */

DECOMP(00429EF0)
void *__thiscall f_00429EF0(void *this, unsigned int flag)
{
    sub_00429B40(this);
    if (flag & 1)
        sub_005E3E9C(this);
    return this;
}
