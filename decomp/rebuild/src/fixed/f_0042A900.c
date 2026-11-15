/* 0x0042A900: forwards to slot 0x28 of the driven object at +0x1C4. */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef int (__thiscall *vf_42A900)(void *self, unsigned int arg);

DECOMP(0042A900)
int __thiscall f_0042A900(char *this, unsigned int arg)
{
    char *driven = *(char **)(this + 0x1c4);

    return ((vf_42A900)(*(void ***)driven)[0x28 / 4])(driven, arg);
}
