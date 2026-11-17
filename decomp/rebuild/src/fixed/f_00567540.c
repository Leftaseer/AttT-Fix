/* 0x00567540: registers the GUI scene class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0360[];
DECOMP(00567540)
unsigned int __cdecl f_00567540(void) { return lua_callback_register(d_008D0360); }
