/* 0x005690C0: Lua factory for the 0xc4-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_0047EE10(void *self, void *args);
DECOMP_C char d_006CA210[], d_006C146C[];
DECOMP(005690C0)
int __cdecl f_005690C0(void) { return lua_object_factory(0xc4, d_006CA210, sub_0047EE10, d_006C146C); }
