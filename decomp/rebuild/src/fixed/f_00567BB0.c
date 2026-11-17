/* 0x00567BB0: Lua factory for the 0x3ec-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_005430C0(void *self, void *args);
DECOMP_C char d_008D0678[], d_006C4FD8[];
DECOMP(00567BB0)
int __cdecl f_00567BB0(void) { return lua_object_factory(0x3ec, d_008D0678, sub_005430C0, d_006C4FD8); }
