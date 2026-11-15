/* 0x0042B650: stores the value at +0x50. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0042B650)
void __thiscall f_0042B650(void *this, unsigned int value)
{
    *(unsigned int *)((char *)this + 0x50) = value;
}
