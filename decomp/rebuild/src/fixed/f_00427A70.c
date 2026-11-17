/* 0x00427A70: registers the console's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_006C8848[];
DECOMP(00427A70)
unsigned int __cdecl f_00427A70(void) { return lua_callback_register(d_006C8848); }
