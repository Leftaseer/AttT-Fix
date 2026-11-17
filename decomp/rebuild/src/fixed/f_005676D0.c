/* 0x005676D0: Lua factory for the 0x230-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_0051B940(void *self, void *args);
DECOMP_C char d_008D0468[], d_006C3504[];
DECOMP(005676D0)
int __cdecl f_005676D0(void) { return lua_object_factory(0x230, d_008D0468, sub_0051B940, d_006C3504); }
