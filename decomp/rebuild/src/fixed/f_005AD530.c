/* 0x005AD530: registers the named class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D1428[];
DECOMP(005AD530)
unsigned int __cdecl f_005AD530(void) { return lua_callback_register(d_008D1428); }
