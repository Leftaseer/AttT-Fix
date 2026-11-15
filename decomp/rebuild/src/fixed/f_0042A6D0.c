/* 0x0042A6D0: whether the driven object's index (+0x1D8) is the animation's last key (+0x1D4). */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042A6D0)
int __thiscall f_0042A6D0(char *this)
{
    char *driven = *(char **)(this + 0x1c4);

    return *(unsigned int *)(driven + 0x1d8) == *(unsigned int *)(this + 0x1d4);
}
