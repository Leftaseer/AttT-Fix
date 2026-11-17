/* 0x00564D60: registers the render object's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CF2E0[];
DECOMP(00564D60)
unsigned int __cdecl f_00564D60(void) { return lua_callback_register(d_008CF2E0); }
