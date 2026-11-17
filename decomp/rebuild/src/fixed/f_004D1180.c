/* 0x004D1180: registers the named class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_006CA6A8[];
DECOMP(004D1180)
unsigned int __cdecl f_004D1180(void) { return lua_callback_register(d_006CA6A8); }
