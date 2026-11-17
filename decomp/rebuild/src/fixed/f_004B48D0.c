/* 0x004B48D0: registers the named class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_006CA478[];
DECOMP(004B48D0)
unsigned int __cdecl f_004B48D0(void) { return lua_callback_register(d_006CA478); }
