/* 0x00427E40: registers a null-terminated table of 16-byte records into the global Lua state: each record's name
 * becomes a global whose closure is 0x00427A70 with the record pointer as its upvalue. */
/* @conv - 0 */
#include "auto_pre.h"
DECOMP_C char d_008D122C[], d_00427A70[];
DECOMP_C void __cdecl sub_00403120(void *L, const char *name);      /* lua_pushstring */
DECOMP_C void __cdecl sub_004032A0(void *L, void *p);               /* lua_pushlightuserdata */
DECOMP_C void __cdecl sub_004031F0(void *L, void *fn, int n);       /* lua_pushcclosure */
DECOMP_C void __cdecl sub_004034C0(void *L, int index);             /* lua_settable */

DECOMP(00427E40)
void __cdecl f_00427E40(char **entry)
{
    while (*entry) {
        void *L = *(void **)d_008D122C;
        sub_00403120(L, *entry);
        sub_004032A0(L, entry);
        sub_004031F0(L, d_00427A70, 1);
        sub_004034C0(L, -3);
        entry += 4;
    }
}
