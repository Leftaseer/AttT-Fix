/* 0x00427370: the 12-byte element at the given index. */
/* @conv ECX 4 */
#include "auto_pre.h"

DECOMP(00427370)
void *__thiscall f_00427370(void *this, int index)
{
    return *(char **)((char *)this + 4) + index * 0xc;
}
