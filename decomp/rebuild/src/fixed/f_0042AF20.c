/* 0x0042AF20: another CSimpleAnimation subclass's destructor: vtable 0x0060863C and the base destructor. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042A720(void *self);
DECOMP_C char d_0060863C[];

DECOMP(0042AF20)
void __thiscall f_0042AF20(char *this)
{
    *(void **)this = d_0060863C;
    sub_0042A720(this);
}
