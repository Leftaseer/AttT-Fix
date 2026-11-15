/* 0x00427EB0: steps the iterator at this back one place (0x004276C0) and returns it. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004276C0(void *self);

DECOMP(00427EB0)
void *__thiscall f_00427EB0(void *this)
{
    sub_004276C0(this);
    return this;
}
