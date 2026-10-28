/* 0x00525540: a constructor from Lua arguments (x, y, z: the numbers at the arguments' base + 1..3, as floats):
 * the vtables at +0 and +8, +4 and +0x20 cleared, then 0x00525070(x, y, z) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);
DECOMP_C void __thiscall sub_00525070(void *self, float x, float y, float z);
DECOMP_C char d_008D122C[], d_00608214[], d_006149AC[], d_006149A4[];

DECOMP(00525540)
void *__thiscall f_00525540(void *this, char *args)
{
    unsigned int *s = (unsigned int *)this;
    float x, y, z;
    s[1] = 0;
    s[2] = (unsigned int)d_00608214;
    s[0] = (unsigned int)d_006149AC;
    s[2] = (unsigned int)d_006149A4;
    s[0x20 / 4] = 0;
    z = (float)sub_00402DE0(*(void **)d_008D122C, *(int *)(args + 0x10) + 3);
    y = (float)sub_00402DE0(*(void **)d_008D122C, *(int *)(args + 0x10) + 2);
    x = (float)sub_00402DE0(*(void **)d_008D122C, *(int *)(args + 0x10) + 1);
    sub_00525070(this, x, y, z);
    return this;
}
