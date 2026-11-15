/* 0x0042A910: forwards to slot 0x30 of the driven object at +0x1C4. */
/* @conv ECX 0 */
#include "auto_pre.h"

typedef int (__thiscall *vf_42A910)(void *self);

DECOMP(0042A910)
int __thiscall f_0042A910(char *this)
{
    char *driven = *(char **)(this + 0x1c4);

    return ((vf_42A910)(*(void ***)driven)[0x30 / 4])(driven);
}
