/* 0x00565320: registers the world unit's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CF4F0[];
DECOMP(00565320)
unsigned int __cdecl f_00565320(void) { return lua_callback_register(d_008CF4F0); }
