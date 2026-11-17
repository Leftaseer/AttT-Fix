/* 0x00565720: Lua factory for the 0x290-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_005824A0(void *self, void *args);
DECOMP_C char d_008CF700[], d_006BF9A8[];
DECOMP(00565720)
int __cdecl f_00565720(void) { return lua_object_factory(0x290, d_008CF700, sub_005824A0, d_006BF9A8); }
