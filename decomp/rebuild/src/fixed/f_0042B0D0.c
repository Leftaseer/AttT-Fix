/* 0x0042B0D0: marks the loop as playing backwards (the +0x20C byte) and returns EAX as it came. */
/* @conv EAX,ECX 0 */
/* @func 0042B0D0 custom */
#include "auto_pre.h"

DECOMP(0042B0D0)
unsigned int __cdecl f_0042B0D0(unsigned int in_eax, char *this)
{
    this[0x20c] = 1;
    return in_eax;
}
