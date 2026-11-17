/* 0x00567460: Lua factory for the 0x2a8-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_0050AF10(void *self, void *args);
DECOMP_C char d_008D0360[], d_006C32C8[];
DECOMP(00567460)
int __cdecl f_00567460(void) { return lua_object_factory(0x2a8, d_008D0360, sub_0050AF10, d_006C32C8); }
