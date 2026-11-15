/* 0x00426560: the 2D render x (+0x58) */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(00426560)
float __thiscall f_00426560(void *this)
{
    return *(float *)((char *)this + 0x58);
}
