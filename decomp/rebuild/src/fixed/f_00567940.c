/* 0x00567940: Lua factory for the 0x374-byte clock script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_00532120(void *self, void *args);
DECOMP_C char d_008D0570[], d_006C1EA8[];
DECOMP(00567940)
int __cdecl f_00567940(void) { return lua_object_factory(0x374, d_008D0570, sub_00532120, d_006C1EA8); }
