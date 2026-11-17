/* 0x00564EF0: Lua factory for the 0x41c-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_00514AD0(void *self, void *args);
DECOMP_C char d_008CF3E8[], d_006C3410[];
DECOMP(00564EF0)
int __cdecl f_00564EF0(void) { return lua_object_factory(0x41c, d_008CF3E8, sub_00514AD0, d_006C3410); }
