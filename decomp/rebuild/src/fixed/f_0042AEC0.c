/* 0x0042AEC0: CCritKeyAnimation's destructor: vtable 0x00608534 and the CSimpleAnimation base destructor. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0042A720(void *self);
DECOMP_C char d_00608534[];

DECOMP(0042AEC0)
void __thiscall f_0042AEC0(char *this)
{
    *(void **)this = d_00608534;
    sub_0042A720(this);
}
