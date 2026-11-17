/* 0x00565590: registers the particle system mesh's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CF5F8[];
DECOMP(00565590)
unsigned int __cdecl f_00565590(void) { return lua_callback_register(d_008CF5F8); }
