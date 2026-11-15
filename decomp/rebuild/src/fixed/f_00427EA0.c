/* 0x00427EA0: advances the iterator at this (0x00427720) and returns it. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00427720(void *self);

DECOMP(00427EA0)
void *__thiscall f_00427EA0(void *this)
{
    sub_00427720(this);
    return this;
}
