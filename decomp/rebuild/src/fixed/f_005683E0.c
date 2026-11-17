/* 0x005683E0: registers the trigger module's direct Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0990[];
DECOMP(005683E0)
unsigned int __cdecl f_005683E0(void) { return lua_callback_register_direct(d_008D0990); }
