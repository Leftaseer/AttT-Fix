/* 0x00565800: registers the GUI element's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CF700[];
DECOMP(00565800)
unsigned int __cdecl f_00565800(void) { return lua_callback_register(d_008CF700); }
