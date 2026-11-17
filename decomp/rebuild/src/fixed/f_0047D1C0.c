/* 0x0047D1C0: registers the music manager's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_006CA210[];
DECOMP(0047D1C0)
unsigned int __cdecl f_0047D1C0(void) { return lua_callback_register(d_006CA210); }
