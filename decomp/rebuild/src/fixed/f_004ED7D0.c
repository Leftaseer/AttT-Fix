/* 0x004ED7D0: registers the unit sound manager's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_006CA838[];
DECOMP(004ED7D0)
unsigned int __cdecl f_004ED7D0(void) { return lua_callback_register(d_006CA838); }
