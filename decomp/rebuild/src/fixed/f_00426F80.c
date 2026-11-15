/* 0x00426F80: pushes a number (lua_pushnumber) and counts it in +8; returns this. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_004030A0(void *L, float n);               /* lua_pushnumber */
DECOMP_C char d_008D122C[];

DECOMP(00426F80)
void *__thiscall f_00426F80(void *this, float n)
{
    char *s = (char *)this;
    sub_004030A0(*(void **)d_008D122C, n);
    ++*(int *)(s + 8);
    return s;
}
