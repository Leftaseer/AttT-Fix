/* 0x00427070: the float at +0x94. */
/* @conv ECX 0 */
#include "auto_pre.h"

DECOMP(00427070)
float __thiscall f_00427070(void *this)
{
    return *(float *)((char *)this + 0x94);
}
