/* 0x0042AF30: whether the animation reached the key the driven object currently shows (its index against +0x204). */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(0042AF30)
unsigned int __thiscall f_0042AF30(void *this)
{
    return *(unsigned int *)(*(char **)((char *)this + 0x1c4) + 0x1d8) == *(unsigned int *)((char *)this + 0x204);
}
