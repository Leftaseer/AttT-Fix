/* 0x005677B0: registers the alternate GUI scene class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0468[];
DECOMP(005677B0)
unsigned int __cdecl f_005677B0(void) { return lua_callback_register(d_008D0468); }
