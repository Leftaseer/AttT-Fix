/* 0x00566AA0: Lua factory for the 0x194-byte script object. */
#include "lua_object_factory.h"
DECOMP_C void *__thiscall sub_00583350(void *self, void *args);
DECOMP_C char d_008CFF40[], d_006C68B4[];
DECOMP(00566AA0)
int __cdecl f_00566AA0(void) { return lua_object_factory(0x194, d_008CFF40, sub_00583350, d_006C68B4); }
