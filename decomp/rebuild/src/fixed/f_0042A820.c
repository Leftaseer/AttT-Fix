/* 0x0042A820: unless the object is hidden (+0x49 clear means the input EAX passes through), releases 0x004AC890
 * first if +0x1E4 is set and forwards to slot 0xD0 of the driven object at +0x1C4; its result is returned. */
/* @conv ECX,EAX 0 */
/* @func 0042A820 custom */
#include "auto_pre.h"

DECOMP_C void __thiscall sub_004AC890(void *self);
typedef int (__thiscall *vf_42A820)(void *self);

DECOMP(0042A820)
int __cdecl f_0042A820(char *this, unsigned int in_eax)
{
    char *driven;

    if (!this[0x49])
        return in_eax;
    if (this[0x1e4])
        sub_004AC890(this);
    driven = *(char **)(this + 0x1c4);
    return ((vf_42A820)(*(void ***)driven)[0xd0 / 4])(driven);
}
