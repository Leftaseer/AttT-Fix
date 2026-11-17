/* 0x00565CE0: registers the button contour's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CF910[];
DECOMP(00565CE0)
unsigned int __cdecl f_00565CE0(void) { return lua_callback_register(d_008CF910); }
