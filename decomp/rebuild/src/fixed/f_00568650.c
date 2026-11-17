/* 0x00568650: registers the attack sphere's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0A98[];
DECOMP(00568650)
unsigned int __cdecl f_00568650(void) { return lua_callback_register(d_008D0A98); }
