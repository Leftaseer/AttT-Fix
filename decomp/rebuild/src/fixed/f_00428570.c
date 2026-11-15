/* 0x00428570: the script "UpdateSoundInPoint" method: the three numbers of the call (stack indices from arg+0x10)
 * are read through the global Lua state as x, y, z and handed to 0x00428350 as the place; no results. */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);                /* lua_tonumber */
DECOMP_C void __thiscall sub_00428350(void *self, float *where);
DECOMP_C char d_008D122C[];

DECOMP(00428570)
int __thiscall f_00428570(void *this, char *args)
{
    void *L = *(void **)d_008D122C;
    int base = *(int *)(args + 0x10);
    float where[3];

    where[0] = (float)sub_00402DE0(L, base + 1);
    where[1] = (float)sub_00402DE0(L, base + 2);
    where[2] = (float)sub_00402DE0(L, base + 3);
    sub_00428350(this, where);
    return 0;
}
