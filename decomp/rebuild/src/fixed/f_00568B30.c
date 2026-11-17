/* 0x00568B30: registers the tooltip's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0CA8[];
DECOMP(00568B30)
unsigned int __cdecl f_00568B30(void) { return lua_callback_register(d_008D0CA8); }
