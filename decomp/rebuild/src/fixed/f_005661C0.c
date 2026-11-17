/* 0x005661C0: registers the alpha button's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CFB20[];
DECOMP(005661C0)
unsigned int __cdecl f_005661C0(void) { return lua_callback_register(d_008CFB20); }
