/* 0x00427980: copies the first dword of what +4 points at to arg 1 (the front of a container held by pointer). */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00427980)
void __thiscall f_00427980(void *this, unsigned int *out)
{
    *out = **(unsigned int **)((char *)this + 4);
}
