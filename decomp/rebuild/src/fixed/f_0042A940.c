/* 0x0042A940: forwards to slot 0x3C of the driven object at +0x1C4. */
/* @conv ECX 0 */
#include "auto_pre.h"

typedef int (__thiscall *vf_42A940)(void *self);

DECOMP(0042A940)
int __thiscall f_0042A940(char *this)
{
    char *driven = *(char **)(this + 0x1c4);

    return ((vf_42A940)(*(void ***)driven)[0x3c / 4])(driven);
}
