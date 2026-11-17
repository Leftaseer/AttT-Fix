/* 0x00566430: registers the viewport's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CFC28[];
DECOMP(00566430)
unsigned int __cdecl f_00566430(void) { return lua_callback_register(d_008CFC28); }
