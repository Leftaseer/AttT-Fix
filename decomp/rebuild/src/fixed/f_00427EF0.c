/* 0x00427EF0: destroys the object at +0xC and then the one at +0 (both by tail call to 0x0044CFE0). */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_0044CFE0(void *self);

DECOMP(00427EF0)
void __thiscall f_00427EF0(void *this)
{
    sub_0044CFE0((char *)this + 0xc);
    sub_0044CFE0(this);
}
