/* 0x005666A0: registers the rectangle class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CFD30[];
DECOMP(005666A0)
unsigned int __cdecl f_005666A0(void) { return lua_callback_register(d_008CFD30); }
