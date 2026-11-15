/* 0x004F4390: scalar deleting destructor: frees the pointer at +0x14, clears +0x14..+0x1C, releases the member
 * at +4 through 0x4F20B0, frees its pointer at +8 and clears it; with bit 0 of the flags set the object itself
 * is freed as well. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_005E3E9C(void *p);
DECOMP_C void __thiscall sub_004F20B0(void *self);

DECOMP(004F4390)
void *__thiscall f_004F4390(char *this, unsigned int flags)
{
    if (*(void **)(this + 0x14))
        sub_005E3E9C(*(void **)(this + 0x14));
    *(void **)(this + 0x14) = 0;
    *(void **)(this + 0x18) = 0;
    *(void **)(this + 0x1c) = 0;
    sub_004F20B0(this + 4);
    sub_005E3E9C(*(void **)(this + 8));
    *(void **)(this + 8) = 0;
    if (flags & 1)
        sub_005E3E9C(this);
    return this;
}
