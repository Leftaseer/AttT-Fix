/* 0x00469CD0: registers the named class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_006C9008[];
DECOMP(00469CD0)
unsigned int __cdecl f_00469CD0(void) { return lua_callback_register(d_006C9008); }
