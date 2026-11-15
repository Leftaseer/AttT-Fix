/* 0x00426F60: a number argument shifted by +0x10, read with lua_tonumber. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);             /* lua_tonumber */
DECOMP_C char d_008D122C[];

DECOMP(00426F60)
double __thiscall f_00426F60(void *this, int index)
{
    return sub_00402DE0(*(void **)d_008D122C, index + *(int *)((char *)this + 0x10));
}
