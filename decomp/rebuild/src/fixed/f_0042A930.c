/* 0x0042A930: forwards to slot 0x34 of the driven object at +0x1C4. */
/* @conv ECX 4 */
#include "auto_pre.h"

typedef int (__thiscall *vf_42A930)(void *self, unsigned int arg);

DECOMP(0042A930)
int __thiscall f_0042A930(char *this, unsigned int arg)
{
    char *driven = *(char **)(this + 0x1c4);

    return ((vf_42A930)(*(void ***)driven)[0x34 / 4])(driven, arg);
}
