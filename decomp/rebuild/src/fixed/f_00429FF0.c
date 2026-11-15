/* 0x00429FF0: stores the argument at +0x1D8 of the object (a sound channel setter). */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00429FF0)
void __thiscall f_00429FF0(void *this, unsigned int value)
{
    *(unsigned int *)((char *)this + 0x1d8) = value;
}
