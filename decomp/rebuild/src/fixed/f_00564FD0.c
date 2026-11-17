/* 0x00564FD0: registers the tactical creature's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008CF3E8[];
DECOMP(00564FD0)
unsigned int __cdecl f_00564FD0(void) { return lua_callback_register(d_008CF3E8); }
