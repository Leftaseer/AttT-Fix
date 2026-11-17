/* 0x00568DA0: registers the message class's Lua callback. */
#include "lua_callback_register.h"
DECOMP_C char d_008D0DB0[];
DECOMP(00568DA0)
unsigned int __cdecl f_00568DA0(void) { return lua_callback_register(d_008D0DB0); }
