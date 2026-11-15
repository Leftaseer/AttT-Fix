/* 0x00426F30: closes the number list: when +0xC values are pending, the flag +0x14 makes the Lua stack shrink by
 * that many (lua_settop with -1 - the count), and the count is cleared either way. */
/* @conv ECX 0 */
#include "auto_pre.h"
DECOMP_C void __cdecl sub_00402A70(void *L, int idx);               /* lua_settop */
DECOMP_C char d_008D122C[];

DECOMP(00426F30)
void __thiscall f_00426F30(void *this)
{
    char *s = (char *)this;
    if (*(int *)(s + 0xc) > 0) {
        if (s[0x14])
            sub_00402A70(*(void **)d_008D122C, -1 - *(int *)(s + 0xc));
        *(unsigned int *)(s + 0xc) = 0;
    }
}
