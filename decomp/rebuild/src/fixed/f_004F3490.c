/* 0x004F3490: scalar deleting destructor: releases the member at +0x10 (after the +0xC object's own release),
 * clears it and, when the low flag bit is set, deletes the object itself. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004F1B50(void *self);
DECOMP_C void __cdecl sub_005E3E9C(void *p);

DECOMP(004F3490)
void *__thiscall f_004F3490(char *this, unsigned int flags)
{
    char *member = this + 0xc;

    sub_004F1B50(member);
    sub_005E3E9C(*(void **)(member + 4));
    *(void **)(member + 4) = 0;
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
