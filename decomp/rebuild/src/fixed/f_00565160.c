/* 0x00565160: Lua factory for the 0x110-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_004F57A0(void *self, void *args);
DECOMP_C char d_006CA838[], d_006C2A2C[];
DECOMP(00565160)
int __cdecl f_00565160(void) { return lua_object_factory(0x110, d_006CA838, sub_004F57A0, d_006C2A2C); }
