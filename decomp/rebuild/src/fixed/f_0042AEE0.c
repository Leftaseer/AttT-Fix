/* 0x0042AEE0: CInvSimpleAnimation vf slot: unless the flag at +0x49 is clear (then the input EAX passes through),
 * stores the step count (+0x1C8 minus +0x1CC, less one) at +0x1D8 of the object at +0x1C4 and forwards the
 * argument to its slot 0xCC. */
/* @conv EAX,ECX 4 */
/* @func 0042AEE0 custom */
#include "auto_pre.h"
typedef int (__thiscall *vf_42AEE0)(void *self, undefined4 arg);

DECOMP(0042AEE0)
int __cdecl f_0042AEE0(undefined4 in_eax, char *this, undefined4 arg)
{
    char *o;

    if (!this[0x49])
        return in_eax;
    o = *(char **)(this + 0x1c4);
    *(unsigned int *)(o + 0x1d8) = *(unsigned int *)(this + 0x1c8)
                                   - *(unsigned int *)(this + 0x1cc) - 1;
    return ((vf_42AEE0)(*(void ***)o)[0xcc / 4])(o, arg);
}
