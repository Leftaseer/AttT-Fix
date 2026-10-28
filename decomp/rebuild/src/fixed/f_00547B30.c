/* Lua_006C6B20::AddRotY 0x00547B30: adds the number at the call's first argument (lua_tonumber of the stack
 * index args+0x10 plus one) to the Y rotation at 0x78, marks the transform dirty (0x80) */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);     /* lua_tonumber */
DECOMP_C char d_008D122C[];                                  /* the game's lua_State */

DECOMP(00547B30)
int __thiscall f_00547B30(void *this, void *args)
{
    float d = (float)sub_00402DE0(*(void **)d_008D122C, *(int *)((char *)args + 0x10) + 1);
    *(float *)((char *)this + 0x78) = d + *(float *)((char *)this + 0x78);
    *(unsigned char *)((char *)this + 0x80) = 1;
    return 0;
}
