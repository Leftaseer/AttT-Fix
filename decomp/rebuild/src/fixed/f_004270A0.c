/* 0x004270A0: puts the vtable 0x00608214 at +0. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_00608214[];

DECOMP(004270A0)
void __thiscall f_004270A0(void *this)
{
    *(const void **)this = d_00608214;
}
