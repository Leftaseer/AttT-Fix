/* 0x00567060: registers the troop icon's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0150[];
DECOMP(00567060)
unsigned int __cdecl f_00567060(void) { return lua_callback_register(d_008D0150); }
