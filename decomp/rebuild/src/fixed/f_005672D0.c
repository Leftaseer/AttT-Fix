/* 0x005672D0: registers the button's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0258[];
DECOMP(005672D0)
unsigned int __cdecl f_005672D0(void) { return lua_callback_register(d_008D0258); }
