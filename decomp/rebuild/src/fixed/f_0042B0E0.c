/* 0x0042B0E0: whether the driven object's index equals the loop's end key (+0x208). */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042B0E0)
unsigned int __thiscall f_0042B0E0(char *this)
{
    return *(unsigned int *)(*(char **)(this + 0x1c4) + 0x1d8) == *(unsigned int *)(this + 0x208);
}
