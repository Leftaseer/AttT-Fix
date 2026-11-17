/* 0x00564AF0: registers the particle system's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CF1D8[];
DECOMP(00564AF0)
unsigned int __cdecl f_00564AF0(void) { return lua_callback_register(d_008CF1D8); }
