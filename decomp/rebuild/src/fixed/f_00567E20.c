/* 0x00567E20: Lua factory for the 0x198-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_00472CB0(void *self, void *args);
DECOMP_C char d_008D0780[], d_006C1008[];
DECOMP(00567E20)
int __cdecl f_00567E20(void) { return lua_object_factory(0x198, d_008D0780, sub_00472CB0, d_006C1008); }
