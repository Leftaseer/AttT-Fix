/* 0x0042B630: stores the pointer at +0x10 and returns it. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(0042B630)
void *__thiscall f_0042B630(void *this, void *value)
{
    *(void **)((char *)this + 0x10) = value;
    return value;
}
