/* 0x00565F50: registers the text class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CFA18[];
DECOMP(00565F50)
unsigned int __cdecl f_00565F50(void) { return lua_callback_register(d_008CFA18); }
