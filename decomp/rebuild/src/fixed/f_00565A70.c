/* 0x00565A70: registers the image class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CF808[];
DECOMP(00565A70)
unsigned int __cdecl f_00565A70(void) { return lua_callback_register(d_008CF808); }
