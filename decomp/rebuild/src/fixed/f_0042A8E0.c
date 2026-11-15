/* 0x0042A8E0: forwards to slot 0x2C of the driven object at +0x1C4 with the argument and a 0. */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef int (__thiscall *vf_42A8E0)(void *self, unsigned int arg, unsigned int zero);

DECOMP(0042A8E0)
int __thiscall f_0042A8E0(char *this, unsigned int arg)
{
    char *driven = *(char **)(this + 0x1c4);

    return ((vf_42A8E0)(*(void ***)driven)[0x2c / 4])(driven, arg, 0);
}
