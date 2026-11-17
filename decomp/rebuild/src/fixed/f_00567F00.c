/* 0x00567F00: registers the main menu scene's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0780[];
DECOMP(00567F00)
unsigned int __cdecl f_00567F00(void) { return lua_callback_register(d_008D0780); }
