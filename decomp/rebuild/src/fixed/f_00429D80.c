/* 0x00429D80: pushes the userdata at this-0x3C onto the Lua stack (Lua state 0x008D122C, 4-byte userdata), gives it
 * the ambient sound manager metatable (registry ref 0x006BF4E4) and returns lua_setmetatable's result. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C char d_008D122C[], d_006BF4E4[];
DECOMP_C void *__cdecl sub_00403BF0(void *L, int size);                 /* lua_newuserdata */
DECOMP_C void __cdecl sub_00403390(void *L, int idx, int n);            /* lua_rawgeti */
DECOMP_C int __cdecl sub_004036B0(void *L, int idx);                    /* lua_setmetatable */

DECOMP(00429D80)
int __thiscall f_00429D80(void *this)
{
    void *L = *(void **)d_008D122C;

    *(char **)sub_00403BF0(L, 4) = (char *)this - 0x3c;
    sub_00403390(L, -10000, *(int *)d_006BF4E4);
    return sub_004036B0(L, -2);
}
