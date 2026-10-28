/* 0x00512A10: Lua SetSubHealth(value [, flag]): the value (truncated as _ftol does: the low dword of the 64-bit
 * conversion) at +0x3DC, at most +0x1EC, and the optional boolean at +0x3E0; no results */
/* @conv ECX 4 */
#include "auto_pre.h"
DECOMP_C int __cdecl sub_00402C20(void *L, int idx);
DECOMP_C int __cdecl sub_00402EA0(void *L, int idx);
DECOMP_C double __cdecl sub_00402DE0(void *L, int idx);
DECOMP_C char d_008D122C[];                                  /* the game's lua_State */

DECOMP(00512A10)
int __thiscall f_00512A10(void *this, char *args)
{
    char *s = (char *)this;
    void *L = *(void **)d_008D122C;
    int base = *(int *)(args + 0x10);
    char flag = 0;
    int v;
    if (*(int *)(args + 0xc) >= 2 && sub_00402C20(L, base + 2))
        flag = sub_00402EA0(*(void **)d_008D122C, *(int *)(args + 0x10) + 2) != 0;
    v = (int)(long long)sub_00402DE0(*(void **)d_008D122C, *(int *)(args + 0x10) + 1);
    *(int *)(s + 0x3dc) = v;
    s[0x3e0] = flag;
    if (v > *(int *)(s + 0x1ec))
        *(int *)(s + 0x3dc) = *(int *)(s + 0x1ec);
    return 0;
}
