/* 0x0042B150: the CLoopAnimation destructor body: vtable 0x00608744 and the CSimpleAnimation base destructor. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042A720(void *self);
DECOMP_C char d_00608744[];

DECOMP(0042B150)
void __thiscall f_0042B150(char *this)
{
    *(void **)this = d_00608744;
    sub_0042A720(this);
}
