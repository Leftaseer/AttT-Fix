/* 0x00566DF0: registers the unit icon's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0048[];
DECOMP(00566DF0)
unsigned int __cdecl f_00566DF0(void) { return lua_callback_register(d_008D0048); }
