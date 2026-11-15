/* 0x0042B640: stores the value at +0x14. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0042B640)
void __thiscall f_0042B640(void *this, unsigned int value)
{
    *(unsigned int *)((char *)this + 0x14) = value;
}
