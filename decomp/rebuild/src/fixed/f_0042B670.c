/* 0x0042B670: returns the index stored at +0x1D8 (the driven object's key index). */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042B670)
unsigned int __thiscall f_0042B670(void *this)
{
    return *(unsigned int *)((char *)this + 0x1d8);
}
