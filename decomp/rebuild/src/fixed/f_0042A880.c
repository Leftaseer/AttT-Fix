/* 0x0042A880: like 0x0042A820, forwarding to slot 0xC8 of the driven object at +0x1C4 instead. */
/* @conv ECX,EAX 0 */
/* @func 0042A880 custom */
#include "auto_pre.h"

DECOMP_C void __thiscall sub_004AC890(void *self);
typedef int (__thiscall *vf_42A880)(void *self);

DECOMP(0042A880)
int __cdecl f_0042A880(char *this, unsigned int in_eax)
{
    char *driven;

    if (!this[0x49])
        return in_eax;
    if (this[0x1e4])
        sub_004AC890(this);
    driven = *(char **)(this + 0x1c4);
    return ((vf_42A880)(*(void ***)driven)[0xc8 / 4])(driven);
}
