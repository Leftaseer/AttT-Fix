/* 0x0042B660: returns the value at +0x50. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042B660)
unsigned int __thiscall f_0042B660(void *this)
{
    return *(unsigned int *)((char *)this + 0x50);
}
