/* 0x00566910: registers the hero rotator's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CFE38[];
DECOMP(00566910)
unsigned int __cdecl f_00566910(void) { return lua_callback_register(d_008CFE38); }
