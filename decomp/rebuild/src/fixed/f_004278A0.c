/* 0x004278A0: the deleting destructor of the script read: releases it (0x00427820), then deletes on flag bit 0;
 * returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_00427820(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *block);

DECOMP(004278A0)
void *__thiscall f_004278A0(void *this, unsigned int flags)
{
    sub_00427820(this);
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
