/* 0x004269A0: the non-virtual thunk of the 2D part: adjusts this (-0x54) and enters the deleting destructor */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void *__thiscall sub_004269B0(void *self, unsigned int flags);

DECOMP(004269A0)
void *__thiscall f_004269A0(void *this, unsigned int flags)
{
    return sub_004269B0((char *)this - 0x54, flags);
}
