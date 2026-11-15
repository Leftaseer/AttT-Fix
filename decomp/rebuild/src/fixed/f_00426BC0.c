/* 0x00426BC0: the non-virtual thunk of the 2D part: adjusts this (-0x54) and enters the deleting destructor */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_00426BD0(void *self, unsigned int flags);

DECOMP(00426BC0)
void *__thiscall f_00426BC0(void *this, unsigned int flags)
{
    return sub_00426BD0((char *)this - 0x54, flags);
}
