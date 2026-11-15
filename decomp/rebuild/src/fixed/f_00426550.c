/* 0x00426550: the address of the 2D render position (+0x58) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(00426550)
void *__thiscall f_00426550(void *this)
{
    return (char *)this + 0x58;
}
