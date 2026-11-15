/* 0x0042A8B0: CSimpleAnimation vf slot: unless the flag at +0x49 is clear (then the input EAX passes through),
 * releases 0x4AC890 first if +0x1E4 is set and forwards the argument to slot 0xC4 of the object at +0x1C4. */
/* @conv EAX,ECX 4 */
/* @func 0042A8B0 custom */
#include "auto_pre.h"
DECOMP_C void __thiscall sub_004AC890(void *self);
typedef int (__thiscall *vf_42A8B0)(void *self, undefined4 arg);

DECOMP(0042A8B0)
int __cdecl f_0042A8B0(undefined4 in_eax, char *this, undefined4 arg)
{
    void *o;

    if (!this[0x49])
        return in_eax;
    if (this[0x1e4])
        sub_004AC890(this);
    o = *(void **)(this + 0x1c4);
    return ((vf_42A8B0)(*(void ***)o)[0xc4 / 4])(o, arg);
}
