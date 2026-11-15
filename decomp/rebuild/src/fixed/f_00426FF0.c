/* 0x00426FF0: nonzero when the counter at +8 is 5. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(00426FF0)
unsigned int __thiscall f_00426FF0(void *this)
{
    return *(int *)((char *)this + 8) == 5;
}
