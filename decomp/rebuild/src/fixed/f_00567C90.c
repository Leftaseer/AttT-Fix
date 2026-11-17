/* 0x00567C90: registers the world GUI scene's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0678[];
DECOMP(00567C90)
unsigned int __cdecl f_00567C90(void) { return lua_callback_register(d_008D0678); }
